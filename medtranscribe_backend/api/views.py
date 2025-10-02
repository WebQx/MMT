from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
import tempfile
import os

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "tiny")

model = None

def get_model():
	global model
	if model is None:
		from faster_whisper import WhisperModel
		model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
	return model

class TranscribeView(APIView):
	authentication_classes = [SessionAuthentication, BasicAuthentication]
	permission_classes = [IsAuthenticated]

	def post(self, request):
		audio_file = request.FILES.get('audio')
		if not audio_file:
			return Response({'error': 'No audio file provided.'}, status=400)

		# Save uploaded chunk to a temporary file because faster-whisper expects a path
		with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
			for chunk in audio_file.chunks():
				tmp.write(chunk)
			tmp_path = tmp.name
		try:
			segments, info = get_model().transcribe(tmp_path)
			collected = []
			full_text = []
			for seg in segments:
				collected.append({
					"id": seg.id,
					"start": seg.start,
					"end": seg.end,
					"text": seg.text.strip()
				})
				full_text.append(seg.text.strip())
			structured = {
				"language": info.language,
				"language_probability": info.language_probability,
				"text": " ".join(full_text).strip(),
				"segments": collected,
			}
			return Response(structured)
		finally:
			try:
				os.remove(tmp_path)
			except OSError:
				pass
from django.shortcuts import render

# Create your views here.

