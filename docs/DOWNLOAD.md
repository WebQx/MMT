Local Whisper (offline) - Download & Run

This repository supports an offline "Local Whisper" mode where users can run a local transcription binary on their device and upload transcripts later.

How to get the local app

1) Releases
   - Download the latest release from: https://github.com/WebQx/MMT/releases/latest

2) Build from source (advanced)
   - Clone the repo and follow the build instructions in `app/README.md` (if present) or the `INSTALL.md`.

Running the local app

- The local binary runs on the user's device and writes transcript files which can later be uploaded to the MMT web UI when internet is available.
- We recommend packaging platform-specific installers (Windows/Mac/Linux) and publishing them on the Releases page.

Security

- Local Whisper runs entirely on the user's machine; no audio is sent to external services unless the user explicitly chooses cloud mode.

Support

- If you want a packaged installer added to Releases, open an issue with your target platform and build preferences.
