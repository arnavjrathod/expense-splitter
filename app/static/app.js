// Real-time split discrepancy feedback (FR-02) + delete confirms (FR-04/06/07 UX).
document.addEventListener('DOMContentLoaded', function () {
  // Confirmation prompts on destructive actions
  document.querySelectorAll('form[data-warn]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!window.confirm(form.dataset.warn)) e.preventDefault();
    });
  });

  var table = document.querySelector('.split-table');
  if (!table) return;
  var form = document.getElementById('expense-form');
  var amountInput = document.getElementById('amount');
  var status = document.getElementById('split-status');

  function rows() {
    return Array.prototype.slice.call(table.querySelectorAll('tr[data-uid]'));
  }
  function currentType() {
    var el = form.querySelector('input[name="split_type"]:checked');
    return el ? el.value : 'equal';
  }
  function fmt(cents) {
    var sign = cents < 0 ? '-' : '';
    var a = Math.abs(cents);
    return sign + Math.floor(a / 100) + '.' + String(a % 100).padStart(2, '0');
  }
  function toCents(v) { return Math.round(parseFloat(v || '0') * 100); }

  function update() {
    var type = currentType();
    var total = toCents(amountInput.value);
    rows().forEach(function (row) {
      var uid = row.dataset.uid;
      var eq = row.querySelector('.participant');
      var pct = row.querySelector('.pct-col input');
      var amt = row.querySelector('.amt-col input');
      var preview = row.querySelector('.preview');
      eq.parentElement.parentElement.style.opacity = type === 'equal' ? 1 : 0.45;
      pct.disabled = type !== 'percentage';
      amt.disabled = type !== 'exact';
      if (!eq.checked) { preview.textContent = '—'; return; }
      var cents = 0;
      if (type === 'equal' && total > 0) {
        var selected = rows().filter(function (r) {
          return r.querySelector('.participant').checked;
        }).length;
        cents = selected ? Math.floor(total / selected) : 0;
      } else if (type === 'percentage') {
        cents = Math.round(total * toCents(pct.value) / 10000);
      } else if (type === 'exact') {
        cents = toCents(amt.value);
      }
      preview.textContent = cents ? fmt(cents) : '0.00';
    });

    var mismatch = '';
    if (total <= 0) {
      mismatch = '';
    } else if (type === 'percentage') {
      var bpTotal = rows().reduce(function (s, r) {
        return s + toCents(r.querySelector('.pct-col input').value);
      }, 0);
      if (bpTotal !== 10000)
        mismatch = 'Percentages total ' + (bpTotal / 100).toFixed(2) +
          '% — must be exactly 100%.';
    } else if (type === 'exact') {
      var sum = rows().reduce(function (s, r) {
        return s + toCents(r.querySelector('.amt-col input').value);
      }, 0);
      if (sum !== total)
        mismatch = 'Exact amounts total ' + fmt(sum) + ' — must equal ' +
          fmt(total) + '.';
    }
    if (mismatch) {
      status.textContent = '⚠ ' + mismatch;
      status.className = 'neg';
    } else {
      status.textContent = type === 'equal'
        ? 'Splitting equally among checked members.'
        : '✓ Split adds up.';
      status.className = 'muted';
    }
  }

  form.addEventListener('input', update);
  form.addEventListener('change', update);
  update();
});
