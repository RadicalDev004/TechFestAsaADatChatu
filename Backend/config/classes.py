from pathlib import Path
from typing import Optional

from pydantic import (SecretStr,
                      Field,
                      model_validator,
                      PositiveInt)
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseSettings):
    model: str = "gpt-5-mini"
    temperature: Optional[float] = Field(default=0.5, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_tokens: PositiveInt = 2100
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def check_exclusivity(self):
        """
        Enforce using at most one of temperature or top_p.
        If both are explicitly set (not None), raise.
        """
        if self.temperature is not None and self.top_p is not None:
            raise ValueError("Use only one: temperature OR top_p (set the other to None).")
        return self
