import os
import time
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from src.session import get_session, save_session, clear_session
from src.llm import get_nlu_response

app = FastAPI(
    title="Ultra-Low-Latency Multilingual Welfare Chatbot API",
    description="Backend services for WhatsApp, SMS webhooks, and Missed-Call trigger loops.",
    version="1.1"
)

# Enable CORS for local simulator testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str

class MissedCallRequest(BaseModel):
    phone_number: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Core messaging endpoint representing WhatsApp and SMS webhooks.
    """
    start_time = time.time()
    
    session_id = request.session_id
    user_message = request.message
    
    # Retrieve state
    session = get_session(session_id)
    
    # Generate bot response
    bot_response = get_nlu_response(user_message, session)
    
    # Save updated state
    save_session(session_id, session)
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    return {
        "response": bot_response,
        "session": {
            "step": session.get('step'),
            "lang": session.get('lang'),
            "age": session.get('age'),
            "income": session.get('income'),
            "occupation": session.get('occupation'),
            "gender": session.get('gender')
        },
        "latency_ms": elapsed_ms
    }

@app.post("/api/missed-call")
async def missed_call_endpoint(request: MissedCallRequest):
    """
    Simulates the zero-data offline trigger where a user places a missed call.
    Automatically resets their session and dispatches the initial SMS greeting.
    """
    start_time = time.time()
    
    phone_number = request.phone_number.strip()
    if not phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")
        
    # 1. Reset any existing session for this user to restart clean
    clear_session(phone_number)
    session = get_session(phone_number)
    
    # 2. Trigger initial greeting (simulating Twilio sending SMS back)
    initial_response = get_nlu_response("", session) # Fetches greeting
    
    save_session(phone_number, session)
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    return {
        "success": True,
        "message": f"Missed call from {phone_number} registered. SMS session initiated.",
        "response": initial_response,
        "session_id": phone_number,
        "session": {
            "step": session.get('step'),
            "lang": session.get('lang')
        },
        "latency_ms": elapsed_ms
    }

@app.post("/api/reset")
async def reset_endpoint(session_id: str = Body(..., embed=True)):
    """
    Clears the session variables for a clean restart.
    """
    clear_session(session_id)
    return {"success": True, "message": "Session reset successful."}

# Serve simulator HTML page on the root index
@app.get("/", response_class=FileResponse)
async def read_root():
    static_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'index.html')
    if os.path.exists(static_file):
        return FileResponse(static_file)
    else:
        return HTMLResponse("<h2>Simulator file static/index.html not found!</h2>", status_code=404)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
