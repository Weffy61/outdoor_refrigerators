import numpy as np
import folium
from django.db.models import Avg
from sklearn.cluster import DBSCAN

from report.models import Organization, Photo

CLUSTER_COLORS = [
    'red', 'blue', 'green', 'purple',
    'orange', 'darkred', 'cadetblue', 'darkgreen',
    'pink', 'lightred',
]


def get_org_coordinates():
    result = []
    for org in Organization.objects.all():
        agg = Photo.objects.filter(
            report__refrigerator__organization=org,
            latitude__isnull=False,
            longitude__isnull=False,
        ).aggregate(avg_lat=Avg('latitude'), avg_lon=Avg('longitude'))

        if agg['avg_lat'] is not None:
            result.append({
                'id': org.id,
                'name': org.name,
                'lat': float(agg['avg_lat']),
                'lon': float(agg['avg_lon']),
            })
    return result


def prepare_coords(orgs):
    coords = np.array([[o['lat'], o['lon']] for o in orgs])
    return np.radians(coords)


def run_dbscan(coords_rad, eps_km=1.0, min_samples=2):
    eps_rad = eps_km / 6371.0
    db = DBSCAN(
        eps=eps_rad,
        min_samples=min_samples,
        algorithm='ball_tree',
        metric='haversine',
    )
    return db.fit_predict(coords_rad)


def cluster_organizations(eps_km=1.0, min_samples=2):
    orgs = get_org_coordinates()
    if not orgs:
        return []
    coords_rad = prepare_coords(orgs)
    labels = run_dbscan(coords_rad, eps_km, min_samples)
    for i, org in enumerate(orgs):
        org['cluster'] = int(labels[i])
    return orgs


def build_cluster_map(orgs_with_clusters):
    if not orgs_with_clusters:
        return ''
    center_lat = sum(o['lat'] for o in orgs_with_clusters) / len(orgs_with_clusters)
    center_lon = sum(o['lon'] for o in orgs_with_clusters) / len(orgs_with_clusters)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11)

    for org in orgs_with_clusters:
        c = org['cluster']
        color = 'gray' if c == -1 else CLUSTER_COLORS[c % len(CLUSTER_COLORS)]
        label = 'Шум (нет кластера)' if c == -1 else f'Кластер {c}'
        folium.CircleMarker(
            location=[org['lat'], org['lon']],
            radius=9,
            color=color,
            fill=True,
            fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>{org['name']}</b><br>{label}",
                max_width=220,
            ),
            tooltip=org['name'],
        ).add_to(m)

    return m._repr_html_()
