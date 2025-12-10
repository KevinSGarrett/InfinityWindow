from app.llm.retrieval_strategies import (
    RetrievalKind,
    get_retrieval_profile,
)


def test_retrieval_profile_defaults(monkeypatch) -> None:
    for key in (
        "RETRIEVAL_MESSAGES_TOP_K",
        "RETRIEVAL_DOCS_TOP_K",
        "RETRIEVAL_MEMORY_TOP_K",
        "RETRIEVAL_TASKS_TOP_K",
    ):
        monkeypatch.delenv(key, raising=False)

    assert get_retrieval_profile(RetrievalKind.DEFAULT).top_k == 5
    assert get_retrieval_profile(RetrievalKind.MESSAGES).top_k == 7
    assert get_retrieval_profile(RetrievalKind.DOCS).top_k == 9
    assert get_retrieval_profile(RetrievalKind.MEMORY).top_k == 4
    assert get_retrieval_profile(RetrievalKind.TASKS).top_k == 3


def test_retrieval_profile_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("RETRIEVAL_MESSAGES_TOP_K", "11")
    monkeypatch.setenv("RETRIEVAL_MESSAGES_SCORE_THRESHOLD", "0.42")

    profile = get_retrieval_profile("messages")
    assert profile.top_k == 11
    assert profile.score_threshold == 0.42

    # Ensure other kinds fall back when not set
    monkeypatch.delenv("RETRIEVAL_DOCS_TOP_K", raising=False)
    assert get_retrieval_profile("docs").top_k == 9

