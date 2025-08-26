# MMT - Multilingual Medical Transcription

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/WebQx/MMT.git
cd MMT
```

2. Create environment file:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys and configuration
```

3. Start all services:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- RabbitMQ Management: http://localhost:15672

### Manual Setup

#### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the backend:
```bash
uvicorn main:app --reload
```

4. Start OpenEMR consumer:
```bash
python openemr_consumer.py
```

#### Frontend Setup

1. Install Flutter and dependencies:
```bash
cd app
flutter pub get
```

2. Run the Flutter web app:
```bash
flutter run -d web-server --web-hostname 0.0.0.0 --web-port 3000
```

### Production Deployment

#### GitHub Pages (Frontend Only)

1. Build the Flutter web app:
```bash
cd app
flutter build web --base-href /MMT/
```

2. Deploy to GitHub Pages (automated via GitHub Actions)

#### Full Stack Deployment

Use the provided Docker configuration for production deployment with proper environment variables and secrets management.

## Configuration

### Environment Variables

See `backend/.env.example` for all required configuration options:

- `OPENAI_API_KEY`: Your OpenAI API key for cloud transcription
- `KEYCLOAK_*`: Keycloak configuration for OAuth2 authentication
- `OPENEMR_*`: OpenEMR integration settings
- `RABBITMQ_URL`: RabbitMQ connection string
- `FRONTEND_DOMAIN`: Allowed frontend domain for CORS

### API Endpoints

- `GET /`: Health check
- `POST /login/oauth2`: Keycloak OAuth2 login
- `POST /login/guest`: Guest login
- `POST /transcribe/`: Local Whisper transcription
- `POST /transcribe/cloud/`: OpenAI Whisper transcription
- `POST /upload_chunk/`: Chunked file upload
- `GET /network_advice/`: Network optimization advice
- `GET /health`: Detailed health check

## Features

- ✅ **Multi-platform**: Web, mobile, and desktop support via Flutter
- ✅ **Multilingual**: Support for 10+ languages with auto-detection
- ✅ **Dual transcription**: Local Whisper and OpenAI Whisper API
- ✅ **Authentication**: OAuth2 (Keycloak) and guest login
- ✅ **EHR Integration**: OpenEMR integration via RabbitMQ
- ✅ **Security**: GDPR, HIPAA, ISO 27701 ready
- ✅ **Real-time**: Live transcription and ambient mode
- ✅ **Offline**: Local Whisper for offline transcription
- ✅ **Cloud**: OpenAI Whisper for cloud transcription
- ✅ **Chunked Upload**: Support for large audio files
- ✅ **Export**: Print, email, and share functionality

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

For support, email Info@WebQx.Healthcare or visit the [GitHub repository](https://github.com/WebQx/MMT).