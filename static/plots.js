/**
 * Progress Analytics & Charting System
 * Displays user learning progress with interactive charts and metrics
 * Integrates with tracker.py backend for session-based analytics
 */

class ProgressAnalytics {
    constructor() {
        this.charts = {};
        this.progressData = null;
        this.currentUserId = null;
        this.init();
    }

    init() {
        // Initialize event listeners
        const refreshBtn = document.getElementById('refreshProgressBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadAndRender());
        }

        // Listen for user changes
        const userIdInput = document.getElementById('user_id');
        if (userIdInput) {
            userIdInput.addEventListener('change', () => {
                const userId = userIdInput.value.trim();
                if (userId) {
                    this.currentUserId = userId;
                    this.loadAndRender();
                }
            });
        }
    }

    async loadAndRender() {
        if (!this.currentUserId) {
            this.showMessage('Please enter a user ID first', 'warning');
            return;
        }

        try {
            this.showMessage('Loading analytics...', 'info');
            this.progressData = await this.fetchProgressData(this.currentUserId);

            if (this.progressData.ok) {
                // Always render dashboard - it will show empty state if no sessions
                this.renderDashboard();

                if (!this.progressData.sessions || this.progressData.sessions.length === 0) {
                    this.showMessage('No practice sessions yet. Start chatting to see your performance charts!', 'info');
                } else {
                    this.showMessage('Analytics loaded successfully', 'success');
                }
            } else {
                this.showMessage('No data available yet. Start practicing to see your progress!', 'info');
            }
        } catch (err) {
            console.error('Error loading progress:', err);
            this.showMessage('Could not load analytics. Make sure you have practice sessions!', 'error');
        }
    }

