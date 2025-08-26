from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx
# Optional imports - will work without these for basic functionality
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    whisper = None
    WHISPER_AVAILABLE = False
from datetime import datetime, timedelta
import jwt
try:
    import pika
    PIKA_AVAILABLE = True
except ImportError:
    pika = None
    PIKA_AVAILABLE = False
import json
from typing import Optional, List
import tempfile
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="MMT - Multilingual Medical Transcription API",
    description="Healthcare-grade transcription platform with OpenAI Whisper integration",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_DOMAIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI configuration
if OPENAI_AVAILABLE and openai:
    openai.api_key = os.getenv("OPENAI_API_KEY")

# Load local Whisper model (will be downloaded on first use)
local_whisper_model = None

def get_local_whisper():
    global local_whisper_model
    if not WHISPER_AVAILABLE:
        raise Exception("Whisper not available - install with: pip install openai-whisper")
    if local_whisper_model is None:
        local_whisper_model = whisper.load_model("base")
    return local_whisper_model

# RabbitMQ connection
def get_rabbitmq_connection():
    if not PIKA_AVAILABLE:
        return None
    try:
        connection = pika.BlockingConnection(
            pika.URLParameters(os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/"))
        )
        return connection
    except Exception as e:
        print(f"RabbitMQ connection failed: {e}")
        return None

# Pydantic models
class LoginRequest(BaseModel):
    token: str

class GuestLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TranscriptionRequest(BaseModel):
    language: Optional[str] = "auto"
    prompt: Optional[str] = None

class TranscriptionResponse(BaseModel):
    id: str
    text: str
    language: str
    confidence: float
    timestamp: datetime

class NetworkAdviceResponse(BaseModel):
    recommended_mode: str
    bandwidth_estimate: str
    latency_ms: int

# Authentication functions
def verify_keycloak_token(token: str) -> dict:
    """Verify Keycloak JWT token"""
    try:
        # In production, you would verify against Keycloak's public key
        # For demo purposes, we'll do basic validation
        public_key = os.getenv("KEYCLOAK_PUBLIC_KEY")
        if not public_key:
            raise HTTPException(status_code=500, detail="Keycloak not configured")
        
        # Decode JWT (simplified - in production use proper key verification)
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_guest_token(token: str) -> dict:
    """Verify guest token"""
    secret = os.getenv("GUEST_SECRET", "guestsecret123")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid guest token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    
    # Try guest token first
    try:
        return verify_guest_token(token)
    except HTTPException:
        pass
    
    # Try Keycloak token
    try:
        return verify_keycloak_token(token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid authentication")

def send_to_rabbitmq(message: dict):
    """Send transcription result to RabbitMQ for OpenEMR integration"""
    if not PIKA_AVAILABLE:
        print("RabbitMQ not available - skipping message")
        return
        
    connection = get_rabbitmq_connection()
    if connection:
        try:
            channel = connection.channel()
            channel.queue_declare(queue='transcriptions', durable=True)
            channel.basic_publish(
                exchange='',
                routing_key='transcriptions',
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
            )
            connection.close()
        except Exception as e:
            print(f"Failed to send to RabbitMQ: {e}")

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "MMT API",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }

@app.post("/login/oauth2")
async def oauth2_login(request: LoginRequest):
    """Exchange Keycloak token for API access"""
    try:
        user_info = verify_keycloak_token(request.token)
        # In production, you might want to create your own JWT with specific claims
        return {
            "access_token": request.token,
            "token_type": "bearer",
            "user_id": user_info.get("sub"),
            "email": user_info.get("email")
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Keycloak token")

@app.post("/login/guest", response_model=GuestLoginResponse)
async def guest_login():
    """Get guest access token"""
    secret = os.getenv("GUEST_SECRET", "guestsecret123")
    payload = {
        "user_type": "guest",
        "user_id": f"guest_{uuid.uuid4().hex[:8]}",
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return GuestLoginResponse(access_token=token)

@app.post("/transcribe/", response_model=TranscriptionResponse)
async def transcribe_local(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    prompt: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Transcribe audio using local Whisper model (transcribe later)"""
    try:
        if not WHISPER_AVAILABLE:
            raise HTTPException(status_code=501, detail="Local Whisper not available. Install with: pip install openai-whisper")
            
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Transcribe with local Whisper
        model = get_local_whisper()
        result = model.transcribe(
            temp_file_path,
            language=None if language == "auto" else language,
            initial_prompt=prompt
        )

        # Clean up temp file
        os.unlink(temp_file_path)

        # Create response
        transcription_id = str(uuid.uuid4())
        response = TranscriptionResponse(
            id=transcription_id,
            text=result["text"],
            language=result["language"],
            confidence=1.0,  # Whisper doesn't provide confidence scores
            timestamp=datetime.utcnow()
        )

        # Send to RabbitMQ for OpenEMR integration
        message = {
            "transcription_id": transcription_id,
            "user_id": current_user.get("user_id"),
            "text": result["text"],
            "language": result["language"],
            "method": "local_whisper",
            "timestamp": datetime.utcnow().isoformat()
        }
        send_to_rabbitmq(message)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/transcribe/cloud/", response_model=TranscriptionResponse)
async def transcribe_cloud(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    prompt: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Transcribe audio using OpenAI Whisper API (real-time/ambient)"""
    try:
        if not OPENAI_AVAILABLE or not openai:
            raise HTTPException(status_code=501, detail="OpenAI not available. Install with: pip install openai")
            
        if not openai.api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")

        # Read file content
        content = await file.read()
        
        # Create a temporary file for OpenAI API
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Transcribe with OpenAI Whisper
        with open(temp_file_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language=None if language == "auto" else language,
                prompt=prompt
            )

        # Clean up temp file
        os.unlink(temp_file_path)

        # Create response
        transcription_id = str(uuid.uuid4())
        response = TranscriptionResponse(
            id=transcription_id,
            text=transcript.text,
            language=language if language != "auto" else "auto-detected",
            confidence=1.0,
            timestamp=datetime.utcnow()
        )

        # Send to RabbitMQ for OpenEMR integration
        message = {
            "transcription_id": transcription_id,
            "user_id": current_user.get("user_id"),
            "text": transcript.text,
            "language": language,
            "method": "openai_whisper",
            "timestamp": datetime.utcnow().isoformat()
        }
        send_to_rabbitmq(message)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloud transcription failed: {str(e)}")

@app.post("/upload_chunk/")
async def upload_chunk(
    chunk: UploadFile = File(...),
    chunk_number: int = Form(...),
    total_chunks: int = Form(...),
    file_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Handle chunked file upload for large audio files"""
    try:
        # Create upload directory if it doesn't exist
        upload_dir = "/tmp/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save chunk
        chunk_path = os.path.join(upload_dir, f"{file_id}_chunk_{chunk_number}")
        with open(chunk_path, "wb") as f:
            content = await chunk.read()
            f.write(content)
        
        # Check if all chunks are uploaded
        all_chunks_present = True
        for i in range(total_chunks):
            chunk_file = os.path.join(upload_dir, f"{file_id}_chunk_{i}")
            if not os.path.exists(chunk_file):
                all_chunks_present = False
                break
        
        if all_chunks_present:
            # Combine all chunks
            final_file_path = os.path.join(upload_dir, f"{file_id}_complete")
            with open(final_file_path, "wb") as final_file:
                for i in range(total_chunks):
                    chunk_file = os.path.join(upload_dir, f"{file_id}_chunk_{i}")
                    with open(chunk_file, "rb") as chunk_f:
                        final_file.write(chunk_f.read())
                    os.unlink(chunk_file)  # Clean up chunk
            
            return {
                "status": "complete",
                "file_id": file_id,
                "message": "All chunks uploaded and combined"
            }
        else:
            return {
                "status": "pending",
                "chunk_number": chunk_number,
                "total_chunks": total_chunks,
                "message": f"Chunk {chunk_number} uploaded successfully"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunk upload failed: {str(e)}")

@app.get("/network_advice/", response_model=NetworkAdviceResponse)
async def network_advice(current_user: dict = Depends(get_current_user)):
    """Provide bandwidth and network optimization advice"""
    try:
        # Simple network advice (in production, you'd do actual bandwidth testing)
        return NetworkAdviceResponse(
            recommended_mode="wifi",
            bandwidth_estimate="high",
            latency_ms=50
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Network advice failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "api": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check OpenAI API
    health_status["services"]["openai"] = "configured" if (OPENAI_AVAILABLE and openai and openai.api_key) else "not_configured"
    
    # Check RabbitMQ
    connection = get_rabbitmq_connection()
    health_status["services"]["rabbitmq"] = "connected" if connection else "disconnected"
    if connection:
        connection.close()
    
    # Check Keycloak
    health_status["services"]["keycloak"] = "configured" if os.getenv("KEYCLOAK_PUBLIC_KEY") else "not_configured"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)