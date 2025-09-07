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

4. Access the application (local dev defaults):

- Frontend: http://localhost:3000  (Flutter web-server)
- Backend API: http://localhost:8000  (uvicorn / FastAPI)
- RabbitMQ Management: http://localhost:15672  (RabbitMQ UI)

Tip: the repo includes a one-step PowerShell helper script `scripts\start-dev.ps1` that will start the backend (uvicorn) in a background process and launch the Flutter web-server on port 3000 with the correct `BASE_URL` dart-define. See the "One-step dev script" section below.

Troubleshooting the frontend port (if http://localhost:3000 doesn't load):

- Common quick checks (PowerShell):

```powershell
Test-NetConnection -ComputerName localhost -Port 3000
netstat -ano | Select-String ":3000"
Get-Process -Id <PID-from-netstat> -ErrorAction SilentlyContinue
```

- Interpreting `Test-NetConnection` output:
	- If `TcpTestSucceeded : False` and the warnings show both `(::1 : 3000)` and `(127.0.0.1 : 3000) failed`, nothing is listening on port 3000. That matches `netstat` showing no process bound to :3000.
	- If `TcpTestSucceeded : True` but you still can't reach the page, check firewall rules or that the server bound to `0.0.0.0` vs only `::1` (IPv6 loopback).

- If nothing is listening, run the one-step script from the repo root to start backend + frontend and capture output:

```powershell
.\scripts\start-dev.ps1
```

- If the script prints a Flutter or uvicorn error (address-in-use, missing Flutter, or Python errors), follow the message it prints (or paste the output into an issue/PR comment for help).


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

Deploying the full stack (frontend on GitHub Pages + backend elsewhere):

- Frontend: the workflow `.github/workflows/deploy_frontend.yml` builds the Flutter web app and publishes `app/build/web` to GitHub Pages; it expects a repository secret named `BACKEND_URL` containing the public URL of the backend API.
- Backend: the workflow `.github/workflows/build_backend_image.yml` builds and pushes a Docker image to GitHub Container Registry as `ghcr.io/<owner>/mmt-backend:latest` on push. You can then deploy that image on Render, Railway, Fly, Cloud Run, or any container host.

Quick Render example (after image pushed to GHCR):

1. Create a new Web Service on Render.
2. Choose "Docker" and use the GHCR image `ghcr.io/<owner>/mmt-backend:latest` or configure Render to deploy from your repo's `backend/Dockerfile`.
3. Add required environment variables (copy values from `backend/.env.example`) in the Render dashboard.
4. When Render assigns a public URL, set that value as the `BACKEND_URL` repository secret (Settings → Secrets → Actions) so the frontend workflow builds with the correct API URL.

Security: do not store secrets in plaintext in the repo. Use platform environment variables and GitHub Actions secrets for deployment.

## Deploying full stack to GitHub Pages (frontend) + container host (backend)

This project includes GitHub Actions to build the Flutter frontend and push it to GitHub Pages, and to build/publish the backend Docker image to GitHub Container Registry (GHCR). Use the steps below to wire everything up and deploy a production-ready frontend and backend.

1) Add required repository secrets (GitHub → Settings → Secrets → Actions)
	- `BACKEND_URL` — public URL of your backend API (e.g. https://mmt-backend.onrender.com)
	- `RENDER_API_KEY` — Render API key (optional, only if using Render auto-deploy)
	- `RENDER_SERVICE_ID` — Render service id (optional)

	You can also set secrets via the GitHub CLI:
	```powershell
	gh secret set BACKEND_URL --body "https://mmt-backend.onrender.com"
	gh secret set RENDER_API_KEY --body "<your_render_api_key>"
	gh secret set RENDER_SERVICE_ID --body "<your_render_service_id>"
	```

2) Enable GitHub Pages
	- Go to the repository Settings → Pages and set the source to branch `gh-pages` (the `deploy_frontend.yml` action will publish there).

3) Backend hosting options
	- Render (recommended): create a Web Service and either point Render to this repo (uses `backend/Dockerfile`) or configure it to pull the GHCR image `ghcr.io/<owner>/mmt-backend:latest`.
	  - Add environment variables from `backend/.env.example` in the Render dashboard.
	  - When Render returns a public URL (https://...), add that URL as the `BACKEND_URL` secret.
	- Railway, Fly, Cloud Run: similar flow — deploy the `backend/` Dockerfile or use the published GHCR image and then set `BACKEND_URL` accordingly.

4) CORS & frontend origin
	- Make sure the backend allows CORS from your GitHub Pages origin (e.g. `https://<your-org>.github.io` or your custom domain). Set `FRONTEND_DOMAIN` / CORS environment vars in the backend host to include the Pages hostname.

5) How deployment works
	- `deploy_frontend.yml` builds the Flutter web app (`app`) and publishes `app/build/web` to the `gh-pages` branch. It reads `BACKEND_URL` from secrets at build time and passes it as a `--dart-define=BASE_URL=...` value.
	- `build_backend_image.yml` builds the Docker image and pushes it to GHCR as `ghcr.io/<owner>/mmt-backend:latest`.
	- `deploy_backend_to_render.yml` triggers a Render deploy after a successful backend image build (requires `RENDER_API_KEY` and `RENDER_SERVICE_ID`).

6) Manual triggers & troubleshooting
	- To run the frontend build locally for testing and simulate the Pages build:
	  ```powershell
	  cd app
	  flutter build web --release --dart-define=BASE_URL=https://mmt-backend.onrender.com
	  # open app/build/web/index.html locally or deploy the folder to any static host
	  ```
	- If the frontend cannot contact the backend after Pages deploy, verify `BACKEND_URL` is correct and that the backend CORS includes the Pages origin.

7) Quick verification
	- After workflows complete, visit the Pages URL (Settings → Pages shows the published URL) and test the app flows that call the backend (guest login, /health, etc.).


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