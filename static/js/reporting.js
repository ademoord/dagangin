document.addEventListener('DOMContentLoaded', function () {
  var period = window.DAGANGIN_PERIOD || '30';
  var query = '?period=' + encodeURIComponent(period);
  var charts = [];

  function colors() {
    if (window.DaganginTheme && window.DaganginTheme.chartColors) {
      return window.DaganginTheme.chartColors();
    }
    return { primary: '#2F645C', accent: '#89C6B8', primaryLight: 'rgba(47, 100, 92, 0.15)', text: '#5A5C5B' };
  }

  function chartScaleOptions() {
    var c = colors();
    return {
      x: {
        ticks: { color: c.text },
        grid: { color: 'rgba(127, 127, 127, 0.15)' },
      },
      y: {
        ticks: { color: c.text },
        grid: { color: 'rgba(127, 127, 127, 0.15)' },
      },
    };
  }

  function sparkline(canvasId, metric) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    fetch('/reporting/api/sparkline/' + metric + query)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var c = colors();
        var chart = new Chart(canvas.getContext('2d'), {
          type: 'line',
          data: {
            labels: data.values.map(function (_, i) { return i + 1; }),
            datasets: [{
              data: data.values,
              borderColor: c.primary,
              backgroundColor: c.primaryLight,
              fill: true,
              tension: 0.4,
              pointRadius: 0,
              borderWidth: 2,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { display: false }, y: { display: false } },
          },
        });
        charts.push(chart);
      });
  }

  function lineChart(canvasId, url, label) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    fetch(url + query)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var c = colors();
        var chart = new Chart(canvas.getContext('2d'), {
          type: 'line',
          data: {
            labels: data.labels,
            datasets: [{
              label: label,
              data: data.values,
              borderColor: c.primary,
              backgroundColor: c.primaryLight,
              fill: true,
              tension: 0.3,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: chartScaleOptions(),
          },
        });
        charts.push(chart);
      });
  }

  sparkline('spark-sales', 'sales');
  sparkline('spark-profit', 'profit');
  sparkline('spark-orders', 'orders');
  sparkline('spark-avg', 'avg');

  lineChart('salesChart', '/reporting/api/sales-chart', 'Penjualan');

  var stockCanvas = document.getElementById('stockChart');
  if (stockCanvas) {
    fetch('/reporting/api/stock-chart' + query)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var c = colors();
        var chart = new Chart(stockCanvas.getContext('2d'), {
          type: 'bar',
          data: {
            labels: data.labels,
            datasets: [
              { label: 'Masuk', data: data.stock_in, backgroundColor: c.accent },
              { label: 'Keluar', data: data.stock_out, backgroundColor: c.primary },
            ],
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { labels: { color: colors().text } },
            },
            scales: chartScaleOptions(),
          },
        });
        charts.push(chart);
      });
  }

  var purchaseCanvas = document.getElementById('purchaseChart');
  if (purchaseCanvas) {
    fetch('/reporting/api/purchase-chart' + query)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var c = colors();
        var chart = new Chart(purchaseCanvas.getContext('2d'), {
          type: 'doughnut',
          data: {
            labels: data.labels,
            datasets: [{
              data: data.values,
              backgroundColor: [c.primary, c.accent, '#5F9F92', '#3F8081', '#27454E'],
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
          },
        });
        charts.push(chart);
      });
  }

  window.addEventListener('dagangin-theme-changed', function () {
    var c = colors();
    charts.forEach(function (chart) {
      chart.data.datasets.forEach(function (ds, i) {
        if (chart.config.type === 'doughnut') {
          ds.backgroundColor = [c.primary, c.accent, '#5F9F92', '#3F8081', '#27454E'];
        } else if (chart.config.type === 'bar') {
          ds.backgroundColor = i === 0 ? c.accent : c.primary;
        } else {
          ds.borderColor = c.primary;
          ds.backgroundColor = c.primaryLight;
        }
      });
      if (chart.options.scales) {
        var scales = chartScaleOptions();
        Object.keys(scales).forEach(function (axis) {
          if (chart.options.scales[axis]) {
            chart.options.scales[axis].ticks = scales[axis].ticks;
            chart.options.scales[axis].grid = scales[axis].grid;
          }
        });
      }
      if (chart.options.plugins && chart.options.plugins.legend) {
        chart.options.plugins.legend.labels.color = c.text;
      }
      chart.update();
    });
  });
});
