// ============================================================
// Domegarde marketing site — shared behaviour
// Forms write directly to Supabase's `contacts` table via the
// auto-generated REST API (PostgREST). No backend server needed.
// ============================================================

// --- Supabase connection -------------------------------------------------
// Public/anon credentials only — safe to expose client-side.
// Row Level Security on `contacts` allows public INSERT and nothing else.
const SUPABASE_URL = 'https://eijwocytpslnxvkgnvgh.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_ok-gbn36McHXGbu_ZC-56w_xUYOocW6';

// Messages shown by the forms, in the language of the page.
const LANG = (document.documentElement.lang || 'en').toLowerCase().indexOf('fr') === 0 ? 'fr' : 'en';
const MESSAGES = {
  en: {
    sending: 'Sending\u2026',
    error: 'Something went wrong sending that. Please try again, or email us directly.'
  },
  fr: {
    sending: 'Envoi\u2026',
    error: "Une erreur est survenue lors de l'envoi. Merci de r\u00e9essayer, ou \u00e9crivez-nous directement."
  }
};

async function insertContact(payload) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/contacts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': SUPABASE_ANON_KEY,
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
      'Prefer': 'return=minimal'
    },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || `Request failed (${res.status})`);
  }
}

function wireForm(formId, statusId, buildPayload, successText) {
  const form = document.getElementById(formId);
  if (!form) return;
  const status = document.getElementById(statusId);
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    // Name, email and message must be filled in and valid before anything is sent.
    if (!form.checkValidity()) { form.reportValidity(); return; }
    const btn = form.querySelector('button[type="submit"]');
    const originalLabel = btn.textContent;
    btn.disabled = true;
    btn.textContent = MESSAGES[LANG].sending;
    status.classList.remove('show', 'ok', 'err');

    try {
      const payload = buildPayload(new FormData(form));
      await insertContact(payload);
      status.textContent = successText[LANG];
      status.classList.add('show', 'ok');
      form.reset();
    } catch (err) {
      status.textContent = MESSAGES[LANG].error;
      status.classList.add('show', 'err');
    } finally {
      btn.disabled = false;
      btn.textContent = originalLabel;
    }
  });
}

// --- Nav toggle (mobile) --------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', links.classList.contains('open'));
    });
  }

  // Scroll reveal
  const revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add('visible'));
  }

  // Wide tables scroll sideways on small screens. Make that scroll area reachable with
  // the keyboard, but only while it actually scrolls (no pointless tab stop otherwise).
  const scrollers = document.querySelectorAll('.compare-wrap, .table-scroll');
  const markScrollers = () => scrollers.forEach((el) => {
    if (el.scrollWidth > el.clientWidth + 1) {
      el.setAttribute('tabindex', '0');
      el.setAttribute('role', 'region');
      el.setAttribute('aria-label', el.getAttribute('data-label') || '');
    } else {
      el.removeAttribute('tabindex');
      el.removeAttribute('role');
      el.removeAttribute('aria-label');
    }
  });
  markScrollers();
  window.addEventListener('resize', markScrollers);
  window.addEventListener('load', markScrollers);

  // Wire known forms if present on this page
  wireForm('about-contact-form', 'about-contact-status', (fd) => ({
    name: fd.get('name'),
    email: fd.get('email'),
    phone: fd.get('phone') || null,
    preferred_language: fd.get('preferred_language') || null,
    message: fd.get('message') || null
  }), {
    en: 'Thanks \u2014 we\u2019ve received your details and will be in touch shortly.',
    fr: "Merci \u2014 nous avons bien re\u00e7u vos coordonn\u00e9es et reviendrons vers vous rapidement."
  });

  wireForm('get-started-form', 'get-started-status', (fd) => ({
    name: fd.get('name'),
    email: fd.get('email'),
    phone: fd.get('phone') || null,
    number_of_properties: fd.get('number_of_properties') ? parseInt(fd.get('number_of_properties'), 10) : null,
    plan_interest: fd.get('plan_interest') || null,
    preferred_language: fd.get('preferred_language') || null,
    message: fd.get('message') || null,
    // Separate, unticked-by-default tick box. The enquiry works without it.
    marketing_consent: fd.get('marketing_consent') === 'yes'
  }), {
    en: 'Thanks \u2014 we\u2019ve received your request. We\u2019ll email you, usually within one business day.',
    fr: "Merci \u2014 nous avons bien re\u00e7u votre demande. Nous vous r\u00e9pondrons par e-mail, g\u00e9n\u00e9ralement sous un jour ouvr\u00e9."
  });
});
