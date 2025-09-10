from pathlib import Path

from pydantic import (SecretStr,
                      Field,
                      model_validator,
                      PositiveInt)
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseSettings):
    model: str = "gpt-5-mini"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: PositiveInt = 1000
    presence_penalty: float = Field(default=1.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=1.0, ge=-2.0, le=2.0)
    api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def check_exclusivity(self):
        temp_active = self.temperature != 1.0
        top_p_active = self.top_p != 1.0
        if temp_active and top_p_active:
            raise ValueError(
                "You can only use one at a time: temperature OR top_p."
            )
        return self
