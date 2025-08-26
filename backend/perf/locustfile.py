"""Locust performance test harness for transcription endpoints."""
from locust import HttpUser, task, between
import base64

SAMPLE_AUDIO = base64.b64encode(b"RIFF....fakewavdata").decode()


class TranscriptionUser(HttpUser):
    wait_time = between(0.5, 2.0)
    token = None

    def on_start(self):  # noqa: D401
        # Assume guest token if allowed
        resp = self.client.post("/login/guest")
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    @task(3)
    def local_transcribe(self):  # noqa: D401
        if not self.token:
            return
        files = {"file": ("sample.wav", b"RIFF....data", "audio/wav")}
        self.client.post("/transcribe/local/", headers={"Authorization": f"Bearer {self.token}"}, files=files)

    @task(1)
    def health(self):  # noqa: D401
        self.client.get("/health/ready")
