from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
 app_env: str = "development"
 frontend_origin: str = "http://localhost:3000"
 openai_api_key: str = ""
 openai_model: str = "gpt-5"
 broker_encryption_key: str = ""
 ctrader_client_id: str = ""
 ctrader_client_secret: str = ""
 ctrader_redirect_uri: str = ""
 model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()
