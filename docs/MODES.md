MMT Modes

1) Demo (guest)
- Intended for quick demos on GitHub Pages or when the backend is not reachable.
- Limited functionality; cloud transcription and some integrations are disabled.
- No account required.

2) Local Whisper (download - transcribe later)
- The user downloads and runs a local transcription application ("Local Whisper").
- Works without internet. Transcription results are saved locally and can be uploaded later.
- Recommended for offline/air-gapped usage.

3) Cloud (OpenAI Whisper API / backend)
- Real-time and ambient transcription powered by cloud services and the backend.
- Requires signing in (Google/Apple/Microsoft/Keycloak) and a backend with proper credentials (OpenAI key, etc.).
- Provides the full feature set.

Usage guidance

- Demo mode is only for guests and should not be mixed with Local Whisper.
- When in demo mode the UI will surface a sign-in CTA to unlock cloud features.
- Local Whisper is available to real users who choose to download and run the standalone app.

If you'd like a printable or embedded version of this doc in the app UI, I can add it as an in-app modal or help page.