    async fetchProgressData(userId) {
        const response = await fetch(`/api/scenario/progress/${userId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch progress: ${response.status}`);
        }
        return await response.json();
    }

    renderDashboard() {
        const data = this.progressData;

        if (!data.progress) {
            return;
        }

        // Update summary stats
        this.updateSummaryStats(data.progress);

        // Render charts if we have session data
        if (data.sessions && data.sessions.length > 0) {
            this.renderScoreTrendChart(data.sessions);
            this.renderGrammarFluencyChart(data.sessions);
            this.renderSessionDistributionChart(data.sessions);
            this.renderPerformanceLevelsChart(data.sessions);
        } else {
            // Show message when no sessions yet
            this.showNoDataMessage();
        }

        // Render text-based analytics
        this.renderWeeklySummary(data.weekly_summary);
        this.renderErrorPatterns(data.error_patterns);
        this.renderMilestones(data.progress);
    }

    showNoDataMessage() {
        // Hide all charts and show message
        const charts = ['scoreChart', 'grammarFluencyChart', 'sessionChart', 'performanceChart'];
        charts.forEach(id => {
            const canvas = document.getElementById(id);
            if (canvas) {
                canvas.parentElement.innerHTML = '<p style="color: #666; font-size: 12px; padding: 20px; text-align: center;">Start a conversation to see your performance charts</p>';
            }
        });
    }

    updateSummaryStats(progress) {
        document.getElementById('current_user').textContent = progress.user_id || 'Unknown';
        document.getElementById('total_sessions').textContent = progress.total_sessions || 0;
        document.getElementById('total_time').textContent = `${Math.round(progress.total_practice_minutes || 0)} min`;
        document.getElementById('current_streak').textContent = `${progress.current_streak || 0} days`;
    }

    renderScoreTrendChart(sessions) {
        const ctx = document.getElementById('scoreChart');
        if (!ctx) {
            console.warn('scoreChart canvas element not found');
            return;
        }

        console.log('Rendering score trend chart with', sessions.length, 'sessions');

        // Extract data
        const dates = [];
        const scores = [];

        sessions.forEach(session => {
            if (session.assessments) {
                session.assessments.forEach(assessment => {
                    const timestamp = new Date(assessment.timestamp);
                    dates.push(timestamp.toLocaleDateString());
                    scores.push(assessment.overall_score?.overall_score || 0);
                });
            }
        });

        console.log('Extracted', scores.length, 'scores from assessments');

        // Destroy existing chart
        if (this.charts.scoreChart) {
            this.charts.scoreChart.destroy();
        }

        this.charts.scoreChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Overall Score',
                    data: scores,
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.15)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointBackgroundColor: '#00d4ff',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        labels: { font: { size: 11 }, color: '#e0e0e0' }
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        ticks: { font: { size: 10 }, color: '#b0b0b0' },
                        grid: { color: 'rgba(200, 200, 200, 0.1)' }
                    },
                    x: {
                        ticks: { font: { size: 9 }, color: '#b0b0b0' },
                        grid: { color: 'rgba(200, 200, 200, 0.05)' }
                    }
                }
            }
        });
    }

    renderGrammarFluencyChart(sessions) {
        const ctx = document.getElementById('grammarFluencyChart');
        if (!ctx) return;

        const dates = [];
        const grammarScores = [];
        const fluencyScores = [];

        sessions.forEach(session => {
            if (session.assessments) {
                session.assessments.forEach(assessment => {
                    const timestamp = new Date(assessment.timestamp);
                    dates.push(timestamp.toLocaleDateString());
                    grammarScores.push(assessment.language_analysis?.grammar_score || 0);
                    fluencyScores.push(assessment.language_analysis?.fluency_score || 0);
                });
            }
        });

        if (this.charts.grammarFluencyChart) {
            this.charts.grammarFluencyChart.destroy();
        }

        this.charts.grammarFluencyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Grammar Score',
                        data: grammarScores,
                        borderColor: '#1eff00',
                        backgroundColor: 'rgba(30, 255, 0, 0.1)',
                        tension: 0.3,
                        fill: false,
                        pointRadius: 3,
                        pointBackgroundColor: '#1eff00',
                        borderWidth: 2
                    },
                    {
                        label: 'Fluency Score',
                        data: fluencyScores,
                        borderColor: '#ff6b9d',
                        backgroundColor: 'rgba(255, 107, 157, 0.1)',
                        tension: 0.3,
                        fill: false,
                        pointRadius: 3,
                        pointBackgroundColor: '#ff6b9d',
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        labels: { font: { size: 11 }, color: '#e0e0e0' }
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        ticks: { font: { size: 10 }, color: '#b0b0b0' },
                        grid: { color: 'rgba(200, 200, 200, 0.1)' }
                    },
                    x: {
                        ticks: { font: { size: 9 }, color: '#b0b0b0' },
                        grid: { color: 'rgba(200, 200, 200, 0.05)' }
                    }
                }
            }
        });
    }

    renderSessionDistributionChart(sessions) {
        const ctx = document.getElementById('sessionChart');
        if (!ctx) return;

        const sessionLabels = [];
        const messageCounts = [];

        sessions.forEach((session, idx) => {
            sessionLabels.push(`Session ${idx + 1}`);
            messageCounts.push(session.assessments?.length || 0);
        });

        if (this.charts.sessionChart) {
            this.charts.sessionChart.destroy();
        }

        this.charts.sessionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sessionLabels,
                datasets: [{
                    label: 'Messages',
                    data: messageCounts,
                    backgroundColor: '#ffd700',
                    borderColor: '#fff',
                    borderWidth: 1,
                    borderRadius: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false, labels: { color: '#e0e0e0' } }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { font: { size: 10 }, color: '#b0b0b0' },
                        grid: { color: 'rgba(200, 200, 200, 0.1)' }
                    },
                    y: {
                        ticks: { font: { size: 9 }, color: '#b0b0b0' },
                        grid: { color: 'rgba(200, 200, 200, 0.05)' }
                    }
                }
            }
        });
    }

    renderPerformanceLevelsChart(sessions) {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        const levels = {};

        sessions.forEach(session => {
            if (session.assessments) {
                session.assessments.forEach(assessment => {
                    const level = assessment.overall_score?.performance_level || 'Unknown';
                    levels[level] = (levels[level] || 0) + 1;
                });
            }
        });

        const labels = Object.keys(levels);
        const data = Object.values(levels);
        const colors = ['#1eff00', '#00d4ff', '#ffd700', '#ff9500', '#ff6b9d'];

        if (this.charts.performanceChart) {
            this.charts.performanceChart.destroy();
        }

        this.charts.performanceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderColor: '#2a2a2a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { font: { size: 11 }, color: '#e0e0e0' }
                    }
                }
            }
        });
    }

    renderWeeklySummary(weeklySummary) {
        const container = document.getElementById('weeklySummary');
        if (!container) return;

        if (!weeklySummary || Object.keys(weeklySummary).length === 0) {
            container.innerHTML = '<p>No weekly data available</p>';
            return;
        }

        const html = `
            <div style="background: #f5f5f5; padding: 10px; border-radius: 3px;">
                <p><strong>Sessions (7 days):</strong> ${weeklySummary.sessions || 0}</p>
                <p><strong>Total Messages:</strong> ${weeklySummary.total_messages || 0}</p>
                <p><strong>Practice Time:</strong> ${Math.round(weeklySummary.total_minutes || 0)} min</p>
                <p><strong>Average Score:</strong> ${(weeklySummary.avg_score || 0).toFixed(1)}/100</p>
                <p><strong>Improvement Rate:</strong> ${weeklySummary.improvement_rate >= 0 ? '+' : ''}${(weeklySummary.improvement_rate || 0).toFixed(1)} points</p>
            </div>
        `;
        container.innerHTML = html;
    }

    renderErrorPatterns(errorPatterns) {
        const container = document.getElementById('errorPatterns');
        if (!container) return;

        if (!errorPatterns || Object.keys(errorPatterns).length === 0) {
            container.innerHTML = '<p>No error patterns detected yet</p>';
            return;
        }

        const categories = errorPatterns.categories || {};
        const examples = errorPatterns.examples || {};
        const mostCommon = errorPatterns.most_common || 'none';

        let html = `
            <div style="background: #fff3cd; padding: 10px; border-radius: 3px; margin-bottom: 10px;">
                <p><strong>Most Common Error:</strong> ${this.capitalizeFirst(mostCommon)}</p>
                <p><strong>Error Breakdown:</strong></p>
                <ul style="margin: 5px 0; padding-left: 20px;">
        `;

        Object.entries(categories).forEach(([category, count]) => {
            html += `<li>${this.capitalizeFirst(category)}: ${count} occurrences</li>`;
        });

        html += '</ul></div>';

        if (Object.keys(examples).length > 0) {
            html += '<p><strong>Example Errors:</strong></p>';
            Object.entries(examples).forEach(([category, errorList]) => {
                if (errorList.length > 0) {
                    html += `<p style="margin: 5px 0;"><em>${this.capitalizeFirst(category)}:</em> ${errorList[0]}</p>`;
                }
            });
        }

        container.innerHTML = html;
    }

    renderMilestones(progress) {
        const container = document.getElementById('milestones');
        if (!container) return;

        const milestones = progress.milestones || [];

        if (milestones.length === 0) {
            container.innerHTML = '<p>No milestones achieved yet. Keep practicing!</p>';
            return;
        }

        let html = '<div>';
        milestones.forEach(milestone => {
            html += `
                <div style="background: #e8f5e9; padding: 8px; margin: 5px 0; border-left: 3px solid #4caf50; border-radius: 2px;">
                    <p style="margin: 0;"><strong>${milestone.message}</strong></p>
                    <p style="margin: 3px 0; font-size: 11px; color: #666;">Achieved at ${new Date(milestone.achieved_at).toLocaleDateString()}</p>
                </div>
            `;
        });
        html += '</div>';

        container.innerHTML = html;
    }

    showMessage(message, type = 'info') {
        // Create temporary message element
        const messageEl = document.createElement('div');
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${this.getMessageColor(type)};
            color: white;
            border-radius: 4px;
            font-size: 12px;
            z-index: 10000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        `;
        messageEl.textContent = message;
        document.body.appendChild(messageEl);

        setTimeout(() => messageEl.remove(), 3000);
    }

    getMessageColor(type) {
        const colors = {
            'success': '#4caf50',
            'error': '#f44336',
            'warning': '#ff9800',
            'info': '#2196f3'
        };
        return colors[type] || colors.info;
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.progressAnalytics = new ProgressAnalytics();
});
