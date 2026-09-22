const vesselData = {
  samudra: { name: 'Vessel A', prior: 0.08, likelihoods: [8.5, 5.2, 3.2], status: 'HIGH RELEVANCE', type: 'Crude oil tanker', dwt: '158,000 t', flag: 'India', note: 'Passed 2.4 km from the origin zone 38 min before the inferred discharge window.' },
  konkan: { name: 'Vessel B', prior: 0.07, likelihoods: [6.2, 3.7, 2.45], status: 'HIGH RELEVANCE', type: 'Product tanker', dwt: '74,200 t', flag: 'India', note: 'Crossed the outer origin ellipse 1h 12m before the window.' },
  malabar: { name: 'Vessel C', prior: 0.05, likelihoods: [3.8, 2.8, 3.1], status: 'REVIEW', type: 'Bulk carrier', dwt: '81,500 t', flag: 'India', note: 'Trajectory passes through the wider hindcast envelope.' },
  godavari: { name: 'Vessel D', prior: 0.04, likelihoods: [1.8, 2.4, 3.9], status: 'LOW RELEVANCE', type: 'Container ship', dwt: '68,100 t', flag: 'India', note: 'Observed nearby after the probable origin window.' }
};

const intakeScreen = document.querySelector('#intake-screen');
const tiffInput = document.querySelector('#tiff-file');
const aisInput = document.querySelector('#ais-file');
const analyzeButton = document.querySelector('#analyze-button');
const demoButton = document.querySelector('#demo-button');
const demo2Button = document.querySelector('#demo2-button');
const newAnalysisButton = document.querySelector('#new-analysis-button');
const fileNames = document.querySelectorAll('.file-name');
let loadedAisRows = [];
let activeCandidates = [];
let activeScenario = 'demo1';
let activeCurrentVector = [0.14, 0.20];
let activeDrift = null;

function formatShipType(shipType) {
  return {
    tanker: 'Oil tanker',
    oil_tanker: 'Oil tanker',
    product_tanker: 'Product tanker',
    bulk_carrier: 'Bulk carrier',
    container: 'Container ship',
    offshore_supply: 'Offshore supply vessel'
  }[shipType] || shipType.replaceAll('_', ' ');
}

function updateEvidenceBars(candidate) {
  const values = [candidate.evidence.origin_proximity ? 96 : 42, candidate.evidence.inside_time_window ? 91 : 38, candidate.evidence.trajectory_match, candidate.evidence.behavioral_anomaly];
  document.querySelectorAll('.evidence-panel .bar-row').forEach((barRow, index) => {
    if (values[index] === undefined) return;
    barRow.querySelector('i').style.width = `${values[index]}%`;
    barRow.querySelector('b').textContent = values[index];
  });
}

