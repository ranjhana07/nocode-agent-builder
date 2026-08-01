from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from nocode_agent.llm import structured_call

SYSTEM = (
    "You rewrite search queries for a documentation index about a no-code platform with API workflows "
    "such as create_app, create_table and publish_site. Produce short alternative phrasings that use "
    "different vocabulary but keep the meaning. Do not answer the question."
)


class QueryVariants(BaseModel):
    queries: list[str] = Field(description="Alternative phrasings of the original query")


def expand_query(llm: BaseChatModel, query: str, count: int = 3) -> list[str]:
    try:
        variants = structured_call(llm, QueryVariants, SYSTEM, f"Original query: {query}\nWrite {count} alternatives.")
    except Exception:
        return [query]
    seen = {query.strip().lower()}
    queries = [query]
    for variant in variants.queries:
        cleaned = variant.strip()
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            queries.append(cleaned)
        if len(queries) == count + 1:
            break
    return queries
