from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.agent import router as agent_router
from app.routers.internal_push import router as internal_push_router
from app.services.store import prompt_store

app = FastAPI(title="LangGraph Test Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def bootstrap_prompt() -> None:
    # Bootstraps one prompt so /api/agent/run can be tested immediately.
    prompt_store.upsert(
        prompt_key="default.system",
        version=1,
        checksum="bootstrapped",
        content="SYSTEM: You are a test LangGraph agent.",
        variables_schema=None,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(internal_push_router)
app.include_router(agent_router)