function applyAnalysisResult(result) {
  document.querySelector('#data-status').textContent = `${result.scenario.toUpperCase()} ANALYSIS`;
  document.querySelector('#tiff-source').textContent = 'Oil-spill TIFF';
  document.querySelector('#tiff-meta').textContent = `${result.tiff} · ${result.tiff_summary.positive_percent}% positive`;
  document.querySelector('#ais-source').textContent = 'AIS CSV';
  document.querySelector('#ais-meta').textContent = `${result.candidates.length} ranked vessels · ${result.ais}`;
  document.querySelector('.incident-heading h1').textContent = result.scenario === 'demo2' ? 'Arabian Sea slick · Demo 2' : 'Arabian Sea slick';
  document.querySelector('.incident-heading p').textContent = `Probable surface oil discharge · Detected ${result.detection}`;
  const environmentValues = document.querySelectorAll('#environment-panel > span');
  [result.environment.wind, result.environment.current, `Sea state ${result.environment.sea_state}`, `Water ${result.environment.water_temperature}`].forEach((value, index) => { environmentValues[index].textContent = value; });
  activeScenario = result.scenario;
  activeCurrentVector = result.environment.current_vector;
  activeDrift = result.drift;
  const metricCards = document.querySelectorAll('.metrics-grid .metric-card');
  metricCards[0].querySelector('.metric-value').innerHTML = `${result.confidence}<span>%</span>`;
  metricCards[1].querySelector('.metric-value').innerHTML = `${result.area_km2}<span> km²</span>`;
  document.querySelector('.summary-list dd').textContent = `${result.origin[0].toFixed(4)}, ${result.origin[1].toFixed(4)}`;
  document.querySelectorAll('.summary-list dd')[1].textContent = `${result.area_km2} km²`;
  document.querySelectorAll('.summary-list dd')[4].textContent = `${result.confidence}%`;
  observedSlickCenter[0] = result.origin[0];
  observedSlickCenter[1] = result.origin[1];
  if (result.drift?.calculated_origin) {
    document.querySelector('.map-footer strong').textContent = `${result.drift.calculated_origin[0].toFixed(2)}, ${result.drift.calculated_origin[1].toFixed(2)}`;
  }
  slickCenter = [...result.origin];
  map.setView([result.origin[0] + 0.13, result.origin[1] + 0.15], 8);
  updateScenarioTraffic(result.scenario);
  activeCandidates = result.candidates;
  updateTrafficLabels(result.candidates);
  renderSlick();
  const candidateRows = document.querySelectorAll('.vessel-row');
  const candidateBars = document.querySelectorAll('.candidate-chart > div');
  result.candidates.slice(0, candidateRows.length).forEach((candidate, index) => {
    const score = Math.round(candidate.posterior);
    candidateRows[index].dataset.candidateIndex = index;
    const displayName = `Vessel ${String.fromCharCode(65 + index)}`;
    candidateRows[index].querySelector('.vessel-info strong').textContent = displayName;
    candidateRows[index].querySelector('.vessel-info small').textContent = `IMO ${candidate.imo} · ${formatShipType(candidate.ship_type)}`;
    candidateRows[index].querySelector('.evidence-value b').textContent = `${candidate.distance_km} km`;
    candidateRows[index].querySelector('.evidence-value small').textContent = `${candidate.time_offset_hours}h offset`;
    candidateRows[index].querySelector('.score').innerHTML = `${score}<span>/100</span>`;
    
    // Update evidence bars with actual data from API
    const values = [
      candidate.evidence.origin_proximity ? 96 : 42, 
      candidate.evidence.inside_time_window ? 91 : 38, 
      candidate.evidence.trajectory_match, 
      candidate.evidence.behavioral_anomaly
    ];
    
    // Update candidate bars
    if (candidateBars[index]) {
      candidateBars[index].querySelector('i').style.width = `${score}%`;
      candidateBars[index].querySelector('b').textContent = score;
      candidateBars[index].querySelector('span').textContent = displayName;
    }
  });
  if (candidateRows[0]) candidateRows[0].click();
}

function showAnalysisError() {
  document.querySelector('#data-status').textContent = 'ANALYSIS UNAVAILABLE';
  document.querySelector('#ais-meta').textContent = 'The API could not complete this analysis';
}

function loadScenario(scenarioId, tiffName, aisName, fallbackRows) {
  completeIntake(tiffName, aisName, fallbackRows, true);
  fetch(`http://localhost:8001/api/analyze?scenario=${scenarioId}`)
    .then((response) => response.ok ? response.json() : Promise.reject(new Error('Analysis API unavailable')))
    .then(applyAnalysisResult)
    .catch(showAnalysisError);
}

function updateFileNames() {
  fileNames[0].textContent = tiffInput.files[0]?.name || fileNames[0].dataset.empty;
  fileNames[1].textContent = aisInput.files[0]?.name || fileNames[1].dataset.empty;
  analyzeButton.disabled = !(tiffInput.files.length && aisInput.files.length);
}

function startNewAnalysis() {
  tiffInput.value = '';
  aisInput.value = '';
  loadedAisRows = [];
  activeCandidates = [];
  activeDrift = null;
  fileNames.forEach((fileName) => { fileName.textContent = fileName.dataset.empty; });
  analyzeButton.disabled = true;
  intakeScreen.classList.remove('hidden');
}

newAnalysisButton.addEventListener('click', startNewAnalysis);

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines.shift().split(',');
  return lines.filter(Boolean).map((line) => Object.fromEntries(line.split(',').map((value, index) => [headers[index], value])));
}

