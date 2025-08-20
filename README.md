# Multilingual Medical Transcription (MMT) - End-to-End Blueprint

## Overview
MMT is a secure, multilingual, healthcare-grade transcription platform supporting real-time, ambient, and offline transcription. It integrates with OpenAI Whisper (cloud), local Whisper, OpenEMR, and supports OAuth2 (Keycloak) and guest login. The app is deployable as a Flutter web app (e.g., GitHub Pages) and as a mobile/desktop app.

---

## Architecture

**Frontend:** Flutter (Web, Mobile, Desktop)
- Multilingual UI (Flutter intl)
- OAuth2 (Keycloak) & Guest login
- Audio recording, file picker, ambient mode
- Print/email/share results

**Backend:** FastAPI (Python)
- REST API for transcription, login, health, etc.
- Local Whisper for "transcribe later"
- OpenAI Whisper API for real-time/ambient
- RabbitMQ for async integration with OpenEMR
- .env for secrets (OpenAI, Keycloak, OpenEMR, RabbitMQ)

**EHR Integration:**
- OpenEMR via REST API (RabbitMQ consumer)

**Security & Compliance:**
- GDPR, HIPAA, ISO 27701 ready
- OAuth2 (Keycloak), HTTPS, audit logging, data minimization

---

## User Flows

### 1. Login
- User chooses: Login with Keycloak (OAuth2) or Continue as Guest
- On success, receives access token (JWT or guest secret)

### 2. Main UI
- Select transcription type:
	- Realtime Transcription (OpenAI Whisper API)
	- Record Now, Transcribe Later (local Whisper)
- Select network mode: Cellular, WiFi, Cloud
- Optionally enable Ambient Mode (continuous listening, OpenAI Whisper API)

### 3. Transcription
- Upload/record audio or enable ambient mode
- For real-time/ambient/cloud: `/transcribe/cloud/` (OpenAI Whisper API)
- For transcribe later: `/transcribe/` (local Whisper)
- Results shown in app, can be printed/emailed
- All results sent to RabbitMQ for OpenEMR integration

### 4. EHR Integration
- RabbitMQ consumer posts transcriptions to OpenEMR API

---

## Security & Compliance
- All secrets in `/backend/.env`
- OAuth2 (Keycloak) for user auth, guest mode for demo/testing
- HTTPS required for all production deployments
- CORS enabled for frontend domain
- Data minimization, audit logging, user data management

---

## Deployment

### Backend (FastAPI)
1. Set up `.env` with all secrets (OpenAI, Keycloak, OpenEMR, RabbitMQ)
2. Run: `uvicorn main:app --reload`
3. Ensure CORS is enabled for your frontend domain

### Frontend (Flutter Web)
1. Run: `flutter build web --base-href /MMT/`
2. Deploy `build/web` to GitHub Pages or your web host
3. Set Keycloak redirect URI to your GitHub Pages URL

### OpenEMR & RabbitMQ
1. Deploy OpenEMR and RabbitMQ
2. Configure OpenEMR API key in `.env`
3. Start the RabbitMQ consumer

---

## File Structure (Key Parts)

- `/backend/main.py` - FastAPI backend, all endpoints
- `/backend/.env` - Secrets and API keys
- `/backend/openemr_consumer.py` - RabbitMQ to OpenEMR integration
- `/app/lib/main.dart` - Flutter app main logic
- `/app/pubspec.yaml` - Flutter dependencies
- `/app/web/index.html` - Web entry point

---

## Example .env
```env
OPENAI_API_KEY=sk-...
KEYCLOAK_PUBLIC_KEY=...
KEYCLOAK_ISSUER=...
GUEST_SECRET=guestsecret
OPENEMR_API_KEY=test-api-key
RABBITMQ_URL=amqp://guest:guest@localhost/
```

---

## API Endpoints (Backend)

- `/login/oauth2` - Exchange Keycloak token
- `/login/guest` - Get guest token
- `/transcribe/` - Local Whisper (transcribe later)
- `/transcribe/cloud/` - OpenAI Whisper API (real-time/ambient)
- `/upload_chunk/` - Chunked upload
- `/network_advice/` - Bandwidth check

---

## Compliance Checklist
- [x] OAuth2 login (Keycloak)
- [x] Guest login
- [x] HTTPS everywhere
- [x] All secrets in .env
- [x] CORS enabled
- [x] Data minimization
- [x] User data management (delete/export)
- [x] Audit logging (backend)
- [x] EHR integration (OpenEMR)

---

## 🤝 Contributing

1. Fork the repository.
2. Create your feature branch:  
   `git checkout -b feature/AmazingFeature`
3. Commit your changes:  
   `git commit -m 'feat: Add new feature'`
4. Push to the branch:  
   `git push origin feature/AmazingFeature`
5. Open a Pull Request.

---

## 📄 License

MIT License. See [LICENSE](LICENSE).

---

## 📧 Contact

- Email: Info@WebQx.Healthcare
- Project: [https://github.com/WebQx/MMT](https://github.com/WebQx/MMT)
## 📧 Contact

- Email: Info@WebQx.Healthcare
- Project Link: [https://github.com/WebQx/MMT](https://github.com/WebQx/MMT)

