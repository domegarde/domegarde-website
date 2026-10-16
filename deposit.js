// Domegarde free tool: when the security deposit must be returned, and what lateness costs.
// Runs entirely in the browser. Nothing typed here is sent anywhere.
// Rules: Service-Public, "Dépôt de garantie dans un bail d'habitation" (checked 16 October 2026).
(function (root) {
  'use strict';

  function round2(x) { return Math.round((x + Number.EPSILON) * 100) / 100; }
  function isoToUtc(iso) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '');
    if (!m) return null;
    var t = Date.UTC(+m[1], +m[2] - 1, +m[3]), d = new Date(t);
    if (d.getUTCFullYear() !== +m[1] || d.getUTCMonth() !== +m[2] - 1 || d.getUTCDate() !== +m[3]) return null;
    return t;
  }
  function utcToIso(t) { return new Date(t).toISOString().slice(0, 10); }
  // The same day number n months later; if that month is shorter, its last day (31 January + 1 month = 28 February).
  function addMonths(t, n) {
    var d = new Date(t), y = d.getUTCFullYear(), m = d.getUTCMonth() + n, day = d.getUTCDate();
    var last = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
    return Date.UTC(y, m, Math.min(day, last));
  }

  // opts: { keysDate, inventory: 'match' | 'differs', rent, checkDate (optional: the day the deposit is or will be returned), noAddress (bool), today }
  function compute(opts) {
    var errors = {};
    var keysT = isoToUtc(opts.keysDate); if (keysT === null) errors.keysDate = true;
    if (opts.inventory !== 'match' && opts.inventory !== 'differs') errors.inventory = true;
    var rent = opts.rent; if (!(rent > 0) || rent > 100000) errors.rent = true;
    var checkT = null; if (opts.checkDate) { checkT = isoToUtc(opts.checkDate); if (checkT === null) errors.checkDate = true; }
    if (Object.keys(errors).length) return { status: 'invalid', errors: errors };

    var base = opts.inventory === 'match' ? 1 : 2;
    var deadlineT = addMonths(keysT, base);
    var todayT = isoToUtc(opts.today || utcToIso(Date.now()));
    var usedT = checkT !== null ? checkT : todayT;
    var out = { status: 'ok', deadline: utcToIso(deadlineT), baseMonths: base, rent: rent, monthlyPenalty: round2(rent * 0.10),
                checkedOn: utcToIso(usedT), usedToday: checkT === null };
    if (usedT <= deadlineT) {
      out.late = false; out.daysLeft = Math.round((deadlineT - usedT) / 86400000); out.months = 0; out.penalty = 0;
      return out;
    }
    var k = 1; while (usedT > addMonths(keysT, base + k)) k++;
    out.late = true; out.daysLate = Math.round((usedT - deadlineT) / 86400000); out.months = k;
    out.noAddress = !!opts.noAddress;
    out.penalty = opts.noAddress ? 0 : round2(rent * 0.10 * k);
    out.penaltyIfAddress = round2(rent * 0.10 * k);
    return out;
  }

  root.DomegardeDeposit = { compute: compute };
  if (typeof module !== 'undefined' && module.exports) module.exports = root.DomegardeDeposit;

  // ---------------------------------------------------------------- page
  if (typeof document === 'undefined') return;
  var LANG = (document.documentElement.lang || 'en').toLowerCase().indexOf('fr') === 0 ? 'fr' : 'en';
  var NB = ' ';
  var S = {
    en: {
      eur: function (n) { return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'EUR' }).format(n); },
      date: function (iso) { return new Date(isoToUtc(iso)).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }); },
      errKeys: 'Enter the date the tenant handed back the keys.', errInv: 'Choose whether the exit inventory matches the entry inventory.',
      errRent: 'Enter the monthly rent excluding charges, for example 600 or 600.50.', errCheck: 'Enter a valid date, or leave it empty.',
      deadline: 'Last day to return the deposit', rule: function (b) { return b === 1 ? 'One month after the keys were handed back (inventories match).' : 'Two months after the keys were handed back (inventories differ).'; },
      onTime: function (r, S2) { return r.usedToday ? 'Today (' + S2.date(r.checkedOn) + ') you are within the deadline: ' + r.daysLeft + ' day' + (r.daysLeft === 1 ? '' : 's') + ' left.' : 'Returned on ' + S2.date(r.checkedOn) + ': within the deadline. No late penalty.'; },
      late: function (r, S2) { return (r.usedToday ? 'Today (' + S2.date(r.checkedOn) + ')' : 'On ' + S2.date(r.checkedOn)) + ' the deposit is ' + r.daysLate + ' day' + (r.daysLate === 1 ? '' : 's') + ' late: ' + r.months + ' month' + (r.months === 1 ? '' : 's') + ' started.'; },
      penalty: 'Late penalty', perMonth: ' (10% of the monthly rent, excluding charges, for each month started late: ',
      noAddr: function (r, S2) { return 'No penalty applies because the delay was caused by the tenant not giving a new address. Otherwise it would be ' + S2.eur(r.penaltyIfAddress) + '.'; },
      notice: 'To recover a late deposit the tenant has to send a formal notice (mise en demeure). The penalty is added to the deposit you owe, on top of anything you may lawfully keep.',
      keep: 'You may keep justified amounts (unpaid rent or charges, repairs) with proof such as invoices or quotes. In a building with shared charges you may keep a provision of up to 20% of the deposit until the building’s annual accounts are approved.',
      foot: 'Source: Service-Public, checked 16 October 2026. We count calendar days and do not extend a deadline for weekends or public holidays. Information, not legal advice.'
    },
    fr: {
      eur: function (n) { return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(n); },
      date: function (iso) { return new Date(isoToUtc(iso)).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }); },
      errKeys: 'Saisissez la date à laquelle le locataire a rendu les clés.', errInv: 'Indiquez si l’état des lieux de sortie est conforme à celui d’entrée.',
      errRent: 'Saisissez le loyer mensuel hors charges, par exemple 600 ou 600,50.', errCheck: 'Saisissez une date valide, ou laissez le champ vide.',
      deadline: 'Dernier jour pour rendre le dépôt', rule: function (b) { return b === 1 ? 'Un mois après la remise des clés (états des lieux conformes).' : 'Deux mois après la remise des clés (états des lieux différents).'; },
      onTime: function (r, S2) { return r.usedToday ? 'Aujourd’hui (' + S2.date(r.checkedOn) + '), vous êtes dans le délai : ' + r.daysLeft + ' jour' + (r.daysLeft > 1 ? 's' : '') + ' restant' + (r.daysLeft > 1 ? 's' : '') + '.' : 'Rendu le ' + S2.date(r.checkedOn) + ' : dans le délai. Aucune pénalité de retard.'; },
      late: function (r, S2) { return (r.usedToday ? 'Aujourd’hui (' + S2.date(r.checkedOn) + ')' : 'Le ' + S2.date(r.checkedOn)) + ', le dépôt a ' + r.daysLate + ' jour' + (r.daysLate > 1 ? 's' : '') + ' de retard : ' + r.months + ' mois commencé' + (r.months > 1 ? 's' : '') + '.'; },
      penalty: 'Pénalité de retard', perMonth: ' (10 % du loyer mensuel hors charges par mois de retard commencé : ',
      noAddr: function (r, S2) { return 'Aucune pénalité ne s’applique car le retard est dû au fait que le locataire n’a pas donné sa nouvelle adresse. Sinon elle serait de ' + S2.eur(r.penaltyIfAddress) + '.'; },
      notice: 'Pour récupérer un dépôt rendu en retard, le locataire doit envoyer une mise en demeure. La pénalité s’ajoute au dépôt dû, en plus de ce que vous pouvez légalement retenir.',
      keep: 'Vous pouvez retenir les sommes justifiées (loyers ou charges impayés, réparations) avec des justificatifs tels que factures ou devis. Dans un immeuble avec charges collectives, vous pouvez conserver une provision d’au plus 20 % du dépôt jusqu’à l’approbation des comptes annuels de l’immeuble.',
      foot: 'Source : Service-Public, vérifié le 16 octobre 2026. Nous comptons en jours calendaires et ne reportons pas un délai pour les week-ends ou jours fériés. Information, pas un conseil juridique.'
    }
  }[LANG];

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function todayIso() { var d = new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function parseRent(v) { v = String(v || '').replace(/[\s  €]/g, '').replace(',', '.'); return /^\d+(\.\d{1,2})?$/.test(v) ? parseFloat(v) : NaN; }

  function init() {
    var form = document.getElementById('dep-form'); if (!form) return;
    var out = document.getElementById('dep-result');
    function setErr(id, msg) {
      var f = document.getElementById(id), box = document.getElementById(id + '-err');
      if (msg) { box.textContent = msg; box.hidden = false; f.setAttribute('aria-invalid', 'true'); } else { box.textContent = ''; box.hidden = true; f.removeAttribute('aria-invalid'); }
    }
    function line(parent, label, value) { var p = el('p', 'tool-line'); p.appendChild(el('strong', '', label + (LANG === 'fr' ? NB : '') + ': ')); p.appendChild(document.createTextNode(value)); parent.appendChild(p); }
    function run() {
      var res = compute({ keysDate: document.getElementById('dep-keys').value, inventory: document.getElementById('dep-inv').value,
        rent: parseRent(document.getElementById('dep-rent').value), checkDate: document.getElementById('dep-check').value,
        noAddress: document.getElementById('dep-noaddr').checked, today: todayIso() });
      setErr('dep-keys', res.errors && res.errors.keysDate ? S.errKeys : '');
      setErr('dep-inv', res.errors && res.errors.inventory ? S.errInv : '');
      setErr('dep-rent', res.errors && res.errors.rent ? S.errRent : '');
      setErr('dep-check', res.errors && res.errors.checkDate ? S.errCheck : '');
      out.textContent = '';
      if (res.status === 'invalid') { var bad = res.errors.keysDate ? 'dep-keys' : res.errors.inventory ? 'dep-inv' : res.errors.rent ? 'dep-rent' : 'dep-check'; document.getElementById(bad).focus(); return; }
      var box = el('div', 'tool-result-box' + (res.late && res.penalty > 0 ? ' tool-warn' : ''));
      box.appendChild(el('h3', 'tool-big', S.deadline + (LANG === 'fr' ? NB : '') + ': ' + S.date(res.deadline)));
      box.appendChild(el('p', '', S.rule(res.baseMonths)));
      if (!res.late) { box.appendChild(el('p', '', S.onTime(res, S))); }
      else {
        box.appendChild(el('p', '', S.late(res, S)));
        if (res.noAddress) box.appendChild(el('p', '', S.noAddr(res, S)));
        else {
          line(box, S.penalty, S.eur(res.penalty) + S.perMonth + S.eur(res.rent) + ' × 10% × ' + res.months + ')');
          box.appendChild(el('p', '', S.notice));
        }
      }
      box.appendChild(el('p', '', S.keep));
      box.appendChild(el('p', 'form-note', S.foot));
      out.appendChild(box);
    }
    form.addEventListener('submit', function (e) { e.preventDefault(); run(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})(typeof window !== 'undefined' ? window : globalThis);
