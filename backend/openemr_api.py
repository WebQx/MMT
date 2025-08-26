import requests
import os

def send_to_openemr_api(filename, text, api_url, api_key):
    payload = {
        "filename": filename,
        "transcription": text,
        "user": "guest"
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.post(api_url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()
