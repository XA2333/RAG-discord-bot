from flask import Flask, jsonify, render_template_string
import os
from backend.observability import ObservabilityLogger

app = Flask(__name__)
logger = ObservabilityLogger()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG Bot Monitor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .card { box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: none; margin-bottom: 20px; }
        .metric-value { font-size: 2rem; font-weight: bold; }
        .status-ok { color: #198754; }
        .status-fail { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>🤖 RAG Bot Dashboard</h1>
            <span id="last-updated" class="text-muted">Loading...</span>
        </div>

        <!-- KPI Cards -->
        <div class="row">
            <div class="col-md-3">
                <div class="card p-3">
                    <h5 class="text-muted">Total Queries (24h)</h5>
                    <div class="metric-value" id="total-queries">-</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card p-3">
                    <h5 class="text-muted">Avg Latency (ms)</h5>
                    <div class="metric-value" id="avg-latency">-</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card p-3">
                    <h5 class="text-muted">Error Rate (24h)</h5>
                    <div class="metric-value" id="error-rate">-</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card p-3">
                    <h5 class="text-muted">Total Sources</h5>
                    <div class="metric-value" id="total-sources">-</div>
                </div>
            </div>
        </div>

        <!-- Recent Logs -->
        <div class="card p-4">
            <h4>Recent Events</h4>
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Time (UTC)</th>
                            <th>Event</th>
                            <th>Status</th>
                            <th>Duration (ms)</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody id="logs-table">
                        <!-- Populated by JS -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        async function updateDashboard() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();

                // KPIs
                document.getElementById('total-queries').innerText = data.metrics.total_queries_24h || 0;
                
                // Calculate avg latency from breakdown if available, else 0
                const queryStats = data.metrics.breakdown?.query || {};
                document.getElementById('avg-latency').innerText = queryStats.avg_ms || 0;
                
                document.getElementById('error-rate').innerText = (data.metrics.error_rate_24h || 0) + '%';
                
                // DB Stats
                document.getElementById('total-sources').innerText = data.db_stats.total_sources || 0;

                // Logs Table
                const tbody = document.getElementById('logs-table');
                tbody.innerHTML = '';
                data.logs.forEach(log => {
                    const row = document.createElement('tr');
                    const statusClass = log.status === 'ok' ? 'status-ok' : 'status-fail';
                    const metaStr = log.meta ? JSON.stringify(log.meta) : '';
                    const errorStr = log.error_type ? `<span class="badge bg-danger">${log.error_type}</span>` : '';
                    
                    row.innerHTML = `
                        <td>${new Date(log.ts).toISOString().split('.')[0].replace('T', ' ')}</td>
                        <td><span class="badge bg-secondary">${log.event}</span></td>
                        <td class="${statusClass} fw-bold">${log.status.toUpperCase()}</td>
                        <td>${Math.round(log.duration_ms)}</td>
                        <td class="small text-muted">${errorStr} ${metaStr}</td>
                    `;
                    tbody.appendChild(row);
                });

                document.getElementById('last-updated').innerText = 'Last Updated: ' + new Date().toLocaleTimeString();

            } catch (e) {
                console.error("Failed to fetch stats:", e);
            }
        }

        // Initial Load & Interval
        updateDashboard();
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stats')
def get_stats():
    metrics = logger.get_metrics_summary()
    logs = logger.get_recent_events(limit=20)
    db_stats = logger.get_db_stats()
    return jsonify({
        "metrics": metrics,
        "logs": logs,
        "db_stats": db_stats
    })

if __name__ == "__main__":
    # Run on port 5000
    print("🚀 Monitor functionality running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
