from __future__ import annotations

from typing import TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from nocode_agent.config import Settings, get_settings

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def build_chat_model(settings: Settings | None = None) -> BaseChatModel:
    settings = settings or get_settings()
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )


def structured_call(llm: BaseChatModel, schema: type[SchemaT], system: str, prompt: str) -> SchemaT:
    runnable = llm.with_structured_output(schema)
    result = runnable.invoke([SystemMessage(content=system), HumanMessage(content=prompt)])
    if isinstance(result, schema):
        return result
    return schema.model_validate(result)


def text_call(llm: BaseChatModel, system: str, prompt: str) -> str:
    reply = llm.invoke([SystemMessage(content=system), HumanMessage(content=prompt)])
    content = reply.content
    if isinstance(content, str):
        return content
    return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
