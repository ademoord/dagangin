document.addEventListener('DOMContentLoaded', function () {
  document.addEventListener('keydown', function (e) {
    if (e.key === 'F9') {
      e.preventDefault();
      var btn = document.getElementById('pay-btn');
      if (btn) {
        var notes = document.getElementById('notes');
        var checkoutNotes = document.getElementById('checkout-notes');
        if (notes && checkoutNotes) {
          checkoutNotes.value = notes.value;
        }
        btn.closest('form').submit();
      }
    }
  });

  document.body.addEventListener('htmx:afterRequest', function (event) {
    if (event.detail.successful && event.detail.target.id === 'cart-root') {
      var productId = event.detail.elt.getAttribute('data-product-id');
      if (productId) {
        updateRecentCookie(productId);
      }
    }
  });
});

function updateRecentCookie(productId) {
  var existing = document.cookie.match(/recent_products=([^;]+)/);
  var ids = existing ? existing[1].split(',').filter(Boolean) : [];
  ids = ids.filter(function (id) { return id !== productId; });
  ids.unshift(productId);
  ids = ids.slice(0, 8);
  document.cookie = 'recent_products=' + ids.join(',') + ';path=/;max-age=2592000';
}
