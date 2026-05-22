from fastapi import FastAPI
from pydantic import BaseModel

from agent import run_agent

# =========================================================
# FastAPI App Initialization
# =========================================================

app = FastAPI(
    title="SHL AI Assessment Agent",
    description="AI-powered SHL assessment recommendation system",
    version="1.0.0"
)

# =========================================================
# Request Schema
# =========================================================

class ChatRequest(BaseModel):

    query: str

# =========================================================
# Root Endpoint
# =========================================================

@app.get("/")

def root():

    return {
        "message": "SHL AI Agent API is running",
        "docs": "http://127.0.0.1:8000/docs"
    }

# =========================================================
# Health Endpoint
# =========================================================

@app.get("/health")

def health_check():

    return {
        "status": "healthy",
        "message": "SHL AI Agent is running successfully"
    }

# =========================================================
# Chat Endpoint
# =========================================================

@app.post("/chat")

def chat(request: ChatRequest):

    try:

        # User query
        query = request.query

        # Run AI agent
        response = run_agent(query)

        # Return response
        return {

            "success": True,
            "query": query,
            "response": response
        }

    except Exception as e:

        return {

            "success": False,
            "error": str(e)
        }