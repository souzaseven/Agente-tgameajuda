from fastapi import Depends, UploadFile, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os
from tools import KNOWLEDGE_DIR, PERGUNTAS_NAO_RESPONDIDAS

security = HTTPBasic()
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USER)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas", headers={"WWW-Authenticate": "Basic"})
    return credentials.username
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
# Servir favicon
@app.get("/favicon.ico")
async def favicon():
    return FileResponse(TEMPLATES_DIR / "favicon.ico")


# Rotas administrativas para base de conhecimento
@app.get("/admin/knowledge", tags=["admin"])
async def list_knowledge_files(user: str = Depends(get_current_admin)):
    files = [f.name for f in KNOWLEDGE_DIR.glob("*.txt")]
    return {"arquivos": files}

@app.post("/admin/knowledge/upload", tags=["admin"])
async def upload_knowledge_file(file: UploadFile, user: str = Depends(get_current_admin)):
    dest = KNOWLEDGE_DIR / file.filename
    with open(dest, "wb") as f:
        f.write(await file.read())
    return {"ok": True, "arquivo": file.filename}

@app.get("/admin/knowledge/perguntas_sem_resposta", tags=["admin"])
async def listar_perguntas_sem_resposta(user: str = Depends(get_current_admin)):
    if not PERGUNTAS_NAO_RESPONDIDAS.exists():
        return {"perguntas": []}
    with open(PERGUNTAS_NAO_RESPONDIDAS, encoding="utf-8") as f:
        perguntas = [linha.strip() for linha in f if linha.strip()]
    return {"perguntas": perguntas}


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
