import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    push_auth_token: str = "local-dev-token"
    prompt_yaml_dir: str = "./data/prompts"

    langsmith_tracing: bool = False
    langchain_tracing_v2: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "prompt-cms-agent"
    langsmith_endpoint: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


def apply_langsmith_env() -> None:
    os.environ["LANGSMITH_TRACING"] = "true" if settings.langsmith_tracing else "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if settings.langchain_tracing_v2 else "false"
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    if settings.langsmith_endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
