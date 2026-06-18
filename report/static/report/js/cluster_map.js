const CLUSTER_COLORS = [
  '#e74c3c', '#3498db', '#2ecc71', '#9b59b6',
  '#e67e22', '#c0392b', '#1abc9c', '#27ae60',
  '#e91e63', '#ff5722',
];

const map = L.map('cluster-map').setView([47.2357, 39.7015], 10);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

const markers = [];

CLUSTER_ORGS.forEach(org => {
  const c = org.cluster;
  const color = c === -1 ? '#888888' : CLUSTER_COLORS[c % CLUSTER_COLORS.length];
  const label = c === -1 ? 'Шум (нет кластера)' : `Кластер ${c}`;

  const marker = L.circleMarker([org.lat, org.lon], {
    color: color,
    fillColor: color,
    fillOpacity: 0.85,
    radius: 9,
    weight: 2,
  });

  marker.bindPopup(`<b>${org.name}</b><br>${label}`, { maxWidth: 220 });
  marker.bindTooltip(org.name);
  marker.addTo(map);
  markers.push(marker);
});

if (markers.length > 0) {
  map.fitBounds(L.featureGroup(markers).getBounds().pad(0.1));
}
