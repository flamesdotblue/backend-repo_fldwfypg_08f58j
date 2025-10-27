import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    tone: Literal["neutral", "poetic", "scientific", "traditional"] = "neutral"


class ChatResponse(BaseModel):
    reply: str
    tone: str


def generate_reply(prompt: str, tone: str) -> str:
    q = prompt.strip()
    if tone == "poetic":
        return (
            f"O seeker of sparks, you ask: ‘{q}’.\n"
            "Between dawn and dusk, the answer drifts like light on water —\n"
            "consider the roots beneath the bloom, the cause beneath the sign.\n"
            "Walk gently, gather facts, and let wonder be your compass."
        )
    if tone == "scientific":
        return (
            f"Question: {q}\n"
            "Summary: Based on first principles and known evidence, we can analyze the problem,\n"
            "state assumptions explicitly, and derive testable predictions.\n"
            "Recommendation: break it into variables, evaluate constraints, and iterate with data."
        )
    if tone == "traditional":
        return (
            f"You ask: {q}.\n"
            "As elders say: measure twice, cut once. Knowledge grows from patience,\n"
            "listening, and steady hands. Begin with the simple, respect the process,\n"
            "and let experience guide each step."
        )
    # neutral
    return (
        f"You asked: {q}.\n"
        "Here is a balanced perspective: clarify the goal, gather reliable sources,\n"
        "compare options, and choose the path that aligns with your constraints and values."
    )


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = generate_reply(req.prompt, req.tone)
    return ChatResponse(reply=reply, tone=req.tone)


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
