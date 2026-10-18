from pathlib import Path
from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)
    data_dir: Path = Field(Path("data"), alias="KAT_DATA_DIR")
    token_factory_base_url: str = Field("https://api.tokenfactory.nebius.com/v1",validation_alias=AliasChoices("TOKEN_FACTORY_BASE_URL","SUPER_BASE_URL"))
    token_factory_api_key: SecretStr = Field(SecretStr(""),validation_alias=AliasChoices("TOKEN_FACTORY_API_KEY","SUPER_API_KEY"))
    nemotron_agent_model: str = Field("nvidia/Nemotron-3.5-Super-VL",validation_alias=AliasChoices("NEMOTRON_AGENT_MODEL","SUPER_MODEL"))
    parse_api_url: str = "https://port8000-kh2kceraevwe0k1.tunnel.applications.uk-south2.nebius.cloud/v1/chat/completions"
    parse_base_url: str = ""
    parse_api_key: SecretStr = SecretStr("")
    parse_model: str = "nvidia/nemotron-3.5-parse"
    parse_prompt: str = "</s><s><predict_bbox><predict_classes><output_markdown><predict_text_in_pic>"
    wikipedia_api_url: str = "https://port8000-rks0xavparpzq59.tunnel.applications.uk-south2.nebius.cloud"
    wikipedia_mode: str = "shared"
    embed_api_url: str = ""
    embed_api_key: SecretStr = Field(SecretStr(""),validation_alias=AliasChoices("EMBED_API_KEY","RETRIEVAL_API_KEY"))
    embed_model: str = "nvidia/llama-nemotron-embed-vl-1b-v2"
    embed_protocol: str = "challenge"
    rerank_api_url: str = ""
    rerank_api_key: SecretStr = Field(SecretStr(""),validation_alias=AliasChoices("RERANK_API_KEY","RETRIEVAL_API_KEY"))
    rerank_model: str = "nvidia/llama-nemotron-rerank-vl-1b-v2"
    rerank_protocol: str = "challenge"
    latex_engine: str = "tectonic"
    retrieval_base_url: str = ""
    retrieval_image: str = ""
    hermes_repo_path: str = ""
    hermes_python: str = ""
    http_timeout: int = Field(120, alias="KAT_HTTP_TIMEOUT")
    fetch_candidates: int = Field(10, alias="KAT_FETCH_CANDIDATES", ge=1, le=30)

    @model_validator(mode="after")
    def starter_aliases(self):
        if self.parse_base_url:self.parse_api_url=self.parse_base_url.rstrip("/")+"/chat/completions"
        if self.retrieval_base_url:
            if not self.embed_api_url:self.embed_api_url=self.retrieval_base_url.rstrip("/")+"/embeddings"
            if not self.rerank_api_url:self.rerank_api_url=self.retrieval_base_url.rstrip("/")+"/rerank"
        return self

    def readiness(self) -> dict:
        return {
            "agent": {"required": "Nemotron 3.5 Super VL", "configured": bool(self.nemotron_agent_model and self.token_factory_api_key.get_secret_value()), "model": self.nemotron_agent_model},
            "parse": {"required": "Nemotron Parse 3.5", "configured": bool(self.parse_api_url and self.parse_model), "model": self.parse_model},
            "embed": {"required": "Nemotron Embed VL", "configured": bool(self.embed_api_url and self.embed_model), "model": self.embed_model},
            "rerank": {"required": "Nemotron Rerank VL", "configured": bool(self.rerank_api_url and self.rerank_model), "model": self.rerank_model},
            "hermes": {"required": "Hermes Agent", "configured": bool(self.hermes_repo_path and self.hermes_python)},
            "vector_database": {"required": "LanceDB", "configured": True},
        }

    def secrets(self) -> list[str]:
        return [s.get_secret_value() for s in [self.token_factory_api_key, self.parse_api_key, self.embed_api_key, self.rerank_api_key] if s.get_secret_value()]
