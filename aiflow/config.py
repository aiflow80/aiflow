import os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import yaml

@dataclass
class WebSocketConfig:
    host: str = "localhost"
    port: int = 8888
    retry_max_attempts: int = 5
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0
    connection_timeout: float = 10.0
    max_connections: int = 100
    keepalive_interval: float = 30.0
    development_mode: bool = True

@dataclass
class SecurityConfig:
    allowed_origins: Optional[List[str]] = field(default_factory=list)
    ssl_cert_path: str = ""
    ssl_key_path: str = ""
    token_secret: str = ""
    enable_cors: bool = True

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    file_path: str = "aiflow.log"
    max_size: int = 10485760  # 10MB
    backup_count: int = 5

@dataclass
class Config:
    websocket: WebSocketConfig = field(default_factory=WebSocketConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    @classmethod
    def load(cls, config_path: str = None) -> 'Config':
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return cls._from_dict(config_data)
        return cls()

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'Config':
        ws_config = WebSocketConfig(**data.get('websocket', {}))
        security_config = SecurityConfig(**data.get('security', {}))
        logging_config = LoggingConfig(**data.get('logging', {}))
        return cls(
            websocket=ws_config,
            security=security_config,
            logging=logging_config
        )

# Global configuration instance
config = Config.load()
