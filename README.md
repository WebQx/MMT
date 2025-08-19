WebQx MMT: Multilingual Medical Transcription Suite 🌟

MMT (Multilingual Medical Transcription) is an open-source project dedicated to making high-quality medical transcription accessible and affordable for healthcare professionals worldwide, especially in resource-constrained environments. By combining OpenAI's Whisper, Flutter, and a lightweight Python backend, MMT offers a sustainable, self-hosted alternative to expensive, proprietary cloud services.

---

## ✨ Key Features

- **Offline-First Workflow:** Record and store audio locally; transcribe automatically when online.
- **Cost-Effective:** Run Whisper locally or on a low-cost cloud server—no per-minute API fees.
- **Robust Multilingual Support:** Accurate transcription in many languages and dialects.
- **Cross-Platform:** Flutter UI for Android and iOS.
- **Customizable:** Easily extend backend API, fine-tune models, or integrate with EMR systems.

---

## 🚀 Getting Started

### Prerequisites

- [Flutter SDK](https://flutter.dev/docs/get-started/install) (latest stable)
- Python 3.8+
- Git

---

### 1. Clone the Repository

```bash
git clone https://github.com/WebQx/MMT.git
cd MMT
```

---

### 2. Backend Server Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be live at [http://localhost:8000](http://localhost:8000).

---

### 3. Flutter App Setup

```bash
cd ../app
flutter pub get
```

**Configure API Endpoint:**  
Edit `lib/config/api_config.dart`:

```dart
// lib/config/api_config.dart
const String BASE_URL = 'http://your-server-ip:8000';
```

**Run the app:**

```bash
flutter run
```

---

## 🏗️ Architecture

- **Frontend (Flutter):** UI, audio recording, backend communication.
- **Backend (Python/FastAPI):** REST API for audio upload, Whisper transcription, and response.
- **Server:** Host locally for privacy/cost, or on a cloud VM for flexible access.

```
[Flutter App] <---audio---> [Python/FastAPI + Whisper] <---optionally---> [EMR/Other Systems]
```

---

## 📈 Performance & Resource Usage

| Model Size | VRAM Required | Transcription Time (per min audio) |
|------------|--------------|-------------------------------------|
| tiny       | ~1 GB        | ~5 seconds                         |
| base       | ~1 GB        | ~15 seconds                        |
| small      | ~2 GB        | ~30 seconds                        |
| medium     | ~5 GB        | ~1 minute                          |
| large-v2   | ~10 GB       | ~2 minutes                         |

> **Tip:** `base` or `small` models balance accuracy and speed. For limited hardware, use `tiny`.

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

