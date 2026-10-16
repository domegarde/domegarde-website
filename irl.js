// Domegarde free tool: yearly rent revision on the IRL (Indice de référence des loyers).
// Runs entirely in the browser. Nothing typed here is sent anywhere.
// Index values: INSEE series 001515333, read from INSEE's data service on 16 October 2026.
(function (root) {
  'use strict';

  var IRL = {
  "2002-Q4": 105.61,
  "2003-Q1": 106.17,
  "2003-Q2": 106.61,
  "2003-Q3": 107.06,
  "2003-Q4": 107.49,
  "2004-Q1": 107.8,
  "2004-Q2": 108.28,
  "2004-Q3": 108.72,
  "2004-Q4": 109.2,
  "2005-Q1": 109.64,
  "2005-Q2": 110.08,
  "2005-Q3": 110.57,
  "2005-Q4": 111.01,
  "2006-Q1": 111.47,
  "2006-Q2": 111.98,
  "2006-Q3": 112.43,
  "2006-Q4": 112.77,
  "2007-Q1": 113.07,
  "2007-Q2": 113.37,
  "2007-Q3": 113.68,
  "2007-Q4": 114.3,
  "2008-Q1": 115.12,
  "2008-Q2": 116.07,
  "2008-Q3": 117.03,
  "2008-Q4": 117.54,
  "2009-Q1": 117.7,
  "2009-Q2": 117.59,
  "2009-Q3": 117.41,
  "2009-Q4": 117.47,
  "2010-Q1": 117.81,
  "2010-Q2": 118.26,
  "2010-Q3": 118.7,
  "2010-Q4": 119.17,
  "2011-Q1": 119.69,
  "2011-Q2": 120.31,
  "2011-Q3": 120.95,
  "2011-Q4": 121.68,
  "2012-Q1": 122.37,
  "2012-Q2": 122.96,
  "2012-Q3": 123.55,
  "2012-Q4": 123.97,
  "2013-Q1": 124.25,
  "2013-Q2": 124.44,
  "2013-Q3": 124.66,
  "2013-Q4": 124.83,
  "2014-Q1": 125.0,
  "2014-Q2": 125.15,
  "2014-Q3": 125.24,
  "2014-Q4": 125.29,
  "2015-Q1": 125.19,
  "2015-Q2": 125.25,
  "2015-Q3": 125.26,
  "2015-Q4": 125.28,
  "2016-Q1": 125.26,
  "2016-Q2": 125.25,
  "2016-Q3": 125.33,
  "2016-Q4": 125.5,
  "2017-Q1": 125.9,
  "2017-Q2": 126.19,
  "2017-Q3": 126.46,
  "2017-Q4": 126.82,
  "2018-Q1": 127.22,
  "2018-Q2": 127.77,
  "2018-Q3": 128.45,
  "2018-Q4": 129.03,
  "2019-Q1": 129.38,
  "2019-Q2": 129.72,
  "2019-Q3": 129.99,
  "2019-Q4": 130.26,
  "2020-Q1": 130.57,
  "2020-Q2": 130.57,
  "2020-Q3": 130.59,
  "2020-Q4": 130.52,
  "2021-Q1": 130.69,
  "2021-Q2": 131.12,
  "2021-Q3": 131.67,
  "2021-Q4": 132.62,
  "2022-Q1": 133.93,
  "2022-Q2": 135.84,
  "2022-Q3": 136.27,
  "2022-Q4": 137.26,
  "2023-Q1": 138.61,
  "2023-Q2": 140.59,
  "2023-Q3": 141.03,
  "2023-Q4": 142.06,
  "2024-Q1": 143.46,
  "2024-Q2": 145.17,
  "2024-Q3": 144.51,
  "2024-Q4": 144.64,
  "2025-Q1": 145.47,
  "2025-Q2": 146.68,
  "2025-Q3": 145.77,
  "2025-Q4": 145.78,
  "2026-Q1": 146.6,
  "2026-Q2": 148.37,
  "2026-Q3": 148.06
};
  var AS_OF = '2026-10-16';

  function qkey(y, q) { return y + '-Q' + q; }
  function round2(x) { return Math.round((x + Number.EPSILON) * 100) / 100; }
  function isoToUtc(iso) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '');
    if (!m) return null;
    var t = Date.UTC(+m[1], +m[2] - 1, +m[3]);
    var d = new Date(t);
    if (d.getUTCFullYear() !== +m[1] || d.getUTCMonth() !== +m[2] - 1 || d.getUTCDate() !== +m[3]) return null;
    return t;
  }
  function utcToIso(t) { return new Date(t).toISOString().slice(0, 10); }
  // The last day on which the revision can still be claimed: one year after the revision date, less a day
  // (Service-Public's own example: revision date 13 March 2026, claim until 12 March 2027).
  function lastDayToClaim(revisionIso) {
    var t = isoToUtc(revisionIso); if (t === null) return null;
    var d = new Date(t);
    return Date.UTC(d.getUTCFullYear() + 1, d.getUTCMonth(), d.getUTCDate()) - 86400000;
  }
  // INSEE publishes a quarter around the middle of the month after the quarter closes.
  function expectedPublication(y, q) {
    var month = q * 3 + 1;               // Q1 -> April, Q2 -> July, Q3 -> October, Q4 -> January
    return { year: q === 4 ? y + 1 : y, month: q === 4 ? 1 : month };
  }

  // opts: { rent: number, refQuarter: 'YYYY-Qn', revisionDate: 'YYYY-MM-DD' | '', dpe: 'A'..'G' | '', today: 'YYYY-MM-DD' }
  function compute(opts) {
    var errors = {};
    var rent = opts.rent;
    if (!(rent > 0) || rent > 100000) errors.rent = true;
    var rq = /^(\d{4})-Q([1-4])$/.exec(opts.refQuarter || '');
    if (!rq || IRL[opts.refQuarter] === undefined) errors.refQuarter = true;
    var revisionT = null;
    if (opts.revisionDate) { revisionT = isoToUtc(opts.revisionDate); if (revisionT === null) errors.revisionDate = true; }
    if (Object.keys(errors).length) return { status: 'invalid', errors: errors };

    var cls = (opts.dpe || '').toUpperCase();
    if (cls === 'F' || cls === 'G') return { status: 'frozen', dpe: cls };

    var y = +rq[1], q = +rq[2];
    var newKey = qkey(y + 1, q);
    if (IRL[newKey] === undefined) return { status: 'pending', quarter: newKey, expected: expectedPublication(y + 1, q) };

    var refIdx = IRL[opts.refQuarter], newIdx = IRL[newKey];
    var newRent = round2(rent * newIdx / refIdx);
    var monthly = round2(newRent - rent);
    var out = {
      status: 'ok', rent: rent, refQuarter: opts.refQuarter, newQuarter: newKey, refIdx: refIdx, newIdx: newIdx,
      newRent: newRent, monthly: monthly, percent: round2((newIdx / refIdx - 1) * 100), annual: round2(monthly * 12), asOf: AS_OF
    };
    if (revisionT !== null) {
      var todayT = isoToUtc(opts.today || utcToIso(Date.now()));
      var lastT = lastDayToClaim(opts.revisionDate);
      out.revisionDate = opts.revisionDate; out.lastDay = utcToIso(lastT);
      if (todayT > lastT) { out.window = 'closed'; }
      else if (todayT < revisionT) { out.window = 'notyet'; out.daysToRevision = Math.round((revisionT - todayT) / 86400000); }
      else {
        out.window = 'open';
        out.daysLeft = Math.round((lastT - todayT) / 86400000);
        var monthsSince = (todayT - revisionT) / 86400000 / (365.25 / 12);
        out.lostSoFar = monthly > 0 ? Math.round(monthly * monthsSince) : 0;
      }
    }
    return out;
  }

  root.DomegardeIRL = { compute: compute, data: IRL, asOf: AS_OF, lastDayToClaim: function (i) { var t = lastDayToClaim(i); return t === null ? null : utcToIso(t); } };
  if (typeof module !== 'undefined' && module.exports) module.exports = root.DomegardeIRL;

  // ---------------------------------------------------------------- page
  if (typeof document === 'undefined') return;
  var LANG = (document.documentElement.lang || 'en').toLowerCase().indexOf('fr') === 0 ? 'fr' : 'en';
  var NB = ' ';
  var S = {
    en: {
      qlabel: function (k) { return k.replace(/^(\d{4})-Q(\d)$/, 'Q$2 $1'); },
      choose: 'Choose the quarter named in your lease',
      eur: function (n) { return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'EUR' }).format(n); },
      num: function (n) { return new Intl.NumberFormat('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n); },
      pct: function (n) { return (n > 0 ? '+' : '') + new Intl.NumberFormat('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n) + '%'; },
      date: function (iso) { var d = new Date(isoToUtc(iso)); return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }); },
      months: ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
      errRent: 'Enter the monthly rent excluding charges, for example 600 or 600.50.',
      errQuarter: 'Choose the reference quarter.',
      errDate: 'Enter a valid date, or leave it empty.',
      newRent: 'New rent', perMonth: ' per month', rise: 'Increase',
      formula: 'Calculation', indexes: 'Indexes',
      source: 'INSEE, series 001515333. Figures as of ',
      frozen: function (c) { return 'Do not apply a revision. A home rated ' + c + ' on its energy label (DPE) cannot have its rent revised during the lease (France, leases signed, renewed or tacitly renewed since 24 August 2022). Source: Service-Public.'; },
      pending: function (k, e, m) { return 'The index for ' + S.qlabel(k) + ' is not published yet. INSEE publishes it around the middle of ' + m[e.month] + ' ' + e.year + '. Come back then, or choose another reference quarter.'; },
      open: function (r, S2) { return 'You can still claim this revision until ' + S2.date(r.lastDay) + ' (' + r.daysLeft + ' day' + (r.daysLeft === 1 ? '' : 's') + ' left). The increase counts only from the day you tell your tenant: it is never back-dated.'; },
      lost: function (r, S2) { return 'If you told your tenant today, the months since ' + S2.date(r.revisionDate) + ' would already be lost: about ' + S2.eur(r.lostSoFar) + '. The sooner you ask, the less is lost.'; },
      notyet: function (r, S2) { return 'The revision date is ' + S2.date(r.revisionDate) + ' (in ' + r.daysToRevision + ' day' + (r.daysToRevision === 1 ? '' : 's') + '). You will then have until ' + S2.date(r.lastDay) + ' to claim it.'; },
      closed: function (r, S2) { return 'The window closed on ' + S2.date(r.lastDay) + '. A revision not claimed within a year is lost for that year. Next year’s revision starts again from your current rent.'; },
      checkLease: 'Check your lease: a revision is only possible if it contains an indexation clause. Information, not legal advice.'
    },
    fr: {
      qlabel: function (k) { return k.replace(/^(\d{4})-Q(\d)$/, 'T$2 $1'); },
      choose: 'Choisissez le trimestre indiqué dans votre bail',
      eur: function (n) { return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n); },
      num: function (n) { return new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n); },
      pct: function (n) { return (n > 0 ? '+' : '') + new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n) + NB + '%'; },
      date: function (iso) { var d = new Date(isoToUtc(iso)); return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }); },
      months: ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
      errRent: 'Saisissez le loyer mensuel hors charges, par exemple 600 ou 600,50.',
      errQuarter: 'Choisissez le trimestre de référence.',
      errDate: 'Saisissez une date valide, ou laissez le champ vide.',
      newRent: 'Nouveau loyer', perMonth: ' par mois', rise: 'Hausse',
      formula: 'Calcul', indexes: 'Indices',
      source: 'Insee, série 001515333. Chiffres au ',
      frozen: function (c) { return 'N’appliquez pas de révision. Un logement classé ' + c + ' au DPE ne peut pas voir son loyer révisé en cours de bail (France, baux signés, renouvelés ou reconduits depuis le 24 août 2022). Source : Service-Public.'; },
      pending: function (k, e, m) { return 'L’indice du ' + S.qlabel(k) + ' n’est pas encore publié. L’Insee le publie vers la mi-' + m[e.month] + ' ' + e.year + '. Revenez à ce moment-là, ou choisissez un autre trimestre de référence.'; },
      open: function (r, S2) { return 'Vous pouvez encore demander cette révision jusqu’au ' + S2.date(r.lastDay) + ' (' + r.daysLeft + ' jour' + (r.daysLeft > 1 ? 's' : '') + ' restant' + (r.daysLeft > 1 ? 's' : '') + '). La hausse ne compte qu’à partir du jour où vous prévenez votre locataire : elle n’est jamais rétroactive.'; },
      lost: function (r, S2) { return 'Si vous préveniez votre locataire aujourd’hui, les mois depuis le ' + S2.date(r.revisionDate) + ' seraient déjà perdus : environ ' + S2.eur(r.lostSoFar) + '. Plus vous demandez tôt, moins vous perdez.'; },
      notyet: function (r, S2) { return 'La date de révision est le ' + S2.date(r.revisionDate) + ' (dans ' + r.daysToRevision + ' jour' + (r.daysToRevision > 1 ? 's' : '') + '). Vous aurez alors jusqu’au ' + S2.date(r.lastDay) + ' pour la demander.'; },
      closed: function (r, S2) { return 'Le délai s’est terminé le ' + S2.date(r.lastDay) + '. Une révision non demandée dans l’année est perdue pour cette année. La révision suivante repart de votre loyer actuel.'; },
      checkLease: 'Vérifiez votre bail : une révision n’est possible que s’il contient une clause d’indexation. Information, pas un conseil juridique.'
    }
  }[LANG];

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function todayIso() { var d = new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function parseRent(v) {
    v = String(v || '').replace(/[\s  €]/g, '').replace(',', '.');
    return /^\d+(\.\d{1,2})?$/.test(v) ? parseFloat(v) : NaN;
  }

  function init() {
    var form = document.getElementById('irl-form'); if (!form) return;
    var sel = document.getElementById('irl-quarter'), out = document.getElementById('irl-result');
    var keys = Object.keys(IRL).sort().reverse(), lastYear = null, group = null;
    sel.appendChild(el('option', '', S.choose)).value = '';
    keys.forEach(function (k) {
      var yr = k.slice(0, 4);
      if (yr !== lastYear) { group = document.createElement('optgroup'); group.label = yr; sel.appendChild(group); lastYear = yr; }
      var o = el('option', '', S.qlabel(k) + ' — ' + S.num(IRL[k])); o.value = k; group.appendChild(o);
    });
    function setErr(id, msg) {
      var f = document.getElementById(id), box = document.getElementById(id + '-err');
      if (msg) { box.textContent = msg; box.hidden = false; f.setAttribute('aria-invalid', 'true'); } else { box.textContent = ''; box.hidden = true; f.removeAttribute('aria-invalid'); }
    }
    function line(parent, label, value) { var p = el('p', 'tool-line'); p.appendChild(el('strong', '', label + (LANG === 'fr' ? NB : '') + ': ')); p.appendChild(document.createTextNode(value)); parent.appendChild(p); }
    function run() {
      var rentRaw = document.getElementById('irl-rent').value;
      var res = compute({ rent: parseRent(rentRaw), refQuarter: sel.value, revisionDate: document.getElementById('irl-date').value,
                          dpe: document.getElementById('irl-dpe').value, today: todayIso() });
      setErr('irl-rent', res.errors && res.errors.rent ? S.errRent : '');
      setErr('irl-quarter', res.errors && res.errors.refQuarter ? S.errQuarter : '');
      setErr('irl-date', res.errors && res.errors.revisionDate ? S.errDate : '');
      out.textContent = '';
      if (res.status === 'invalid') { var bad = res.errors.rent ? 'irl-rent' : res.errors.refQuarter ? 'irl-quarter' : 'irl-date'; document.getElementById(bad).focus(); return; }
      var box = el('div', 'tool-result-box');
      if (res.status === 'frozen') { box.classList.add('tool-warn'); box.appendChild(el('p', '', S.frozen(res.dpe))); }
      else if (res.status === 'pending') { box.appendChild(el('p', '', S.pending(res.quarter, res.expected, S.months))); }
      else {
        box.appendChild(el('h3', 'tool-big', S.newRent + (LANG === 'fr' ? NB : '') + ': ' + S.eur(res.newRent) + S.perMonth));
        line(box, S.rise, S.eur(res.monthly) + S.perMonth + ' (' + S.pct(res.percent) + ')');
        line(box, S.formula, S.eur(res.rent) + ' × ' + S.num(res.newIdx) + ' ÷ ' + S.num(res.refIdx) + ' = ' + S.eur(res.newRent));
        line(box, S.indexes, S.qlabel(res.newQuarter) + ' = ' + S.num(res.newIdx) + ' ; ' + S.qlabel(res.refQuarter) + ' = ' + S.num(res.refIdx));
        if (res.window === 'open') { box.appendChild(el('p', '', S.open(res, S))); if (res.lostSoFar > 0) box.appendChild(el('p', 'tool-warn-text', S.lost(res, S))); }
        else if (res.window === 'notyet') box.appendChild(el('p', '', S.notyet(res, S)));
        else if (res.window === 'closed') { box.classList.add('tool-warn'); box.appendChild(el('p', '', S.closed(res, S))); }
        box.appendChild(el('p', 'form-note', S.source + S.date(res.asOf) + '. ' + S.checkLease));
      }
      out.appendChild(box);
    }
    form.addEventListener('submit', function (e) { e.preventDefault(); run(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})(typeof window !== 'undefined' ? window : globalThis);
