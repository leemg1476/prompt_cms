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
    loaded = prompt_store.load_all_from_yaml()
    if loaded == 0:
        # Bootstraps one prompt file so the agent starts with a valid YAML-backed prompt.
        path = prompt_store.write_prompt_yaml(
            prompt_key="default.system",
            version=1,
            checksum="bootstrapped",
            content="SYSTEM: You are a test LangGraph agent.",
            variables_schema=None,
        )
        prompt_store.load_prompt_yaml_file(path)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(internal_push_router)
app.include_router(agent_router)
