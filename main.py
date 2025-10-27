import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal, List, Dict

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


# A tiny, public-domain teaching set to ground responses
TEACHINGS: List[Dict[str, str]] = [
    {
        "source": "Bhagavad Gita 2.47",
        "tags": "krishna arjuna gita duty karma yoga dharma action" ,
        "text": "You have the right to work, but never to the fruit of work. Let not the fruits of action be your motive, nor let your attachment be to inaction.",
    },
    {
        "source": "Bhagavad Gita 4.7-8",
        "tags": "krishna gita avatar dharma protection righteousness" ,
        "text": "Whenever there is decline in righteousness and rise of unrighteousness, then I manifest Myself. For the protection of the good and the destruction of the wicked, for the establishment of dharma, I appear age after age.",
    },
    {
        "source": "Dhammapada 1:1-2",
        "tags": "buddha dhammapada mind intention suffering happiness" ,
        "text": "Mind precedes all phenomena; mind matters most. If with an impure mind one speaks or acts, suffering follows like the wheel the foot of the ox. If with a pure mind one speaks or acts, happiness follows like a shadow that never departs.",
    },
    {
        "source": "Dhammapada 160",
        "tags": "buddha dhammapada self effort discipline refuge" ,
        "text": "By oneself is evil done; by oneself is one defiled. By oneself is evil left undone; by oneself is one purified. Purity and impurity depend on oneself; no one can purify another.",
    },
    {
        "source": "Acharanga Sutra (Jain)",
        "tags": "mahavira jain ahimsa nonviolence restraint compassion" ,
        "text": "All breathing, existing, living, sentient creatures should not be slain, nor treated with violence, nor abused, nor tormented, nor driven away.",
    },
    {
        "source": "Uttaradhyayana Sutra (Jain)",
        "tags": "mahavira jain truth discipline conduct karma" ,
        "text": "A man is not called wise because he talks and talks again; but if he is peaceful, loving, and fearless then he is in truth called wise.",
    },
]


def _score(teaching: Dict[str, str], q: str) -> int:
    ql = q.lower()
    score = 0
    for token in teaching["tags"].split():
        if token in ql:
            score += 2
    # light fuzzy match on words in the verse text
    for word in ql.split():
        if len(word) > 4 and word in teaching["text"].lower():
            score += 1
    return score


def _select_teachings(prompt: str, limit: int = 2) -> List[Dict[str, str]]:
    ranked = sorted(TEACHINGS, key=lambda t: _score(t, prompt), reverse=True)
    # ensure at least something meaningful by mixing in diverse sources if low scores
    result = [t for t in ranked[:limit] if _score(t, prompt) > 0]
    if len(result) < limit:
        # add a diverse fallback not already present
        for t in TEACHINGS:
            if t not in result:
                result.append(t)
            if len(result) >= limit:
                break
    return result[:limit]


def generate_reply(prompt: str, tone: str) -> str:
    q = prompt.strip()
    picks = _select_teachings(q, limit=2)

    # Compose differently per tone
    if tone == "poetic":
        lines = [
            f"You ask beneath the banyan: ‘{q}’.",
            "Listen — tradition hums like a veena across ages:",
        ]
        for t in picks:
            lines.append(f"• {t['text']} — {t['source']}")
        lines.extend([
            "Between breath and breath, carry compassion and clarity.",
            "Walk as a flame that warms but does not burn.",
        ])
        return "\n".join(lines)

    if tone == "scientific":
        lines = [
            f"Question: {q}",
            "Contextual retrieval: selected teachings based on lexical overlap and tags.",
        ]
        for i, t in enumerate(picks, 1):
            lines.append(f"{i}. {t['source']}: {t['text']}")
        lines.append(
            "Synthesis: Across Hindu, Buddhist, and Jain sources, action aligned with duty, disciplined mind, and non-violence emerge as convergent principles."
        )
        return "\n".join(lines)

    if tone == "traditional":
        lines = [
            f"You inquire: {q}",
            "Hear what elders preserve:",
        ]
        for t in picks:
            lines.append(f"• {t['source']}: {t['text']}")
        lines.append("Take what is good, test by conduct, and proceed with humility.")
        return "\n".join(lines)

    # neutral
    lines = [f"You asked: {q}", "Relevant teachings:"]
    for t in picks:
        lines.append(f"• {t['source']}: {t['text']}")
    lines.append("In practice: clarify intent, choose the kindest sufficient action, and learn from outcomes.")
    return "\n".join(lines)


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
