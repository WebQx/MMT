MMT: Multilingual Medical Transcription Suite
🌟 Project Overview
MMT (Multilingual Medical Transcription) is an open-source project dedicated to making high-quality medical transcription accessible and affordable for healthcare professionals worldwide, especially in resource-constrained environments. By combining the power of OpenAI's Whisper, Flutter, and a lightweight Python backend, MMT offers a sustainable, self-hosted alternative to expensive, proprietary cloud services.

✨ Key Features
Offline-First Workflow: The Flutter app can record and store audio locally, allowing doctors to continue their work even without a stable internet connection. Recordings are automatically transcribed when connectivity is restored.

Cost-Effective: By running the Whisper model on a local or low-cost cloud server, MMT eliminates the per-minute transcription costs associated with commercial APIs like Google or Amazon.

Robust Multilingual Support: Leverage Whisper's state-of-the-art multilingual capabilities to accurately transcribe medical conversations in a wide range of languages and dialects.

Cross-Platform: The intuitive Flutter UI works seamlessly on both Android and iOS devices, with a consistent user experience.

Customizable: The backend API can be easily modified to add new features, fine-tune the model with local terminology, or integrate with existing EMR systems.

🚀 Getting Started
Prerequisites
To get started with MMT, you'll need the following installed:

Flutter SDK (latest stable version)

Python 3.8+

Git

Installation & Setup
Clone the repository:

Bash

git clone https://github.com/your-username/MMT.git
cd MMT
Backend Server Setup

Navigate to the backend directory:

Bash

cd backend
Create and activate a virtual environment (recommended):

Bash

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Install the required Python packages:

Bash

pip install -r requirements.txt
Start the server. For development, a simple local server is sufficient:

Bash

uvicorn main:app --host 0.0.0.0 --port 8000
The transcription API will now be live at http://localhost:8000.

Flutter App Setup

Navigate to the app directory:

Bash

cd ../app
Install Flutter dependencies:

Bash

flutter pub get
Configure API Endpoint: Open lib/config/api_config.dart and update the BASE_URL to point to your backend server's IP address.

Dart

// Replace with your server's IP address.
const String BASE_URL = 'http://your-server-ip:8000'; 
Run the app on a connected device or simulator:

Bash

flutter run
🏗️ Architecture
MMT follows a decoupled, client-server architecture to ensure flexibility and scalability.

Frontend (Flutter): Manages the user interface, audio recording, and communication with the backend. It's designed to be a thin client, with all heavy processing handled on the server.

Backend (Python/FastAPI): A simple RESTful API that receives audio files, processes them using the Whisper model, and returns the transcribed text. This is the heart of the transcription engine.

Local or Cloud Server: The backend can be hosted on a local machine in a clinic for maximum privacy and low cost, or on a low-cost cloud VM for more flexible access.

A high-level diagram illustrating the data flow from the Flutter app to the Whisper backend.

📈 Performance & Resource Usage
The performance of the transcription depends on the hardware of your backend server.

Model Size	VRAM Required	Transcription Time (per min of audio)
tiny	~1 GB	~5 seconds
base	~1 GB	~15 seconds
small	~2 GB	~30 seconds
medium	~5 GB	~1 minute
large-v2	~10 GB	~2 minutes

Export to Sheets
Note: The base or small model is often a good balance of accuracy and speed for most use cases. For resource-constrained hardware, tiny is a great starting point.

🤝 How to Contribute
We welcome contributions from the community! Whether it's adding a new feature, fixing a bug, or improving documentation, your help is appreciated.

Fork the repository.

Create your feature branch (git checkout -b feature/AmazingFeature).

Commit your changes (git commit -m 'feat: Add new feature').

Push to the branch (git push origin feature/AmazingFeature).

Open a Pull Request.

📄 License
This project is licensed under the MIT License. See the LICENSE file for details.

📧 Contact
Info@WebQx.Healthcare

Project Link: https://github.com/WebQx/MMT
