"""NexusAgent 领域模型包"""

from core.exceptions import ModelValidationError
from models.contact import Contact
from models.llm_base import BaseModel
from models.message import ChatMessage
from models.model_config import ModelConfig

__all__ = [
    "BaseModel",
    "ModelValidationError",
    "ChatMessage",
    "Contact",
    "ModelConfig",
]
