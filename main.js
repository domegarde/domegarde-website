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

function wireForm(formId, statusId, buildPayload) {
  const form = document.getElementById(formId);
  if (!form) return;
  const status = document.getElementById(statusId);
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const originalLabel = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Sending…';
    status.classList.remove('show', 'ok', 'err');

    try {
      const payload = buildPayload(new FormData(form));
      await insertContact(payload);
      status.textContent = 'Thanks — we\u2019ve received your details and will be in touch shortly.';
      status.classList.add('show', 'ok');
      form.reset();
    } catch (err) {
      status.textContent = 'Something went wrong sending that. Please try again, or email us directly.';
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

  // Wire known forms if present on this page
  wireForm('about-contact-form', 'about-contact-status', (fd) => ({
    name: fd.get('name'),
    email: fd.get('email'),
    phone: fd.get('phone') || null,
    message: fd.get('message') || null
  }));

  wireForm('get-started-form', 'get-started-status', (fd) => ({
    name: fd.get('name'),
    email: fd.get('email'),
    phone: fd.get('phone') || null,
    number_of_properties: fd.get('number_of_properties') ? parseInt(fd.get('number_of_properties'), 10) : null,
    plan_interest: fd.get('plan_interest') || null,
    message: fd.get('message') || null
  }));
});
