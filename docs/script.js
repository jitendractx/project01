fetch('dora_metrics.json')
  .then(response => response.json())
  .then(data => {
    const ctx = document.getElementById('doraChart').getContext('2d');
    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Deployment Frequency', 'Lead Time (hrs)'],
        datasets: [{
          label: 'Latest DORA Metrics',
          data: [data.deployment_frequency, data.average_lead_time_hours],
          backgroundColor: ['#4CAF50', '#FF9800']
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
  })
  .catch(err => {
    console.error('Failed to load metrics:', err);
  });
