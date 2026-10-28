from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # Auth
    JWT_SECRET: str
    JWT_ACCESS_EXPIRES_MINUTES: int = 60
    JWT_REFRESH_EXPIRES_DAYS: int = 30

    # Database
    DATABASE_URL: str
    DIRECT_URL: str | None = None

    # Supabase Storage
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_STORAGE_BUCKET_CONDITIONS: str = "condition-photos"
    SUPABASE_STORAGE_BUCKET_DOCS: str = "verification-docs"
    SUPABASE_STORAGE_BUCKET_CONTRACTS: str = "contracts"

    # Upstash Redis
    UPSTASH_REDIS_URL: str
    UPSTASH_REDIS_TOKEN: str

    # AI Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_CACHE_TTL: int = 86400

    # Resend
    RESEND_API_KEY: str
    RESEND_FROM_EMAIL: str = "notifications@availo.app"

    # Fair-use limits
    MAX_ACTIVE_BOOKINGS_PER_USER: int = 3
    MAX_BOOKINGS_PER_RESOURCE_PER_WEEK: int = 2
    WAITLIST_AUTO_PROMOTE_MINUTES: int = 30

    # Demo credentials
    DEMO_USER_PASSWORD: str = "DemoUser@Availo"
    DEMO_OWNER_PASSWORD: str = "DemoOwner@Availo"
    DEMO_ADMIN_PASSWORD: str = "DemoAdmin@Availo"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