function completeIntake(tiffName, aisName, rows, isDemo) {
  loadedAisRows = rows;
  document.querySelector('#data-status').textContent = isDemo ? 'DEMO DATA' : 'UPLOADED DATA';
  document.querySelector('#tiff-source').textContent = 'Oil-spill TIFF';
  document.querySelector('#tiff-meta').textContent = `${tiffName} · mask analysis`;
  document.querySelector('#ais-source').textContent = 'AIS CSV';
  document.querySelector('#ais-meta').textContent = `${new Set(rows.map((row) => row.mmsi)).size} vessels · ${rows.length} positions`;
  intakeScreen.classList.add('hidden');
}

tiffInput.addEventListener('change', updateFileNames);
aisInput.addEventListener('change', updateFileNames);
analyzeButton.addEventListener('click', () => {
  const aisFile = aisInput.files[0];
  const reader = new FileReader();
  reader.onload = () => completeIntake(tiffInput.files[0].name, aisFile.name, parseCsv(reader.result), false);
  reader.readAsText(aisFile);
});
demoButton.addEventListener('click', () => {
  loadScenario('demo1', 'demo_oil_spill_mask.tif', 'demo_ais_tracks.csv', [{ mmsi: 'demo-001' }, { mmsi: 'demo-002' }]);
});
demo2Button.addEventListener('click', () => {
  loadScenario('demo2', 'demo2_oil_spill_mask.tif', 'demo2_ais_tracks.csv', [{ mmsi: 'demo2-001' }, { mmsi: 'demo2-002' }]);
});

function posteriorProbability(prior, likelihoods) {
  const priorOdds = prior / (1 - prior);
  const posteriorOdds = priorOdds * likelihoods.reduce((product, likelihoodRatio) => product * likelihoodRatio, 1);
  return Math.round((posteriorOdds / (1 + posteriorOdds)) * 100);
}

Object.values(vesselData).forEach((vessel) => { vessel.score = posteriorProbability(vessel.prior, vessel.likelihoods); });
document.querySelector('#selected-vessel').textContent = vesselData.samudra.name;
document.querySelector('.timeline-item:nth-child(3) strong').textContent = `${vesselData.samudra.name} enters origin zone`;

