from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    sec_user_agent: str = "SECAnalyzer admin@example.com"
    sec_base_url: str = "https://data.sec.gov"
    sec_efts_url: str = "https://efts.sec.gov"
    sec_www_url: str = "https://www.sec.gov"
    rate_limit_per_second: int = 8

    model_config = {"env_file": ".env"}


settings = Settings()
