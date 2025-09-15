// MMT Landing Page JavaScript - Enhanced with Remote Backend Connectivity
class MMTLanding {
    constructor() {
        this.backendUrls = this.detectBackendUrls();
        this.connectionStatus = new Map();
        this.errorLog = [];
        this.init();
    }

    detectBackendUrls() {
        const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        const isGitHubPages = window.location.hostname === 'webqx.github.io';
        // Allow explicit override via global config or query string (api, backend, api_base)
        const params = new URLSearchParams(window.location.search);
        const override = (window.__MMT_CONFIG && window.__MMT_CONFIG.API_BASE_URL) || params.get('api') || params.get('backend') || params.get('api_base');
        
        if (isDevelopment) {
            return {
                django: override || 'http://localhost:8001',
                openemr: 'http://localhost:8080',
                flutter: 'http://localhost:3000',
                websocket: (override ? override.replace(/^http/, 'ws') : 'ws://localhost:8001')
            };
        } else if (isGitHubPages) {
            // For production deployment, these would be real URLs
            return {
                django: override || 'https://api.yourserver.com',  // Replace with actual production URLs or set via query/global
                openemr: 'https://openemr.yourserver.com',
                flutter: 'https://app.yourserver.com',
                websocket: (override ? override.replace(/^http/,'wss') : 'wss://api.yourserver.com')
            };
        } else {
            // Custom domain detection
            const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const baseUrl = `${protocol}//${window.location.hostname}`;
            const api = override || `${baseUrl}:8001`;
            
            return {
                django: api,
                openemr: `${baseUrl}:8080`,
                flutter: `${baseUrl}:3000`,
                websocket: api.replace(/^http/, wsProtocol)
            };
        }
    }

    init() {
        this.setupSmoothScrolling();
        this.setupAnimations();
        this.setupServiceStatusChecker();
        this.setupInteractiveElements();
        this.setupErrorLogging();
        this.initializeBackendConnections();
    }

