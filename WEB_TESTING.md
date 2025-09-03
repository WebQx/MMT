# MMT Web App Testing Guide (Revised)

This version resolves earlier conflicts/inaccuracies: incorrect integration test commands, inconsistent ports (3000 vs 8080), improper `python -m http.server` usage, and missing setup steps for web + auth flows.

---
## 1. Test Environment Prereqs
| Item | Command / Note |
|------|----------------|
| Enable web | `flutter config --enable-web` |
| List devices | `flutter devices` |
| Chrome device | Preferred for debugging & hot reload |
| Backend (FastAPI) | `uvicorn main:app --port 9000 --reload` inside `backend` |
| Env defines (example) | `--dart-define=KEYCLOAK_ISSUER=... --dart-define=SENTRY_DSN=...` |

Recommended dev port alignment: use **3000** for Flutter (to match prior docs) and **9000** for backend.

---
## 2. Unit Tests
```bash
cd app
flutter test
```

---
## 3. Integration / Widget-Level (Golden) Tests
Flutter’s modern approach for web & mobile integration tests is the `integration_test` package run via `flutter test --platform chrome` (for web) or standard `flutter test` (device backends will be simulated).

Directory convention:
```
app/
  integration_test/
    app_flow_test.dart
```

Example file (`integration_test/app_flow_test.dart`):
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mmt/main.dart' as app;

void main() {
  testWidgets('Guest login flow renders transcription UI', (tester) async {
    app.main();
    await tester.pumpAndSettle();
    expect(find.text('MMT Transcription'), findsOneWidget);
  });
}
```

Run (web):
```bash
flutter test --platform chrome integration_test/app_flow_test.dart
```

Run (all integration tests mobile/web capable):
```bash
flutter test integration_test
```

Note: The older `flutter drive` is only needed for device automation with a separate driver file—currently not required here.

---
## 4. Manual Testing Checklist
### Core Functionality
- [ ] Guest login works (token stored)
- [ ] OAuth login flow (Keycloak) completes
- [ ] File upload accepts supported audio (wav/mp3/m4a?)
- [ ] Ambient mode microphone permission + streaming
- [ ] Transcription displays parsed text
- [ ] Export (print / share) triggers without errors
- [ ] Error states (network 500 / 401 refresh) handled

### State & Persistence
- [ ] Tokens persisted in secure storage (non-web) / memory (web fallback)
- [ ] Refresh token path invoked when 401 occurs

---
## 5. Cross-Browser Testing
Use a consistent port (3000):
```bash
# Chrome (auto opens)
flutter run -d chrome --web-port 3000 \
  --dart-define=KEYCLOAK_ISSUER=https://example/realms/realm

# Generic web server (for Firefox/Safari - open manually)
flutter run -d web-server --web-port 3000
# Then in another browser: http://localhost:3000
```
If port busy, retry with `--web-port 3010`.

---
## 6. Responsive Design Matrix
Test breakpoints:
- Desktop: 1920x1080, 1440x900, 1366x768
- Tablet: 1024x768, 834x1112, 768x1024
- Mobile: 414x896, 390x844, 375x667

Checklist:
- [ ] Layout scales (no overflow warnings in console)
- [ ] Buttons accessible via keyboard (tab order)
- [ ] Text legible (contrast AA)

---
## 7. Performance & Build
Build optimized bundle:
```bash
flutter build web --release --dart-define=KEYCLOAK_ISSUER=... --dart-define=SENTRY_DSN=...
```
Serve locally:
```bash
python -m http.server 8000 --directory build/web
# OR: npx serve build/web
```
Measure:
- Chrome DevTools Performance panel
- Lighthouse (Performance + PWA + Accessibility)

---
## 8. End-to-End (E2E) via Playwright
Setup (local, no global install needed):
```bash
cd app
npm init -y
npm install -D @playwright/test
npx playwright install
```
`playwright.config.js` minimal:
```js
// playwright.config.js
module.exports = { webServer: { command: 'flutter run -d web-server --web-port 3000', port: 3000, reuseExistingServer: true } };
```
Sample test `tests/app.spec.js`:
```js
const { test, expect } = require('@playwright/test');
test('guest flow', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.click('text=Continue as Guest');
  await expect(page.locator('text=MMT Transcription')).toBeVisible();
});
```
Run:
```bash
npx playwright test
```

---
## 9. Accessibility Audit
```bash
npx @axe-core/cli http://localhost:3000
```
Add manual keyboard traversal + screen reader (NVDA / VoiceOver) pass.

---
## 10. Security Checklist
- [ ] CSP headers set in production host (avoid `unsafe-inline`)
- [ ] HTTPS enforced; mixed content blocked
- [ ] Tokens never logged to console
- [ ] Refresh token rotation tested
- [ ] No sensitive data stored in web local storage (secure_storage fallback)
- [ ] Input fields sanitized (basic redaction already present)

---
## 11. Quick Commands (Cheat Sheet)
```bash
# From repo root
cd backend && uvicorn main:app --port 9000 --reload

# In another terminal
cd app
flutter run -d chrome --web-port 3000 \
  --dart-define=KEYCLOAK_ISSUER=https://example/realms/realm

# Unit tests
flutter test

# Integration (web)
flutter test --platform chrome integration_test

# Build release + serve
flutter build web --release
python -m http.server 8000 --directory build/web
```

---
## 12. Production Validation
- [ ] Release build loads < 3s on first byte (LAN)
- [ ] No 404s for main.dart.js / assets
- [ ] Sentry events appear (if DSN set)
- [ ] Auth callback redirect works with deployed origin

---
## 13. Key Areas (Prioritized)
1. Authentication (guest + OAuth error fallback)
2. Upload pipeline (large file, slow network, retry path)
3. Ambient mode streaming stability
4. Token refresh resilience (force 401 on backend)
5. Accessibility & responsive coverage
6. Performance (bundle size, runtime CPU)

---
## 14. Known Limitations / TODO
- `flutter_secure_storage` is limited on web (fallback logic may be needed).
- Need dedicated mock backend for deterministic integration tests.
- Add golden tests for layout regressions.

---
## 15. Troubleshooting
| Symptom | Fix |
|---------|-----|
| Port not opening | Try `--web-port 3010` or kill stale Dart processes |
| Auth popup blocked | Ensure user gesture (button) triggers flow |
| Slow hot reload | Run Chrome with extensions disabled (`--disable-extensions`) |
| Missing packages | Re-run `flutter pub get` after editing `pubspec.yaml` |

---
Feel free to extend this guide as the app grows.