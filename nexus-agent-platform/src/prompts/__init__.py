"""NexusAgent Prompt 模板库 — Day 17"""

from prompts.base import PromptTemplate, extract_variables
from prompts.library import (
    BUILTIN_TEMPLATES,
    COMPLIANCE_REVIEW,
    DEFAULT_ASSISTANT,
    DOC_SUMMARY,
    PRODUCT_FAQ,
    RAG_QA,
)
from prompts.registry import PromptRegistry, default_registry

__all__ = [
    "PromptTemplate",
    "PromptRegistry",
    "default_registry",
    "extract_variables",
    "BUILTIN_TEMPLATES",
    "DEFAULT_ASSISTANT",
    "RAG_QA",
    "DOC_SUMMARY",
    "PRODUCT_FAQ",
    "COMPLIANCE_REVIEW",
]
