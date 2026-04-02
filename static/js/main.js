/* ─────────────────────────────────────────────────────────────────────────
   IronForge Nigeria — Main JavaScript
────────────────────────────────────────────────────────────────────────── */

// ── Navbar scroll shadow ──────────────────────────────────────────────────
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 10);
  }, { passive: true });
}

// ── Mobile menu toggle ────────────────────────────────────────────────────
const mobileBtn  = document.getElementById('mobile-menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
if (mobileBtn && mobileMenu) {
  mobileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    mobileMenu.classList.toggle('open');
  });
  document.addEventListener('click', (e) => {
    if (!mobileBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
      mobileMenu.classList.remove('open');
    }
  });
}

// ── Scroll-reveal ────────────────────────────────────────────────────────
(function initReveal() {
  const els = document.querySelectorAll('.reveal');
  if (!els.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  els.forEach(el => observer.observe(el));
})();

// ── Toast notification helper ─────────────────────────────────────────────
function showToast(message, type = 'success') {
  const colours = {
    success: 'bg-green-600',
    error:   'bg-red-600',
    info:    'bg-forge-black',
  };

  const toast = document.createElement('div');
  toast.className = [
    'fixed bottom-6 left-1/2 -translate-x-1/2 z-[9999]',
    'flex items-center gap-3 px-6 py-3 rounded-xl shadow-2xl',
    'text-white text-sm font-semibold tracking-wide',
    'transition-all duration-300 opacity-0 translate-y-4',
    colours[type] || colours.info,
  ].join(' ');
  toast.textContent = message;
  document.body.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      toast.classList.remove('opacity-0', 'translate-y-4');
    });
  });

  // Auto-remove after 3 s
  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-4');
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }, 3000);
}

// ── AJAX Add to Cart ──────────────────────────────────────────────────────
document.querySelectorAll('form').forEach(form => {
  const btn = form.querySelector('.add-to-cart-btn');
  if (!btn) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const originalText = btn.textContent.trim();
    btn.textContent = 'Adding…';
    btn.disabled = true;

    try {
      const response = await fetch(form.action, {
        method:  'POST',
        body:    new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          // Update cart badge
          const badge = document.getElementById('cart-badge');
          if (badge) {
            badge.textContent = data.cart_count;
            badge.classList.remove('hidden');
            // Bounce badge
            badge.classList.add('scale-125');
            setTimeout(() => badge.classList.remove('scale-125'), 200);
          }

          // Button feedback
          btn.textContent = '✓ Added!';
          btn.style.background = '#16a34a'; // green-600
          showToast(`${data.product_name || 'Item'} added to cart`);

          setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
            btn.disabled = false;
          }, 1600);
        } else {
          form.submit();
        }
      } else {
        form.submit();
      }
    } catch {
      form.submit();
    }
  });
});

// ── Auto-dismiss flash messages after 5 s ────────────────────────────────
document.querySelectorAll('.flash-msg').forEach(msg => {
  setTimeout(() => {
    msg.style.transition = 'opacity .4s, transform .4s';
    msg.style.opacity    = '0';
    msg.style.transform  = 'translateY(-8px)';
    setTimeout(() => msg.remove(), 400);
  }, 5000);
});

// ── Quantity helpers (product detail page) ───────────────────────────────
window.incrementQty = function () {
  const input = document.getElementById('qty-input');
  if (input && parseInt(input.value) < 100) input.value = parseInt(input.value) + 1;
};
window.decrementQty = function () {
  const input = document.getElementById('qty-input');
  if (input && parseInt(input.value) > 1) input.value = parseInt(input.value) - 1;
};

// ── Image thumbnail switcher (product detail page) ──────────────────────
window.setMainImage = function (src, thumb) {
  const img = document.getElementById('main-image');
  if (img) {
    img.style.opacity = '0';
    img.style.transition = 'opacity .2s';
    setTimeout(() => {
      img.src = src;
      img.style.opacity = '1';
    }, 200);
  }
  // Highlight active thumb
  document.querySelectorAll('.thumb-btn').forEach(t => t.classList.remove('ring-2','ring-forge-orange'));
  if (thumb) thumb.classList.add('ring-2','ring-forge-orange');
};

// ── Animate cart badge on any add ────────────────────────────────────────
(function patchBadge() {
  const badge = document.getElementById('cart-badge');
  if (!badge) return;
  const style = document.createElement('style');
  style.textContent = `
    #cart-badge { transition: transform .2s ease; }
    #cart-badge.scale-125 { transform: scale(1.25); }
  `;
  document.head.appendChild(style);
})();

// ── Newsletter Subscription ───────────────────────────────────────────────
const newsletterForm = document.getElementById('newsletter-form');
if (newsletterForm) {
  newsletterForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = newsletterForm.querySelector('button[type="submit"]');
    const input = newsletterForm.querySelector('input[type="email"]');
    const originalText = btn.textContent;
    btn.textContent = '...';
    btn.disabled = true;

    try {
      const fd = new FormData(newsletterForm);
      const res = await fetch(newsletterForm.action, { method: 'POST', body: fd, headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      const data = await res.json();
      if (data.success) {
        showToast(data.message, 'success');
        input.value = '';
      }
    } catch {
      showToast('An error occurred. Please try again.', 'error');
    }

    btn.textContent = originalText;
    btn.disabled = false;
  });
}
