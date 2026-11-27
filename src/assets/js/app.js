(function () {
  // mobile menu
  var mb = document.querySelector('.menu-btn'), ul = document.querySelector('.nav ul');
  if (mb && ul) mb.addEventListener('click', function () {
    var open = ul.classList.toggle('open'); mb.setAttribute('aria-expanded', open);
  });

  // product gallery
  var gm = document.getElementById('gmain');
  if (gm) [].slice.call(document.querySelectorAll('.gt')).forEach(function (b) {
    b.addEventListener('click', function () {
      var stage = gm.parentNode, old = stage.querySelector('video');
      if (old) stage.removeChild(old);
      if (b.dataset.video) {
        var v = document.createElement('video'); v.src = b.dataset.video; v.poster = b.dataset.poster || '';
        v.controls = true; v.autoplay = true; v.playsInline = true; v.className = 'gvideo'; gm.hidden = true; stage.appendChild(v);
      } else { gm.hidden = false; gm.src = b.dataset.src; }
    });
  });

  // shop filtering (progressive enhancement: the full grid is already in the HTML)
  var grid = document.getElementById('product-grid');
  if (!grid) return;
  var cards = [].slice.call(grid.children);
  var q = document.getElementById('q'), sort = document.getElementById('sort');
  var chips = [].slice.call(document.querySelectorAll('.chip'));
  var count = document.getElementById('result-count'), empty = document.getElementById('empty');
  var state = { cat: 'all', q: '', sort: 'new' };

  var params = new URLSearchParams(location.search);
  if (params.get('cat')) state.cat = params.get('cat');
  if (params.get('q')) { state.q = params.get('q').toLowerCase(); q.value = params.get('q'); }

  function apply() {
    var shown = cards.filter(function (c) {
      var ok = (state.cat === 'all' || c.dataset.cat === state.cat) &&
               (!state.q || c.dataset.title.indexOf(state.q) > -1);
      c.hidden = !ok; return ok;
    });
    shown.sort(function (a, b) {
      if (state.sort === 'low') return a.dataset.price - b.dataset.price;
      if (state.sort === 'high') return b.dataset.price - a.dataset.price;
      return a.dataset.order - b.dataset.order;
    }).forEach(function (c) { grid.appendChild(c); });
    count.textContent = shown.length + (shown.length === 1 ? ' design' : ' designs');
    empty.hidden = shown.length > 0;
    chips.forEach(function (ch) { ch.setAttribute('aria-pressed', ch.dataset.cat === state.cat); });
  }
  chips.forEach(function (ch) { ch.addEventListener('click', function () { state.cat = ch.dataset.cat; apply(); }); });
  q.addEventListener('input', function () { state.q = q.value.trim().toLowerCase(); apply(); });
  sort.addEventListener('change', function () { state.sort = sort.value; apply(); });
  apply();
})();
