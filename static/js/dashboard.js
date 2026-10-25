// AI Smart Traffic Management System - Dashboard Core Script
// Handles Chart.js visualization, real-time metrics updates, and UI interactions

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initProfileDropdown();
    initMobileSidebar();
    initCharts();
    initDataPolling();
});

let vehicleDistChart = null;
let trafficTrendChart = null;

/**
 * Real-time digital clock in topbar
 */
function initClock() {
    const clockEl = document.getElementById('liveClock');
    if (!clockEl) return;

    function update() {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString('en-US', { hour12: false }) + ' UTC';
    }
    update();
    setInterval(update, 1000);
}

/**
 * User Profile Dropdown Toggle
 */
function initProfileDropdown() {
    const btn = document.getElementById('profileBtn');
    const dropdown = document.getElementById('profileDropdown');

    if (!btn || !dropdown) return;

    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });
}

/**
 * Mobile Sidebar Drawer Toggle
 */
function initMobileSidebar() {
    const toggleBtn = document.getElementById('mobileSidebarToggle');
    const sidebar = document.getElementById('sidebar');

    if (!toggleBtn || !sidebar) return;

    toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });
}

/**
 * Initialize Chart.js Analytics
 */
function initCharts() {
    // 1. Vehicle Distribution Doughnut Chart
    const distCtx = document.getElementById('vehicleDistChart');
    if (distCtx) {
        vehicleDistChart = new Chart(distCtx, {
            type: 'doughnut',
            data: {
                labels: ['Cars', 'Motorcycles/Bikes', 'Buses', 'Trucks'],
                datasets: [{
                    data: [42, 28, 12, 8],
                    backgroundColor: [
                        '#3b82f6', // Cars - Blue
                        '#10b981', // Bikes - Green
                        '#f59e0b', // Buses - Amber
                        '#8b5cf6'  // Trucks - Purple
                    ],
                    borderColor: '#10192e',
                    borderWidth: 3,
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#94a3b8',
                            font: { size: 11 },
                            padding: 14,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: '#0a0f1d',
                        titleColor: '#00f0ff',
                        bodyColor: '#f8fafc',
                        borderColor: 'rgba(0, 240, 255, 0.3)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                cutout: '68%'
            }
        });
    }

    // 2. Traffic Flow Volume Trend Line Chart
    const trendCtx = document.getElementById('trafficTrendChart');
    if (trendCtx) {
        const gradient = trendCtx.getContext('2d').createLinearGradient(0, 0, 0, 260);
        gradient.addColorStop(0, 'rgba(0, 240, 255, 0.35)');
        gradient.addColorStop(1, 'rgba(0, 240, 255, 0.0)');

        trafficTrendChart = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: ['06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00'],
                datasets: [{
                    label: 'Vehicles / Hour',
                    data: [35, 88, 72, 60, 68, 95, 110, 78],
                    borderColor: '#00f0ff',
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2.5,
                    pointBackgroundColor: '#00f0ff',
                    pointBorderColor: '#0a0f1d',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0a0f1d',
                        titleColor: '#00f0ff',
                        borderColor: 'rgba(0, 240, 255, 0.3)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#64748b', font: { size: 11 } }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#64748b', font: { size: 11 } },
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

/**
 * Poll live simulated traffic data from Flask backend
 */
function initDataPolling() {
    fetchTrafficData();
    // Poll every 5 seconds for simulated smart updates
    setInterval(fetchTrafficData, 5000);

    const refreshBtn = document.getElementById('manualRefreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            fetchTrafficData();
        });
    }
}

async function fetchTrafficData() {
    try {
        const response = await fetch('/api/traffic-data');
        if (!response.ok) return;

        const data = await response.json();
        updateDashboardUI(data);
    } catch (err) {
        console.warn('Live telemetry fetch notice:', err);
    }
}

/**
 * Update DOM cards, charts, and traffic signal lights dynamically
 */
function updateDashboardUI(data) {
    // 1. Update Metric Numbers
    setTextSafe('countTotal', data.total_vehicles);
    setTextSafe('countCars', data.cars);
    setTextSafe('countBikes', data.bikes);
    setTextSafe('countBuses', data.buses);
    setTextSafe('countTrucks', data.trucks);

    // 2. Update Recommended Green-light duration
    setTextSafe('recGreenTime', data.recommended_green + 's');
    setTextSafe('signalPhase', data.current_phase || 'Phase A - North/South');

    // 3. Update Density Badge
    const densityEl = document.getElementById('trafficDensity');
    if (densityEl) {
        densityEl.textContent = data.density;
        densityEl.className = 'density-badge ' + data.density.toLowerCase();
    }

    // 4. Update Traffic Light Bulbs
    const redLight = document.getElementById('lightRed');
    const yellowLight = document.getElementById('lightYellow');
    const greenLight = document.getElementById('lightGreen');

    if (redLight && yellowLight && greenLight) {
        redLight.classList.remove('active');
        yellowLight.classList.remove('active');
        greenLight.classList.remove('active');

        const activeLight = (data.light_state || 'green').toLowerCase();
        if (activeLight === 'red') redLight.classList.add('active');
        else if (activeLight === 'yellow') yellowLight.classList.add('active');
        else greenLight.classList.add('active');
    }

    // 5. Congestion Alert Banner
    const alertBanner = document.getElementById('congestionBanner');
    const alertCount = document.getElementById('alertCount');
    if (alertBanner) {
        if (data.density === 'High' || data.total_vehicles > 35) {
            alertBanner.classList.add('active');
            if (alertCount) alertCount.textContent = data.total_vehicles;
        } else {
            alertBanner.classList.remove('active');
        }
    }

    // 6. Update Chart Data
    if (vehicleDistChart) {
        vehicleDistChart.data.datasets[0].data = [
            data.cars,
            data.bikes,
            data.buses,
            data.trucks
        ];
        vehicleDistChart.update('none');
    }
}

function setTextSafe(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}
