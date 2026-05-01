from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

agent_instance = None
init_error: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_instance, init_error
    try:
        from agent import AgentHD
        agent_instance = AgentHD()
    except ValueError as e:
        init_error = str(e)
    except Exception as e:
        init_error = f"Falha ao inicializar o agente: {e}"
    yield



app = FastAPI(title="Agente tgameajuda", lifespan=lifespan)

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _require_agent():
    if init_error:
        raise HTTPException(status_code=503, detail=init_error)
    if agent_instance is None:
        raise HTTPException(status_code=503, detail="Agente não inicializado.")
    return agent_instance


class ChatRequest(BaseModel):
    message: str



# Rota principal
@app.get("/")
async def root():
    return FileResponse(TEMPLATES_DIR / "index.html")

# Servir favicon
@app.get("/favicon.ico")
async def favicon():
    return FileResponse(TEMPLATES_DIR / "favicon.ico")


@app.get("/api/intro")
async def intro():
    agent = _require_agent()
    try:
        text = agent.get_intro()
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(req: ChatRequest):
    agent = _require_agent()
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Mensagem não pode ser vazia.")
    try:
        result = agent.chat(req.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/limpar")
async def limpar():
    agent = _require_agent()
    agent.clear_history()
    return {"ok": True}


@app.get("/api/status")
async def status():
    agent = _require_agent()
    return agent.get_status()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
