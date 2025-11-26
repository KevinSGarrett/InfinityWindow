from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="InfinityWindow Backend",
    description="Backend for the InfinityWindow personal AI workbench.",
    version="0.0.1",
)


class ChatTestRequest(BaseModel):
    message: str


class ChatTestResponse(BaseModel):
    echo: str


@app.get("/health")
def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "service": "InfinityWindow backend"}


@app.post("/chat/test", response_model=ChatTestResponse)
def chat_test(payload: ChatTestRequest):
    """
    Temporary test endpoint that simply echoes your message.
    We'll later replace this with the orchestrator.
    """
    return ChatTestResponse(echo=f"You said: {payload.message}")
