const STATUS_LABELS = {
  'approved': 'Одобрен',
  'on_review': 'На рассмотрении',
  'decline': 'Отклонён',
};
const STATUS_COLORS = {
  'approved': '#22bb33',
  'on_review': '#f0ad4e',
  'decline': '#bb2124',
};

const map = L.map('map').setView([55.75, 37.62], 4);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

const legend = L.control({ position: 'bottomright' });
legend.onAdd = () => {
  const div = L.DomUtil.create('div', 'legend');
  div.innerHTML = `
    <b>Статус отчёта</b><br>
    <span class="legend-dot" style="background:#22bb33"></span>Одобрен<br>
    <span class="legend-dot" style="background:#f0ad4e"></span>На рассмотрении<br>
    <span class="legend-dot" style="background:#bb2124"></span>Отклонён<br>
    <span class="legend-dot" style="background:#777"></span>Нет отчёта
  `;
  return div;
};
legend.addTo(map);

const noCoordsTbody = document.getElementById('no-coords-list');
const noCoordsEmpty = document.getElementById('no-coords-empty');

fetch('/api/refrigerators/')
  .then(r => r.json())
  .then(data => {
    const markers = [];
    const noCoords = [];

    data.forEach(ref => {
      const color = STATUS_COLORS[ref.last_report_status] || '#777';
      const statusLabel = STATUS_LABELS[ref.last_report_status] || 'Нет отчёта';

      if (ref.latitude && ref.longitude) {
        const marker = L.circleMarker([ref.latitude, ref.longitude], {
          color: color,
          fillColor: color,
          fillOpacity: 0.85,
          radius: 9,
          weight: 2,
        }).addTo(map);

        marker.bindPopup(`
          <b>${ref.model}</b><br>
          <span style="color:#888">С/н: ${ref.serial_number}</span><br>
          <hr style="margin:4px 0">
          📍 ${ref.organization_name}<br>
          ${ref.organization_address ? ref.organization_address + '<br>' : ''}
          👤 ${ref.assigned_to || '—'}<br>
          Статус: <span style="color:${color};font-weight:600">${statusLabel}</span>
        `, { maxWidth: 260 });

        markers.push(marker);
      } else {
        noCoords.push(ref);
      }
    });

    if (markers.length > 0) {
      map.fitBounds(L.featureGroup(markers).getBounds().pad(0.15));
    }

    if (noCoords.length === 0) {
      document.getElementById('no-coords-table').style.display = 'none';
      noCoordsEmpty.style.display = 'block';
    } else {
      noCoords.forEach(ref => {
        const color = STATUS_COLORS[ref.last_report_status] || '#777';
        const statusLabel = STATUS_LABELS[ref.last_report_status] || 'Нет отчёта';
        noCoordsTbody.insertAdjacentHTML('beforeend', `
          <tr class="tr-shadow">
            <td>${ref.serial_number}</td>
            <td>${ref.model}</td>
            <td>${ref.organization_name || '—'}</td>
            <td>${ref.assigned_to || '—'}</td>
            <td><span style="color:${color};font-weight:600">${statusLabel}</span></td>
          </tr>
          <tr class="spacer"></tr>
        `);
      });
    }
  })
  .catch(() => {
    document.getElementById('map').insertAdjacentHTML(
      'afterend',
      '<p class="text-danger mt-2">Не удалось загрузить данные с сервера.</p>'
    );
  });
