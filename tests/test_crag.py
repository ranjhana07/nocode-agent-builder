from __future__ import annotations

from nocode_agent.agent.crag import RewrittenQuery, build_crag_graph, interleave
from nocode_agent.agent.grader import ChunkGrade, GradeReport
from nocode_agent.rag.types import Chunk, ScoredChunk
from tests.fakes import FakeChat
from tests.graph_helpers import make_deps


def hits(*ids: str) -> list[ScoredChunk]:
    return [ScoredChunk(Chunk(identifier, f"text {identifier}", {"source": f"{identifier}.md"}), 1.0) for identifier in ids]


class ScriptedRetriever:
    def __init__(
        self,
        by_query: dict[str, list[ScoredChunk]],
        fallback: list[ScoredChunk] | None = None,
        wide: list[ScoredChunk] | None = None,
    ) -> None:
        self.by_query = by_query
        self.fallback = fallback or []
        self.wide = wide
        self.calls: list[tuple[str, bool]] = []

    def __call__(self, query: str, k: int, widen: bool) -> list[ScoredChunk]:
        self.calls.append((query, widen))
        if widen and self.wide is not None:
            return self.wide[:k]
        return self.by_query.get(query, self.fallback)[:k]


def report(*scores: float) -> GradeReport:
    return GradeReport(grades=[ChunkGrade(index=index, score=score) for index, score in enumerate(scores)])


def run(llm: FakeChat, retriever: ScriptedRetriever, **settings):
    deps = make_deps(llm, retriever=retriever, **settings)
    return build_crag_graph(deps).invoke({"query": "q", "original_query": "q"})


def test_good_context_proceeds_without_rewriting() -> None:
    retriever = ScriptedRetriever({"q": hits("a", "b")})
    llm = FakeChat({GradeReport: report(0.9, 0.8, 0.7, 0.1)})
    state = run(llm, retriever)
    assert state["grade_decision"] == "proceed"
    assert state["retrieval_attempts"] == 1
    assert llm.calls_for(RewrittenQuery) == 0
    assert [document["id"] for document in state["documents"]] == ["a", "b", "a"][: len(state["documents"])]


def test_irrelevant_context_rewrites_then_succeeds() -> None:
    retriever = ScriptedRetriever({"q": hits("bad1"), "better query": hits("good1", "good2")})
    llm = FakeChat(
        {
            GradeReport: [report(0.1, 0.0), report(0.9, 0.9, 0.8, 0.0)],
            RewrittenQuery: RewrittenQuery(query="better query"),
        }
    )
    state = run(llm, retriever)
    assert state["grade_decision"] == "proceed"
    assert state["retrieval_attempts"] == 2
    assert state["query"] == "better query"
    assert {document["id"] for document in state["documents"]} == {"good1", "good2"}


def test_partial_context_retrieves_again_with_wider_search() -> None:
    retriever = ScriptedRetriever({"q": hits("a")}, wide=hits("a", "b", "c"))
    llm = FakeChat({GradeReport: [report(0.9), report(0.9, 0.8, 0.7)]})
    state = run(llm, retriever)
    assert state["retrieval_attempts"] == 2
    assert [widen for _, widen in retriever.calls] == [False, False, True, True]
    assert state["grade_decision"] == "proceed"


def test_loop_gives_up_after_the_attempt_cap() -> None:
    retriever = ScriptedRetriever({}, fallback=hits("noise"))
    llm = FakeChat(
        {
            GradeReport: [report(0.0, 0.0)] * 5,
            RewrittenQuery: RewrittenQuery(query="still bad"),
        }
    )
    state = run(llm, retriever, max_retrieval_attempts=3)
    assert state["grade_decision"] == "give_up"
    assert state["retrieval_attempts"] == 3
    assert state["documents"] == []
    assert llm.calls_for(RewrittenQuery) == 2


def test_both_retrieval_agents_feed_the_merge() -> None:
    state = run(FakeChat({GradeReport: report(1, 1, 1, 1)}), ScriptedRetriever({"q": hits("a", "b")}))
    assert any("api-spec agent" in line for line in state["trace"])
    assert any("docs agent" in line for line in state["trace"])


def test_interleave_dedupes_and_alternates() -> None:
    first = [{"id": "s1"}, {"id": "s2"}, {"id": "shared"}]
    second = [{"id": "d1"}, {"id": "shared"}]
    assert [item["id"] for item in interleave(first, second)] == ["s1", "d1", "s2", "shared"]