const origin = [18.72, 72.10];
const map = L.map('incident-map', { zoomControl: true }).setView([18.85, 72.25], 8);
const streetTiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' });
const satelliteTiles = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18, attribution: 'Tiles &copy; Esri' });
streetTiles.addTo(map);
let slickLayer;
let forecastLayer;
let hindcastLayer;
let originMarker;
let originUncertainty;
let centroidMarker;
let slickCenter = [...origin];
const observedSlickCenter = [...origin];
const traffic = [
  [19.28, 71.68, 0.00019, 0.00027], [19.25, 71.58, -0.00023, 0.00008],
  [18.05, 72.62, 0.00008, -0.00012], [19.75, 71.72, -0.00012, -0.00016],
  [19.34, 71.7, 0.0002, 0.00013], [18.18, 72.7, -0.00016, 0.00022],
  [19.95, 71.85, -0.0001, -0.00019]
].map(([lat, lng, latStep, lngStep], index) => ({ name: `Vessel ${String.fromCharCode(65 + index)}`, lat, lng, latStep, lngStep }));
const vesselLayers = traffic.map((vessel) => {
  const bend = Math.random() * Math.PI * 2;
  const trackLength = 700 + Math.random() * 700;
  const lateralScale = 0.025 + Math.random() * 0.02;
  const path = vessel.name === 'Vessel A'
    ? [[18.92, 71.35], [18.72, 71.55], [18.48, 71.38], [18.16, 71.30], [18.24, 71.45], [18.46, 71.58], [18.34, 71.46], [vessel.lat, vessel.lng]]
    : Array.from({ length: 9 }, (_, index) => {
      const progress = index / 8;
      const distance = (1 - progress) * trackLength;
      const lateral = Math.sin(progress * Math.PI * 2.2 + bend) * lateralScale * (1 - progress);
      const drift = (Math.random() - 0.5) * 0.01 * (1 - progress);
      return [vessel.lat - vessel.latStep * distance + lateral + drift, vessel.lng - vessel.lngStep * distance + lateral * 0.7 - drift];
    });
  const line = L.polyline(path, { color: '#1a63ad', weight: vessel.name.includes('Samudra') ? 3 : 1.5, opacity: vessel.name.includes('Samudra') ? 0.9 : 0.55, dashArray: '5 6' }).addTo(map);
  const marker = L.circleMarker([vessel.lat, vessel.lng], { radius: vessel.name.includes('Samudra') ? 6 : 4, color: '#fff', weight: 1.5, fillColor: '#1a63ad', fillOpacity: 0.95 }).addTo(map).bindTooltip(`${vessel.name}<br><small>Simulated AIS position</small>`, { direction: 'top', offset: [0, -5] });
  return { ...vessel, bend, line, marker };
});
function updateTrafficLabels(candidates) {
  const visibleLayers = vesselLayers.filter((vessel) => map.hasLayer(vessel.marker));
  visibleLayers.forEach((vessel, index) => {
    const label = `Vessel ${String.fromCharCode(65 + index)}`;
    const type = candidates[index]?.ship_type ? formatShipType(candidates[index].ship_type) : 'Synthetic AIS position';
    vessel.mapLabel = label;
    vessel.marker.setTooltipContent(`${label}<br><small>${type}</small>`);
  });
}
function updateScenarioTraffic(scenarioId) {
  if (scenarioId !== 'demo2') {
    vesselLayers.slice(0, 2).forEach((vessel) => {
      if (!map.hasLayer(vessel.marker)) map.addLayer(vessel.marker);
      if (!map.hasLayer(vessel.line)) map.addLayer(vessel.line);
    });
    return;
  }
  const positions = { 'Vessel C': [20.48, 70.18], 'Vessel D': [20.665, 68.9], 'Vessel E': [20.7, 69.3], 'Vessel F': [20.8, 68.9], 'Vessel G': [21.12, 69.8] };
  vesselLayers.forEach((vessel, index) => {
    if (vessel.name === 'Vessel A' || vessel.name === 'Vessel B') {
      map.removeLayer(vessel.marker);
      map.removeLayer(vessel.line);
      return;
    }
    const [lat, lng] = positions[vessel.name] || [vessel.lat, vessel.lng];
    vessel.marker.setLatLng([lat, lng]);
    if (vessel.name === 'Vessel D') {
      vessel.line.setLatLngs(curvedPath([19.42, 68.82], [19.2, 69.02], [19.076, 69.18], [lat, lng], 24));
      return;
    }
    const variation = Math.random() * Math.PI * 2;
    const start = [lat - 0.16 - Math.random() * 0.16, lng - 0.2 + (Math.random() - 0.5) * 0.2];
    const controlOne = [lat - 0.1 + Math.sin(variation) * 0.12, lng - 0.12 + Math.cos(variation) * 0.18];
    const controlTwo = [lat - 0.04 + Math.cos(variation) * 0.1, lng - 0.05 + Math.sin(variation) * 0.16];
    vessel.line.setLatLngs(curvedPath(start, controlOne, controlTwo, [lat, lng], 14));
  });
}
function curvedPath(start, controlOne, controlTwo, end, steps = 20) {
  return Array.from({ length: steps + 1 }, (_, index) => {
    const t = index / steps;
    const inverse = 1 - t;
    return [
      inverse ** 3 * start[0] + 3 * inverse ** 2 * t * controlOne[0] + 3 * inverse * t ** 2 * controlTwo[0] + t ** 3 * end[0],
      inverse ** 3 * start[1] + 3 * inverse ** 2 * t * controlOne[1] + 3 * inverse * t ** 2 * controlTwo[1] + t ** 3 * end[1]
    ];
  });
}
function renderSlick() {
  const width = (activeScenario === 'demo2' ? 0.31 : 0.17) + Math.random() * (activeScenario === 'demo2' ? 0.1 : 0.06);
  const height = (activeScenario === 'demo2' ? 0.1 : 0.055) + Math.random() * (activeScenario === 'demo2' ? 0.04 : 0.026);
  const rotation = Math.random() * 0.45 - 0.22;
  const stretchAngle = Math.random() * Math.PI * 2;
  const points = Array.from({ length: 64 }, (_, index) => {
    const angle = (index / 64) * Math.PI * 2;
    const stretch = 1 + 0.34 * Math.max(0, Math.cos(angle - stretchAngle)) ** 3;
    const taper = 0.78 + 0.22 * Math.abs(Math.cos(angle));
    const contour = 1 + 0.13 * Math.sin(angle * 3 + 0.4) + 0.08 * Math.sin(angle * 7 - 0.7) + 0.04 * Math.sin(angle * 11 + 1.1);
    const x = Math.cos(angle) * width * stretch * taper * contour;
    const y = Math.sin(angle) * height * (0.92 + 0.08 * Math.cos(angle * 2)) * contour;
    return [slickCenter[0] + y * Math.cos(rotation) - x * Math.sin(rotation), slickCenter[1] + x * Math.cos(rotation) + y * Math.sin(rotation)];
  });
  if (slickLayer) map.removeLayer(slickLayer);
  slickLayer = L.polygon(points, { color: '#d47c53', weight: 1.5, dashArray: '5 6', fillColor: '#d47c53', fillOpacity: 0.22, smoothFactor: 1.2 }).addTo(map);
  if (!centroidMarker) {
    centroidMarker = L.circleMarker(slickCenter, { radius: 5, color: '#fff', weight: 2, fillColor: '#c04b91', fillOpacity: 1 }).addTo(map).bindTooltip('<b>Current spill centroid</b><br>Center of the detected slick estimate', { direction: 'top', offset: [0, -6], opacity: 0.95 });
  } else {
    centroidMarker.setLatLng(slickCenter);
  }
  const calculatedHindcast = activeDrift?.hindcast?.map(([lat, lng]) => [lat, lng]);
  const calculatedForecast = activeDrift?.forecast?.map(([lat, lng]) => [lat, lng]);
  const driftEnd = calculatedForecast?.at(-1) || [slickCenter[0] + activeCurrentVector[0] * 3, slickCenter[1] + activeCurrentVector[1] * 5];
  if (forecastLayer) map.removeLayer(forecastLayer);
  forecastLayer = L.layerGroup().addTo(map);
  const forecastPath = calculatedForecast || curvedPath(slickCenter, [driftEnd[0] - 0.08, driftEnd[1] - 0.02], [driftEnd[0] + 0.09, driftEnd[1] + 0.08], driftEnd);
  L.polyline(forecastPath, { color: '#16a39a', weight: 3, dashArray: '8 7' }).addTo(forecastLayer);
  if (hindcastLayer) map.removeLayer(hindcastLayer);
  const hindcastStart = calculatedHindcast?.at(-1) || [observedSlickCenter[0] - activeCurrentVector[0] * 4, observedSlickCenter[1] - activeCurrentVector[1] * 4];
  const hindcastPath = calculatedHindcast || curvedPath(hindcastStart, [hindcastStart[0] + 0.18, hindcastStart[1] + 0.12], [slickCenter[0] - 0.12, slickCenter[1] - 0.12], slickCenter);
  hindcastLayer = L.polyline(hindcastPath, { color: '#d6854f', weight: 3, dashArray: '3 7' }).addTo(map);
  if (!originMarker) {
    originMarker = L.circleMarker(hindcastStart, { radius: 7, color: '#fff', weight: 2, fillColor: '#df8054', fillOpacity: 1 }).addTo(map).bindTooltip('<b>Hindcast origin estimate</b><br>Derived from backward drift reconstruction', { direction: 'right', offset: [12, 0], opacity: 0.95 });
    originUncertainty = L.circle(hindcastStart, { radius: 9000, color: '#df8c5b', weight: 1, dashArray: '4 5', fill: false }).addTo(map);
  } else {
    originMarker.setLatLng(hindcastStart);
    originUncertainty.setLatLng(hindcastStart);
  }
}
renderSlick();

