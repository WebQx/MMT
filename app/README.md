# MMT Frontend

Flutter client for the MMT transcription backend.

## Unified Endpoint Usage
Uses backend `/transcribe/` which accepts:
1. Multipart file upload (`file` field) with optional `use_cloud=true` query for cloud model.
2. JSON ambient payload `{ "text": "...", "mode": "ambient" }` (no model inference).

## Build-Time Configuration
Pass via `--dart-define`:
```
BASE_URL=https://transcribe.example.com
KEYCLOAK_ISSUER=https://keycloak.example/realms/mmt
```
Example:
```
flutter run --dart-define=BASE_URL=http://localhost:8000 --dart-define=KEYCLOAK_ISSUER=https://keycloak.local/realms/mmt
```

## Auth
Keycloak OpenID Connect. Ensure realm roles include `writer` or `reader` mapped to access. Guest login disabled in production (backend `ENV=prod`).

### OAuth providers (web)
- The login screen exposes Google, Microsoft, and Apple buttons. When the backend is configured with the corresponding `OAUTH_*` env vars it returns provider authorize URLs.
- On web builds the app captures the `#access_token=` fragment after redirect and persists it to SharedPreferences so the `AppStateProvider` treats the user as authenticated.
- Non-web platforms keep throwing `UnsupportedError` until native deep link handling is added, preventing accidental usage on mobile builds.

## Ambient Mode
Continuous speech capture; sends finalized segments as JSON ambient transcripts. Provide clear UI indicator (checkbox + status). Consider user consent and optional local-only buffer.

## Roadmap
- Token refresh & retry logic
- Crash/error telemetry (Sentry / Crashlytics)
- Offline queue for record-later
- PHI redaction before share/print

## Development
Run backend locally, then:
```
flutter pub get
flutter run --dart-define=BASE_URL=http://localhost:8000
```

## Testing
Add widget tests under `test/` (pending). Suggested scenarios: guest login (dev), file upload success, ambient transcript send.

