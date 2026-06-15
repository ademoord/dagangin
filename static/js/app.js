(function () {
  function currentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'light';
  }

  function syncToggle(theme) {
    var moon = document.getElementById('themeIconMoon');
    var sun = document.getElementById('themeIconSun');
    var label = document.querySelector('.theme-toggle-label');
    var isDark = theme === 'dark';

    if (moon) moon.style.display = isDark ? 'none' : 'block';
    if (sun) sun.style.display = isDark ? 'block' : 'none';
    if (label) label.textContent = isDark ? 'Terang' : 'Gelap';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    syncToggle(theme);
    window.dispatchEvent(new CustomEvent('dagangin-theme-changed', { detail: { theme: theme } }));
  }

  window.DaganginTheme = {
    current: currentTheme,
    apply: applyTheme,
    chartColors: function () {
      var styles = getComputedStyle(document.documentElement);
      return {
        primary: styles.getPropertyValue('--color-primary').trim() || '#2F645C',
        accent: styles.getPropertyValue('--color-accent').trim() || '#89C6B8',
        primaryLight: styles.getPropertyValue('--color-primary-light').trim() || 'rgba(47, 100, 92, 0.15)',
        text: styles.getPropertyValue('--color-text-secondary').trim() || '#5A5C5B',
      };
    },
  };

  document.addEventListener('DOMContentLoaded', function () {
    syncToggle(currentTheme());

    document.addEventListener('click', function (e) {
      var toggle = e.target.closest('#themeToggle');
      if (!toggle) return;
      e.preventDefault();
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    });
  });
})();

document.addEventListener('DOMContentLoaded', function () {
  document.body.addEventListener('htmx:configRequest', function (event) {
    var token = document.querySelector('meta[name=csrf-token]');
    if (token) {
      event.detail.headers['X-CSRFToken'] = token.content;
    }
  });

  document.body.addEventListener('htmx:afterOnLoad', function (event) {
    if (event.detail.target && event.detail.target.id === 'cart-root') {
      var elt = event.detail.elt;
      var productId = elt && elt.getAttribute('data-product-id');
      if (productId && typeof updateRecentCookie === 'function') {
        updateRecentCookie(productId);
      }
    }
  });
});
