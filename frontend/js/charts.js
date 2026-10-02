/**
 * Clean Threat intelligence Bar Chart renderer for Chat Bubbles
 */

let chartInstancesMap = {};

function renderInlineThreatChart(canvasId, labels, scores) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');

    if (chartInstancesMap[canvasId]) {
        chartInstancesMap[canvasId].destroy();
    }

    const barColors = [
        'rgba(255, 51, 102, 0.85)',   // Phishing
        'rgba(255, 170, 0, 0.85)',    // Malware
        'rgba(157, 78, 221, 0.85)',   // Reputation
        'rgba(0, 243, 255, 0.85)',    // Obfuscation
        'rgba(0, 255, 157, 0.85)'     // Connection
    ];

    const borderColors = ['#ff3366', '#ffaa00', '#9d4edd', '#00f3ff', '#00ff9d'];

    chartInstancesMap[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Risk Score (0 - 100%)',
                data: scores,
                backgroundColor: barColors,
                borderColor: borderColors,
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 800 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0b0f19',
                    titleColor: '#00f3ff',
                    bodyColor: '#ffffff',
                    borderColor: 'rgba(0, 243, 255, 0.3)',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8', font: { size: 11, family: 'Inter' } }
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8', font: { size: 10 }, stepSize: 25 }
                }
            }
        }
    });
}
