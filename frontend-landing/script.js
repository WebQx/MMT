// MMT Landing Page JavaScript
class MMTLanding {
    constructor() {
        this.init();
    }

    init() {
        this.setupSmoothScrolling();
        this.setupAnimations();
        this.setupServiceStatusChecker();
        this.setupInteractiveElements();
    }

    setupSmoothScrolling() {
        // Smooth scrolling for navigation links
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
        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                    
                    // Add staggered animation for grid items
                    if (entry.target.parentElement.classList.contains('features-grid') ||
                        entry.target.parentElement.classList.contains('workflow-steps')) {
                        const delay = Array.from(entry.target.parentElement.children).indexOf(entry.target) * 100;
                        entry.target.style.animationDelay = `${delay}ms`;
                    }
                }
            });
        }, observerOptions);

        // Observe elements for animation
        document.querySelectorAll('.feature-card, .workflow-step, .stat-item').forEach(el => {
            observer.observe(el);
        });
    }

    setupServiceStatusChecker() {
        const services = [
            { 
                url: 'http://localhost:8080', 
                name: 'OpenEMR',
                selector: '[href="http://localhost:8080"]'
            },
            { 
                url: 'http://localhost:3000', 
                name: 'MMT App',
                selector: '[href="http://localhost:3000"]'
            },
            { 
                url: 'http://localhost:8001/api/health/', 
                name: 'Django API',
                selector: '[href="http://localhost:8001/api/"]'
            }
        ];

        // Create status indicator container
        this.createStatusIndicator();

        services.forEach(service => {
            this.checkServiceStatus(service);
        });

        // Check services periodically
        setInterval(() => {
            services.forEach(service => {
                this.checkServiceStatus(service);
            });
        }, 30000); // Check every 30 seconds
    }

    createStatusIndicator() {
        const statusContainer = document.createElement('div');
        statusContainer.id = 'service-status';
        statusContainer.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            font-size: 0.9rem;
            min-width: 200px;
            transition: all 0.3s ease;
            transform: translateX(100%);
        `;

        statusContainer.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 10px; color: #1f2937;">
                <i class="fas fa-heartbeat"></i> Service Status
            </div>
            <div id="status-list"></div>
            <div style="margin-top: 10px; font-size: 0.8rem; color: #6b7280;">
                Auto-refresh every 30s
            </div>
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

    async checkServiceStatus(service) {
        const statusList = document.getElementById('status-list');
        const existingStatus = document.getElementById(`status-${service.name.replace(/\s+/g, '-').toLowerCase()}`);
        
        try {
            const response = await fetch(service.url, { 
                method: 'HEAD',
                mode: 'no-cors',
                timeout: 5000 
            });
            
            this.updateServiceStatus(service, true, existingStatus, statusList);
        } catch (error) {
            this.updateServiceStatus(service, false, existingStatus, statusList);
        }
    }

    updateServiceStatus(service, isOnline, existingStatus, statusList) {
        const statusId = `status-${service.name.replace(/\s+/g, '-').toLowerCase()}`;
        const statusColor = isOnline ? '#10b981' : '#ef4444';
        const statusIcon = isOnline ? 'fas fa-check-circle' : 'fas fa-times-circle';
        const statusText = isOnline ? 'Online' : 'Offline';

        const statusHTML = `
            <div id="${statusId}" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px;">
                <span style="color: #374151;">${service.name}</span>
                <span style="color: ${statusColor};">
                    <i class="${statusIcon}"></i> ${statusText}
                </span>
            </div>
        `;

        if (existingStatus) {
            existingStatus.outerHTML = statusHTML;
        } else {
            statusList.innerHTML += statusHTML;
        }

        // Update link appearances based on service status
        const links = document.querySelectorAll(service.selector);
        links.forEach(link => {
            if (isOnline) {
                link.style.opacity = '1';
                link.style.pointerEvents = 'auto';
                link.removeAttribute('disabled');
            } else {
                link.style.opacity = '0.5';
                link.style.pointerEvents = 'none';
                link.setAttribute('disabled', 'true');
            }
        });
    }

    setupInteractiveElements() {
        // Add hover effects to cards
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-8px) scale(1.02)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
            });
        });

        // Add click tracking for analytics (if needed)
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const buttonText = button.textContent.trim();
                console.log(`Button clicked: ${buttonText}`);
                
                // You could send analytics data here
                // analytics.track('button_click', { button: buttonText });
            });
        });

        // Add tooltips for external links
        document.querySelectorAll('a[target="_blank"]').forEach(link => {
            link.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, 'Opens in new tab');
            });

            link.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });

        // Add loading states for buttons
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', () => {
                if (button.getAttribute('href').startsWith('http')) {
                    const originalHTML = button.innerHTML;
                    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                    button.style.pointerEvents = 'none';

                    setTimeout(() => {
                        button.innerHTML = originalHTML;
                        button.style.pointerEvents = 'auto';
                    }, 2000);
                }
            });
        });
    }

    showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.id = 'tooltip';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            position: absolute;
            background: #1f2937;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.8rem;
            z-index: 1001;
            pointer-events: none;
            white-space: nowrap;
        `;

        document.body.appendChild(tooltip);

        const rect = element.getBoundingClientRect();
        tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
        tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
    }

    hideTooltip() {
        const tooltip = document.getElementById('tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    // Utility method to show notifications
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            z-index: 1002;
            font-weight: 500;
            max-width: 300px;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Remove after 5 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    }
}

// Initialize the landing page functionality
document.addEventListener('DOMContentLoaded', () => {
    new MMTLanding();
});

// Add keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
            case '1':
                e.preventDefault();
                window.open('http://localhost:8080', '_blank');
                break;
            case '2':
                e.preventDefault();
                window.open('http://localhost:3000', '_blank');
                break;
            case '3':
                e.preventDefault();
                window.open('http://localhost:8001/api/', '_blank');
                break;
        }
    }
});

// Add console welcome message
console.log(`
🏥 MMT Platform - Medical Transcription with OpenEMR Integration
============================================================
Keyboard Shortcuts:
- Ctrl/Cmd + 1: Open OpenEMR
- Ctrl/Cmd + 2: Open MMT App  
- Ctrl/Cmd + 3: Open API Documentation

Services:
- Landing Page: http://localhost/
- OpenEMR: http://localhost:8080
- MMT App: http://localhost:3000
- Django API: http://localhost:8001/api/
- Admin Panel: http://localhost:8001/admin/

For support, check the documentation or service status indicator.
============================================================
`);