from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.db import engine
from app.models import Base
from app.routers.internal_push import router as internal_push_router
from app.routers.prompts import router as prompts_router
from app.routers.worker import router as worker_router

app = FastAPI(title="Prompt CMS Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(prompts_router)
app.include_router(worker_router)
app.include_router(internal_push_router)
