# MMT Frontend Landing Page

A modern, responsive landing page that serves as the central hub for the MMT (Medical Transcription Tool) platform integrated with OpenEMR.

## Features

### 🎨 Modern Design
- Clean, professional healthcare-focused design
- Responsive layout that works on all devices
- Smooth animations and transitions
- Interactive elements with hover effects

### 🔗 Service Integration
- Real-time service status monitoring
- Direct links to all platform components
- Proxy configuration for seamless navigation
- Health checks for all services

### 📱 Interactive Elements
- Service status indicator with auto-refresh
- Smooth scrolling navigation
- Keyboard shortcuts for quick access
- Loading states and visual feedback

### 🚀 Performance
- Lightweight nginx-based serving
- Optimized assets and caching
- Gzip compression enabled
- Fast loading times

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   Django API    │    │     OpenEMR     │
│  Landing Page   │◄──►│                 │◄──►│                 │
│   (Port 80)     │    │   (Port 8001)   │    │   (Port 8080)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Flutter App   │
│   (Port 3000)   │
└─────────────────┘
```

## Quick Start

The landing page is automatically included when you start the MMT platform:

```bash
# Start all services including the landing page
./start_integration.sh

# Access the landing page
open http://localhost
```

## Service Links

The landing page provides direct access to:

- **OpenEMR Portal**: http://localhost:8080
  - Patient management
  - Medical records
  - Clinical workflows

- **MMT Transcription App**: http://localhost:3000
  - Audio recording and transcription
  - Real-time Whisper AI processing
  - Encounter documentation

- **Django API**: http://localhost:8001/api/
  - RESTful endpoints
  - Authentication management
  - Data integration

- **Admin Dashboard**: http://localhost:8001/admin/
  - User management
  - System configuration
  - Database administration

## Key Sections

### Hero Section
- Platform overview and value proposition
- Quick access buttons to main services
- Professional medical branding

### Features Overview
- AI-Powered Transcription with Whisper
- OpenEMR Integration capabilities
- Patient Management tools
- Digital Filing Cabinet
- Advanced Search functionality
- HIPAA Compliance features

### Workflow Guide
Simple 4-step process:
1. **Patient Check-in** - Search/add patients in OpenEMR
2. **Record & Transcribe** - Use MMT app for audio capture
3. **Review & Edit** - Verify transcription accuracy
4. **File & Store** - Automatically integrate with OpenEMR

### Service Status
- Real-time monitoring of all platform components
- Visual indicators for service availability
- Auto-refresh every 30 seconds
- Hover to expand status details

## Keyboard Shortcuts

- `Ctrl/Cmd + 1`: Open OpenEMR
- `Ctrl/Cmd + 2`: Open MMT App
- `Ctrl/Cmd + 3`: Open API Documentation

## Technical Details

### Nginx Configuration
- Reverse proxy to Django API and OpenEMR
- CORS handling for cross-origin requests
- Security headers implementation
- Gzip compression for performance

### Service Health Monitoring
```javascript
// Automatic service status checking
const services = [
    { url: 'http://localhost:8080', name: 'OpenEMR' },
    { url: 'http://localhost:3000', name: 'MMT App' },
    { url: 'http://localhost:8001/api/health/', name: 'Django API' }
];
```

### Responsive Design
- Mobile-first approach
- Breakpoints at 768px for tablet/mobile
- Flexible grid layouts
- Scalable typography

## Customization

### Styling
All CSS is contained in the HTML file for simplicity. Key variables:

```css
:root {
    --primary-color: #2563eb;
    --secondary-color: #06b6d4;
    --accent-color: #10b981;
    --text-dark: #1f2937;
    --text-light: #6b7280;
}
```

### Content Updates
Edit `frontend-landing/index.html` to:
- Update service URLs
- Modify feature descriptions
- Change branding elements
- Add new sections

### JavaScript Functionality
Edit `frontend-landing/script.js` to:
- Add new interactive features
- Modify service monitoring
- Implement analytics tracking
- Customize animations

## Development

### Local Development
```bash
# Serve locally for development
cd frontend-landing
python -m http.server 8080

# Or use nginx directly
nginx -p . -c nginx.conf
```

### Building
```bash
# Build Docker image
docker build -t mmt-frontend-landing ./frontend-landing

# Run standalone
docker run -p 80:80 mmt-frontend-landing
```

## Production Considerations

### Performance
- Enable gzip compression (✓ included)
- Optimize images and assets
- Use CDN for external resources
- Implement caching strategies

### Security
- HTTPS termination at load balancer
- Security headers (✓ included)
- Content Security Policy
- Regular security audits

### Monitoring
- Access log analysis
- Error tracking and alerts
- Performance monitoring
- User analytics

## Contributing

To update the landing page:

1. Edit files in `frontend-landing/`
2. Test changes locally
3. Rebuild Docker image
4. Update docker-compose.yml if needed
5. Deploy and test integration

## Browser Support

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Modern browser features used:
- CSS Grid and Flexbox
- Intersection Observer API
- Fetch API
- CSS Custom Properties

## License

Same license as the main MMT project.