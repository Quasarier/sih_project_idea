const candidates = {
  a: { score: '96.9%', note: 'Strong spatial and temporal match' },
  b: { score: '78.5%', note: 'Near origin, weaker heading match' },
  c: { score: '10.9%', note: 'Distant and outside the vessel profile' },
  d: { score: '18.7%', note: 'Good heading, weak spatial match' },
};

document.querySelector('.ranking-column .chip').textContent = 'CORRELATION';
document.querySelector('.ranking-column .explain').textContent = 'Relative match across location, time, and movement.';
document.querySelector('.posterior-head span').textContent = 'Selected match';
document.querySelectorAll('.model-note')[1].textContent = 'Forward movement estimate. Position uncertainty ±4.6 km.';

document.querySelectorAll('.vessel').forEach((row) => row.addEventListener('click', () => {
  document.querySelectorAll('.vessel').forEach((item) => item.classList.remove('selected'));
  row.classList.add('selected');
  const candidate = candidates[row.dataset.vessel];
  document.querySelector('#posterior-value').textContent = candidate.score;
  document.querySelector('#posterior-bar').style.width = candidate.score;
  document.querySelector('#posterior-note').textContent = candidate.note;
}));
