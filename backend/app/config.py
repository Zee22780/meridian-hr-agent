from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# libpq-only connection params. Neon appends these to the connection strings it
# hands out, but asyncpg rejects them as unexpected keyword arguments. SSL is
# enforced via connect_args in app/db/session.py instead.
LIBPQ_ONLY_PARAMS = {"sslmode", "channel_binding"}


class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str
    openai_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignore unrecognized keys rather than rejecting them. pydantic-settings
        # forbids extras by default, which would turn any stale leftover in a
        # local .env (e.g. the retired SUPABASE_* keys) into a boot failure.
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        # Accept plain postgresql:// or postgres:// and upgrade to asyncpg
        for prefix in ("postgresql://", "postgres://"):
            if v.startswith(prefix):
                v = "postgresql+asyncpg://" + v[len(prefix):]
                break

        # Strip libpq-only params so asyncpg.connect() never sees them
        parts = urlsplit(v)
        if parts.query:
            kept = [
                (key, value)
                for key, value in parse_qsl(parts.query, keep_blank_values=True)
                if key.lower() not in LIBPQ_ONLY_PARAMS
            ]
            v = urlunsplit(parts._replace(query=urlencode(kept)))

        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
