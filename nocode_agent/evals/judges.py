from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from nocode_agent.llm import structured_call

GROUNDEDNESS_SYSTEM = (
    "You judge whether an answer is grounded in the supplied documentation excerpts.\n"
    "Score 1.0 when every claim in the answer is supported by the excerpts, 0.5 when some claims are unsupported\n"
    "or the answer adds details that are not in the excerpts, and 0.0 when the answer contradicts the excerpts or\n"
    "is mostly unsupported. An answer that correctly says the excerpts do not contain the answer is grounded."
)

CORRECTNESS_SYSTEM = (
    "You compare a model answer with a reference answer for a question about a no-code platform API.\n"
    "Score 1.0 when the answer states the same facts as the reference, 0.5 when it is partially right or leaves out\n"
    "part of the reference, and 0.0 when it is wrong or does not answer. Ignore wording and formatting differences."
)


class Verdict(BaseModel):
    score: float = Field(ge=0, le=1)
    reasoning: str = Field(default="")


def format_contexts(contexts: list[str]) -> str:
    return "\n\n".join(f"[{index}] {text}" for index, text in enumerate(contexts, start=1)) or "(no excerpts)"


def judge_groundedness(llm: Any, answer: str, contexts: list[str]) -> Verdict:
    prompt = f"Documentation excerpts:\n{format_contexts(contexts)}\n\nAnswer to judge:\n{answer}"
    return structured_call(llm, Verdict, GROUNDEDNESS_SYSTEM, prompt)


def judge_correctness(llm: Any, question: str, answer: str, reference: str) -> Verdict:
    prompt = f"Question: {question}\nReference answer: {reference}\nModel answer: {answer}"
    return structured_call(llm, Verdict, CORRECTNESS_SYSTEM, prompt)
