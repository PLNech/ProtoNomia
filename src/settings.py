"""
ProtoNomia settings module.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pydantic.types import ImportString
from typing import Any, Callable

# Default Language Model to use
DEFAULT_LM = "gemma3:4b"  # Can be changed to gemma:7b or other available Ollama models

# LLM API settings
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_TIMEOUT = 30  # seconds
LLM_MAX_RETRIES = 10


class Settings(BaseSettings):
    agent_first_day_dark_triad: bool = False
    # auth_key: str = Field(validation_alias='my_auth_key')  
    # api_key: str = Field(alias='my_api_key')  

    # redis_dsn: RedisDsn = Field(
    #     'redis://user:pass@localhost:6379/1',
    #     validation_alias=AliasChoices('service_redis_dsn', 'redis_url'),  
    # )
    # pg_dsn: PostgresDsn = 'postgres://user:pass@localhost:5432/foobar'
    # amqp_dsn: AmqpDsn = 'amqp://user:pass@localhost:5672/'

    # special_function: ImportString[Callable[[Any], Any]] = 'math.cos'  

    # # to override domains:
    # # export my_prefix_domains='["foo.com", "bar.com"]'
    # domains: set[str] = set()

    # # to override more_settings:
    # # export my_prefix_more_settings='{"foo": "x", "apple": 1}'
    # more_settings: SubModel = SubModel()

    # model_config = SettingsConfigDict(env_prefix='my_prefix_')  

settings = Settings()
