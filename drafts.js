// Draft pages only: a button that shows a draft as it would read once finished
// (the invented examples appear as text and the guidance boxes are hidden), and back again.
(function () {
  'use strict';
  var body = document.querySelector('.post-body');
  if (!body || !document.querySelector('.ph')) return;
  var fr = (document.documentElement.lang || 'en').toLowerCase().indexOf('fr') === 0;
  var labels = fr
    ? ['Voir comme une page terminée, exemples affichés comme texte', 'Réafficher les consignes']
    : ['View as a finished page, examples shown as text', 'Show the guidance again'];
  var main = document.getElementById('main');
  var btn = document.createElement('button');
  btn.type = 'button'; btn.className = 'btn btn-ghost ph-toggle'; btn.setAttribute('aria-pressed', 'false');
  btn.textContent = labels[0];
  btn.addEventListener('click', function () {
    var on = main.classList.toggle('ph-preview');
    btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    btn.textContent = on ? labels[1] : labels[0];
  });
  body.parentNode.insertBefore(btn, body);
})();