const rows = document.querySelectorAll('.vessel-row');
rows.forEach((row) => row.addEventListener('click', () => {
  rows.forEach((item) => item.classList.remove('selected'));
  row.classList.add('selected');
  const apiCandidate = activeCandidates[Number(row.dataset.candidateIndex)];
  if (apiCandidate) {
    document.querySelector('#selected-vessel').textContent = row.querySelector('.vessel-info strong').textContent;
    document.querySelector('#candidate-score').textContent = Math.round(apiCandidate.posterior);
    document.querySelector('.status-tag').textContent = apiCandidate.posterior >= 70 ? 'HIGH RELEVANCE' : apiCandidate.posterior >= 50 ? 'REVIEW' : 'LOW RELEVANCE';
    const candidateFacts = document.querySelector('.candidate-facts');
    candidateFacts.innerHTML = '<div><span>VESSEL TYPE</span><strong></strong></div><div><span>IMO</span><strong></strong></div><div><span>DISTANCE</span><strong></strong></div>';
    candidateFacts.querySelectorAll('strong')[0].textContent = formatShipType(apiCandidate.ship_type);
    candidateFacts.querySelectorAll('strong')[1].textContent = apiCandidate.imo;
    candidateFacts.querySelectorAll('strong')[2].textContent = `${apiCandidate.distance_km} km`;
    const evidenceNote = document.querySelector('.evidence-note p');
    evidenceNote.textContent = '';
    const evidenceTitle = document.createElement('strong');
    evidenceTitle.textContent = 'Bayesian update';
    evidenceNote.append(evidenceTitle, document.createTextNode(` Ranking combines proximity, timing, vessel type, and trajectory evidence. Current posterior relevance: ${apiCandidate.posterior}%.`));
    updateEvidenceBars(apiCandidate);
    return;
  }
  const vessel = vesselData[row.dataset.vessel];
  document.querySelector('#selected-vessel').textContent = vessel.name;
  document.querySelector('#candidate-score').textContent = vessel.score;
  document.querySelector('.status-tag').textContent = vessel.status;
  const candidateFacts = document.querySelector('.candidate-facts');
  candidateFacts.innerHTML = '<div><span>VESSEL TYPE</span><strong></strong></div><div><span>DWT</span><strong></strong></div><div><span>FLAG</span><strong></strong></div>';
  candidateFacts.querySelectorAll('strong')[0].textContent = vessel.type;
  candidateFacts.querySelectorAll('strong')[1].textContent = vessel.dwt;
  candidateFacts.querySelectorAll('strong')[2].textContent = vessel.flag;
  const evidenceNote = document.querySelector('.evidence-note p');
  evidenceNote.textContent = '';
  const evidenceTitle = document.createElement('strong');
  evidenceTitle.textContent = 'Bayesian update';
  evidenceNote.append(evidenceTitle, document.createTextNode(` Prior vessel relevance updated by proximity, timing, and trajectory evidence. ${vessel.note}`));
}));

document.querySelectorAll('.view-tab').forEach((tab) => tab.addEventListener('click', () => {
  document.querySelectorAll('.view-tab').forEach((item) => item.classList.remove('active'));
  tab.classList.add('active');
  document.querySelector('.map-wrap').classList.toggle('satellite-mode', tab.dataset.view === 'satellite');
  if (tab.dataset.view === 'satellite') {
    map.removeLayer(streetTiles);
    satelliteTiles.addTo(map);
  } else {
    map.removeLayer(satelliteTiles);
    streetTiles.addTo(map);
  }
  setTimeout(() => map.invalidateSize(), 0);
}));

document.querySelector('#env-tab').addEventListener('click', () => {
  const panel = document.querySelector('#environment-panel');
  panel.classList.toggle('visible');
  document.querySelector('#env-tab').classList.toggle('active', panel.classList.contains('visible'));
});

document.querySelector('.export-button').addEventListener('click', () => {
  const button = document.querySelector('.export-button');
  const original = button.innerHTML;
  button.innerHTML = 'Brief ready <span>✓</span>';
  button.classList.add('exported');
  setTimeout(() => { button.innerHTML = original; button.classList.remove('exported'); }, 1800);
});