    setupErrorLogging() {
        // Global error handler
        window.addEventListener('error', (event) => {
            this.logError('Global Error', event.error?.message || event.message, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            this.logError('Unhandled Promise Rejection', event.reason?.message || event.reason, {
                promise: event.promise
            });
        });
    }

    logError(type, message, details = {}) {
        const error = {
            timestamp: new Date().toISOString(),
            type,
            message,
            details,
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        this.errorLog.push(error);
        console.error(`[MMT Error] ${type}:`, message, details);
        
        // Keep only last 100 errors to prevent memory issues
        if (this.errorLog.length > 100) {
            this.errorLog.shift();
        }

        // Try to send error to backend if available
        this.sendErrorToBackend(error).catch(() => {
            // Silent fail - don't create recursive errors
        });
    }

    async sendErrorToBackend(error) {
        try {
            const response = await fetch(`${this.backendUrls.django}/api/errors/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(error)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (err) {
            // Store failed logs locally for later retry
            const failedLogs = JSON.parse(localStorage.getItem('mmt_failed_logs') || '[]');
            failedLogs.push(error);
            localStorage.setItem('mmt_failed_logs', JSON.stringify(failedLogs.slice(-50))); // Keep last 50
        }
    }

    async initializeBackendConnections() {
        // Check all backend services
        await this.checkAllServices();
        // Fetch demo/production status banner
        this.fetchDemoStatus();
        
        // Set up periodic health checks
        setInterval(() => {
            this.checkAllServices();
        }, 30000); // Every 30 seconds

        // Retry failed error logs
        this.retryFailedLogs();
    }

    async fetchDemoStatus() {
        try {
            const resp = await fetch(`${this.backendUrls.django}/demo/status`, { cache: 'no-store' });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            this.renderEnvBanner(data);
        } catch (e) {
            // If unreachable, show a subtle warning only once
            this.renderEnvBanner({ unreachable: true });
        }
    }

    renderEnvBanner(info) {
        let bar = document.getElementById('env-banner');
        if (!bar) {
            bar = document.createElement('div');
            bar.id = 'env-banner';
            bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:9999;padding:4px 10px;font-size:12px;font-family:system-ui,Arial,sans-serif;display:flex;align-items:center;gap:12px;color:#fff;';
            document.body.prepend(bar);
            // push main content if any
            document.documentElement.style.setProperty('--mmt-banner-height','24px');
        }
        let text = '';
        let bg = '#1f2937';
        if (info.unreachable) {
            text = 'Backend unreachable – using static landing only. Add ?api=https://your-api.example to test.';
            bg = '#b91c1c';
        } else if (info.demo_mode) {
            text = 'Demo Mode Active: transcripts stored locally only';
            bg = '#2563eb';
        } else {
            text = 'Production Backend Connected';
            bg = '#059669';
        }
        const apiDisp = this.backendUrls.django;
        const prodApi = (window.__MMT_CONFIG && window.__MMT_CONFIG.PRODUCTION_API_BASE_URL) || null;
        const showUpgrade = info.demo_mode && prodApi && prodApi !== apiDisp;
        bar.innerHTML = `<span style="font-weight:600;">${text}</span><span style="opacity:.8;">API: ${apiDisp}</span>`+
            `<button id="change-api-btn" style="margin-left:auto;background:#374151;color:#fff;border:0;padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px;">Change API</button>`+
            (showUpgrade ? `<button id="upgrade-to-prod-btn" style="background:#059669;color:#fff;border:0;padding:3px 10px;border-radius:4px;cursor:pointer;font-size:11px;">Connect to Production</button>` : '');
        bar.style.background = bg;
        const btn = document.getElementById('change-api-btn');
        if (btn) {
            btn.onclick = () => {
                const current = this.backendUrls.django;
                const entered = prompt('Enter new API base URL (e.g. https://api.example.com)', current);
                if (entered && /^https?:\/\//.test(entered)) {
                    const url = new URL(window.location.href);
                    url.searchParams.set('api', entered);
                    window.location.href = url.toString();
                }
            };
        }
        const upgradeBtn = document.getElementById('upgrade-to-prod-btn');
        if (upgradeBtn && prodApi) {
            upgradeBtn.onclick = () => {
                const url = new URL(window.location.href);
                url.searchParams.set('api', prodApi);
                window.location.href = url.toString();
            };
        }
    }

    async checkAllServices() {
        const services = [
            { name: 'Django API', url: `${this.backendUrls.django}/api/health/`, key: 'django' },
            { name: 'OpenEMR', url: `${this.backendUrls.openemr}/`, key: 'openemr' },
            { name: 'Flutter App', url: `${this.backendUrls.flutter}/`, key: 'flutter' }
        ];

        for (const service of services) {
            try {
                const status = await this.checkServiceHealth(service);
                this.connectionStatus.set(service.key, status);
                this.updateServiceStatusUI(service.key, status);
            } catch (error) {
                this.logError('Service Check Failed', `Failed to check ${service.name}`, {
                    service: service.name,
                    url: service.url,
                    error: error.message
                });
                this.connectionStatus.set(service.key, { status: 'error', error: error.message });
                this.updateServiceStatusUI(service.key, { status: 'error', error: error.message });
            }
        }
    }

    async checkServiceHealth(service) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

        try {
            const response = await fetch(service.url, {
                method: 'HEAD',
                mode: 'cors',
                signal: controller.signal,
                headers: {
                    'Cache-Control': 'no-cache'
                }
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                return {
                    status: 'online',
                    responseTime: performance.now(),
                    lastCheck: new Date().toISOString()
                };
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('Timeout');
            } else if (error.message.includes('CORS')) {
                // CORS error might mean service is running but not configured for frontend
                return {
                    status: 'cors_error',
                    error: 'CORS configuration needed',
                    lastCheck: new Date().toISOString()
                };
            } else {
                throw error;
            }
        }
    }

    updateServiceStatusUI(serviceKey, status) {
        const statusList = document.getElementById('status-list');
        if (!statusList) return;

        const existingItem = document.getElementById(`status-${serviceKey}`);
        const statusInfo = this.getStatusDisplayInfo(status);
        
        const statusHTML = `
            <div id="status-${serviceKey}" style="display: flex; align-items: center; margin-bottom: 8px; padding: 5px; border-radius: 5px; background: rgba(255,255,255,0.5);">
                <i class="${statusInfo.icon}" style="color: ${statusInfo.color}; margin-right: 8px; width: 16px;"></i>
                <div style="flex: 1;">
                    <div style="font-weight: 500; font-size: 0.85rem;">${statusInfo.name}</div>
                    <div style="font-size: 0.75rem; color: #6b7280;">${statusInfo.description}</div>
                </div>
                ${statusInfo.action ? `<button onclick="window.mmtLanding.${statusInfo.action}" style="font-size: 0.7rem; padding: 2px 6px; border: none; border-radius: 3px; background: #3b82f6; color: white; cursor: pointer;">Fix</button>` : ''}
            </div>
        `;

        if (existingItem) {
            existingItem.outerHTML = statusHTML;
        } else {
            statusList.insertAdjacentHTML('beforeend', statusHTML);
        }
    }

    getStatusDisplayInfo(status) {
        const serviceNames = {
            django: 'Django API',
            openemr: 'OpenEMR',
            flutter: 'Flutter App'
        };

        switch (status.status) {
            case 'online':
                return {
                    name: serviceNames[Object.keys(serviceNames).find(k => status.lastCheck)] || 'Service',
                    icon: 'fas fa-check-circle',
                    color: '#10b981',
                    description: 'Online and responding'
                };
            case 'cors_error':
                return {
                    name: serviceNames[Object.keys(serviceNames).find(k => status.lastCheck)] || 'Service',
                    icon: 'fas fa-exclamation-triangle',
                    color: '#f59e0b',
                    description: 'CORS configuration needed',
                    action: 'showCORSHelp()'
                };
            case 'error':
            default:
                return {
                    name: serviceNames[Object.keys(serviceNames).find(k => status.lastCheck)] || 'Service',
                    icon: 'fas fa-times-circle',
                    color: '#ef4444',
                    description: status.error || 'Offline or unreachable'
                };
        }
    }

    showCORSHelp() {
        this.showNotification(`
            CORS Configuration Needed
            
            To fix CORS errors:
            1. Add your frontend URL to CORS_ALLOW_ORIGINS
            2. For development: CORS_ALLOW_ORIGINS="http://localhost:3000,https://webqx.github.io"
            3. Restart your backend services
        `, 'info');
    }

    async retryFailedLogs() {
        try {
            const failedLogs = JSON.parse(localStorage.getItem('mmt_failed_logs') || '[]');
            if (failedLogs.length === 0) return;

            const retryPromises = failedLogs.map(log => this.sendErrorToBackend(log));
            await Promise.allSettled(retryPromises);
            
            // Clear successfully retried logs
            localStorage.removeItem('mmt_failed_logs');
        } catch (error) {
            this.logError('Log Retry Failed', error.message);
        }
    }

    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    setupAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                    
                    if (entry.target.parentElement.classList.contains('features-grid') ||
                        entry.target.parentElement.classList.contains('workflow-steps')) {
                        const delay = Array.from(entry.target.parentElement.children).indexOf(entry.target) * 100;
                        entry.target.style.animationDelay = `${delay}ms`;
                    }
                }
            });
        }, observerOptions);

        document.querySelectorAll('.feature-card, .workflow-step, .stat-card').forEach(el => {
            observer.observe(el);
        });

        const style = document.createElement('style');
        style.textContent = `
            .fade-in-up {
                animation: fadeInUp 0.6s ease-out forwards;
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }

    setupServiceStatusChecker() {
        this.createStatusIndicator();
        
        // Update every 30 seconds
        setInterval(() => {
            this.updateStatusTimestamp();
        }, 30000);
    }

    updateStatusTimestamp() {
        const statusList = document.getElementById('status-list');
        if (statusList) {
            const timeIndicator = statusList.querySelector('.time-indicator');
            const currentTime = new Date().toLocaleTimeString();
            
            if (!timeIndicator) {
                const timeDiv = document.createElement('div');
                timeDiv.className = 'time-indicator';
                timeDiv.style.cssText = 'font-size: 0.7rem; color: #9ca3af; text-align: center; margin-top: 5px; border-top: 1px solid #e5e7eb; padding-top: 5px;';
                timeDiv.innerHTML = `
                    <div>Last updated: ${currentTime}</div>
                    <div style="margin-top: 2px;">
                        <button onclick="window.mmtLanding.downloadErrorLog()" style="font-size: 0.6rem; padding: 1px 4px; border: none; border-radius: 2px; background: #6b7280; color: white; cursor: pointer; margin-right: 5px;">Download Logs</button>
                        <button onclick="window.mmtLanding.clearErrorLog()" style="font-size: 0.6rem; padding: 1px 4px; border: none; border-radius: 2px; background: #ef4444; color: white; cursor: pointer;">Clear Logs</button>
                    </div>
                `;
                statusList.appendChild(timeDiv);
            } else {
                timeIndicator.querySelector('div').textContent = `Last updated: ${currentTime}`;
            }
        }
    }

    downloadErrorLog() {
        const logData = {
            timestamp: new Date().toISOString(),
            errors: this.errorLog,
            connectionStatus: Object.fromEntries(this.connectionStatus),
            backendUrls: this.backendUrls,
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        const blob = new Blob([JSON.stringify(logData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mmt-error-log-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showNotification('Error log downloaded successfully', 'success');
    }

    clearErrorLog() {
        this.errorLog = [];
        localStorage.removeItem('mmt_failed_logs');
        this.showNotification('Error log cleared', 'success');
    }

    createStatusIndicator() {
        const statusContainer = document.createElement('div');
        statusContainer.id = 'service-status';
        statusContainer.style.cssText = `
            position: fixed;
            top: 50%;
            right: 0;
            transform: translateY(-50%);
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            font-size: 0.9rem;
            min-width: 250px;
            max-width: 300px;
            transition: all 0.3s ease;
            transform: translateX(100%);
        `;

        statusContainer.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 10px; color: #1f2937;">
                <i class="fas fa-heartbeat"></i> Service Status
            </div>
            <div id="status-list"></div>
        `;

        document.body.appendChild(statusContainer);

        // Show status indicator after page load
        setTimeout(() => {
            statusContainer.style.transform = 'translateX(0)';
        }, 2000);

        // Hide after 10 seconds, show on hover
        setTimeout(() => {
            statusContainer.style.transform = 'translateX(calc(100% - 30px))';
        }, 10000);

        statusContainer.addEventListener('mouseenter', () => {
            statusContainer.style.transform = 'translateX(0)';
        });

        statusContainer.addEventListener('mouseleave', () => {
            statusContainer.style.transform = 'translateX(calc(100% - 30px))';
        });
    }

    setupInteractiveElements() {
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-8px) scale(1.02)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
            });
        });

        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const buttonText = button.textContent.trim();
                console.log(`Button clicked: ${buttonText}`);
                
                // Handle service access for localhost links
                if (button.href && button.href.includes('localhost')) {
                    e.preventDefault();
                    this.handleServiceAccess(button.href, buttonText);
                }
                
                // Log interaction for analytics
                this.logInteraction('button_click', {
                    text: buttonText,
                    href: button.href,
                    timestamp: new Date().toISOString()
                });
            });
        });
    }

    handleServiceAccess(url, serviceName) {
        // Extract service type from URL
        let serviceType = 'unknown';
        if (url.includes(':8080')) serviceType = 'openemr';
        else if (url.includes(':3000')) serviceType = 'flutter';
        else if (url.includes(':8001')) serviceType = 'django';

        this.accessService(serviceType, serviceName);
    }

    accessService(serviceType, serviceName = '') {
        const service = this.connectionStatus.get(serviceType);
        const url = this.backendUrls[serviceType];

        if (!url) {
            this.showNotification(`Service ${serviceType} not configured`, 'error');
            return;
        }

        if (service && service.status === 'online') {
            // Service is confirmed online, open it
            window.open(url, '_blank');
            this.logInteraction('service_access', {
                serviceType,
                serviceName,
                url,
                status: 'success'
            });
        } else if (service && service.status === 'cors_error') {
            // Service is running but has CORS issues
            const proceed = confirm(`${serviceName || serviceType} is running but may have CORS configuration issues.\n\nWould you like to try opening it anyway?`);
            if (proceed) {
                window.open(url, '_blank');
                this.logInteraction('service_access', {
                    serviceType,
                    serviceName,
                    url,
                    status: 'cors_warning_ignored'
                });
            }
        } else {
            // Service appears offline
            const isDev = window.location.hostname === 'localhost';
            const message = isDev ? 
                `${serviceName || serviceType} appears to be offline.\n\nMake sure you've started it with:\ndocker-compose up ${serviceType}\n\nWould you like to try opening it anyway?` :
                `${serviceName || serviceType} is not available in demo mode.\n\nTo access this service:\n1. Clone the repository\n2. Run: docker-compose up\n3. Access services locally\n\nWould you like to view the setup guide?`;
            
            const proceed = confirm(message);
            if (proceed) {
                if (isDev) {
                    window.open(url, '_blank');
                } else {
                    window.open('https://github.com/WebQx/MMT#setup', '_blank');
                }
                this.logInteraction('service_access', {
                    serviceType,
                    serviceName,
                    url,
                    status: 'offline_attempt'
                });
            }
        }
    }

    logInteraction(type, data) {
        // Store user interactions for analytics
        const interactions = JSON.parse(localStorage.getItem('mmt_interactions') || '[]');
        interactions.push({ type, data, timestamp: new Date().toISOString() });
        localStorage.setItem('mmt_interactions', JSON.stringify(interactions.slice(-100))); // Keep last 100
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            z-index: 10000;
            font-size: 0.9rem;
            max-width: 400px;
            word-wrap: break-word;
            white-space: pre-line;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;

        notification.innerHTML = `
            <div style="display: flex; align-items: flex-start;">
                <i class="fas ${type === 'success' ? 'fa-check' : type === 'error' ? 'fa-times' : 'fa-info'}" style="margin-right: 10px; margin-top: 2px;"></i>
                <div style="flex: 1;">${message}</div>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; cursor: pointer; margin-left: 10px; font-size: 1.1rem;">&times;</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Slide in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Remove after 8 seconds
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 8000);
    }
}

// Initialize the landing page functionality
document.addEventListener('DOMContentLoaded', () => {
    window.mmtLanding = new MMTLanding();
});

// Keyboard shortcuts with enhanced functionality
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
            case '1':
                e.preventDefault();
                showOpenEMRInfo();
                break;
            case '2':
                e.preventDefault();
                showMMTInfo();
                break;
            case '3':
                e.preventDefault();
                window.open('https://github.com/WebQx/MMT', '_blank');
                break;
            case 'd':
                e.preventDefault();
                if (window.mmtLanding) {
                    window.mmtLanding.downloadErrorLog();
                }
                break;
            case 'r':
                e.preventDefault();
                if (window.mmtLanding) {
                    window.mmtLanding.checkAllServices();
                    window.mmtLanding.showNotification('Services refreshed', 'success');
                }
                break;
        }
    }
});

// Enhanced demo and info functions
function showDemo() {
    const isDev = window.location.hostname === 'localhost';
    const message = isDev ? 
        '🎬 Local Development Mode\n\nYou\'re running the development version!\n\nServices should be available at:\n• OpenEMR: http://localhost:8080\n• Django API: http://localhost:8001\n• Flutter App: http://localhost:3000\n\nUse docker-compose up to start all services.' :
        '🎬 Demo Mode\n\nThis is a demonstration of the MMT-OpenEMR integration platform.\n\nTo run the full stack locally:\n1. Clone the repository\n2. Run: docker-compose up\n3. Access services on localhost ports\n\nFor more details, visit the GitHub repository.';
    alert(message);
}

function showOpenEMRInfo() {
    alert('🏥 OpenEMR Integration\n\nOpenEMR is an open-source electronic health records system that serves as the backbone for patient data management.\n\nIn this integration:\n• Stores patient records\n• Manages encounters\n• Acts as authentication provider\n• Serves as filing cabinet for transcriptions\n\nTo deploy locally, use Docker Compose setup.');
}

function showMMTInfo() {
    alert('🎤 MMT Application\n\nMedical Transcription Tool (MMT) is a Flutter-based mobile/web app for real-time medical transcription.\n\nFeatures:\n• Voice-to-text using Whisper AI\n• Real-time transcription\n• Integration with OpenEMR\n• Mobile and web support\n\nRun locally with: flutter run -d web-server --web-port=3000');
}

// Enhanced console welcome message
console.log(`
🏥 MMT Platform - Medical Transcription with OpenEMR Integration
============================================================
Enhanced Frontend with Remote Backend Connectivity

Environment: ${window.location.hostname === 'localhost' ? 'Development' : 'Production'}
Backend URLs: ${JSON.stringify(window.mmtLanding?.backendUrls, null, 2)}

Features:
• Automatic backend service discovery
• Real-time connection monitoring
• Comprehensive error logging
• CORS error detection and guidance
• Network failure handling

Keyboard Shortcuts:
- Ctrl/Cmd + 1: OpenEMR Info
- Ctrl/Cmd + 2: MMT App Info
- Ctrl/Cmd + 3: GitHub Repository
- Ctrl/Cmd + D: Download Error Logs
- Ctrl/Cmd + R: Refresh Service Status

For deployment and troubleshooting, check the service status panel.
============================================================
`);