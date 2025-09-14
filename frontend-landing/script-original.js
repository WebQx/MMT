// MMT Landing Page JavaScript - GitHub Pages Optimized
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
        this.showDemoStatus();
        
        setInterval(() => {
            this.updateDemoStatus();
        }, 30000);
    }

    showDemoStatus() {
        const services = [
            { name: 'Landing Page', status: 'online', description: 'GitHub Pages (Active)' },
            { name: 'Full Stack', status: 'demo', description: 'Deploy locally to activate' },
            { name: 'Documentation', status: 'online', description: 'Available on GitHub' }
        ];

        const statusList = document.getElementById('status-list');
        if (!statusList) return;

        statusList.innerHTML = services.map(service => {
            const statusColor = service.status === 'online' ? '#10b981' : 
                              service.status === 'demo' ? '#f59e0b' : '#ef4444';
            const statusIcon = service.status === 'online' ? 'fas fa-check-circle' : 
                             service.status === 'demo' ? 'fas fa-info-circle' : 'fas fa-times-circle';
            
            return `
                <div style="display: flex; align-items: center; margin-bottom: 8px; padding: 5px; border-radius: 5px; background: rgba(255,255,255,0.5);">
                    <i class="${statusIcon}" style="color: ${statusColor}; margin-right: 8px; width: 16px;"></i>
                    <div style="flex: 1;">
                        <div style="font-weight: 500; font-size: 0.85rem;">${service.name}</div>
                        <div style="font-size: 0.75rem; color: #6b7280;">${service.description}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    updateDemoStatus() {
        const currentTime = new Date().toLocaleTimeString();
        const statusList = document.getElementById('status-list');
        if (statusList) {
            const timeIndicator = statusList.querySelector('.time-indicator');
            if (!timeIndicator) {
                const timeDiv = document.createElement('div');
                timeDiv.className = 'time-indicator';
                timeDiv.style.cssText = 'font-size: 0.7rem; color: #9ca3af; text-align: center; margin-top: 5px;';
                timeDiv.textContent = `Last updated: ${currentTime}`;
                statusList.appendChild(timeDiv);
            } else {
                timeIndicator.textContent = `Last updated: ${currentTime}`;
            }
        }
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

        setTimeout(() => {
            statusContainer.style.transform = 'translateX(0)';
        }, 2000);

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
            });
        });
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
        }
    }
});

// Demo and Info Functions for GitHub Pages
function showDemo() {
    alert('🎬 Demo Mode\n\nThis is a demonstration of the MMT-OpenEMR integration platform.\n\nTo run the full stack locally:\n1. Clone the repository\n2. Run: docker-compose up\n3. Access services on localhost ports\n\nFor more details, visit the GitHub repository.');
}

function showOpenEMRInfo() {
    alert('🏥 OpenEMR Integration\n\nOpenEMR is an open-source electronic health records system that serves as the backbone for patient data management.\n\nIn this integration:\n• Stores patient records\n• Manages encounters\n• Acts as authentication provider\n• Serves as filing cabinet for transcriptions\n\nTo deploy locally, use Docker Compose setup.');
}

function showMMTInfo() {
    alert('�� MMT Application\n\nMedical Transcription Tool (MMT) is a Flutter-based mobile/web app for real-time medical transcription.\n\nFeatures:\n• Voice-to-text using Whisper AI\n• Real-time transcription\n• Integration with OpenEMR\n• Mobile and web support\n\nRun locally with: flutter run -d web-server --web-port=3000');
}

// Add console welcome message
console.log(`
🏥 MMT Platform - Medical Transcription with OpenEMR Integration
============================================================
GitHub Pages Demo Version

This is a demonstration landing page. To run the full stack:
1. Clone: git clone https://github.com/WebQx/MMT.git
2. Deploy: docker-compose up
3. Access: http://localhost (this page)

Full Services (when running locally):
- OpenEMR: http://localhost:8080
- MMT App: http://localhost:3000  
- Django API: http://localhost:8001/api/
- Admin Panel: http://localhost:8001/admin/

Keyboard Shortcuts:
- Ctrl/Cmd + 1: OpenEMR Info
- Ctrl/Cmd + 2: MMT App Info
- Ctrl/Cmd + 3: GitHub Repository

For deployment and setup, check the GitHub repository.
============================================================
`);
