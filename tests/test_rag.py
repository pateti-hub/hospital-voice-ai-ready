from app.services.rag import reciprocal_rank_fusion, tokenize


def test_tokenize():
    assert tokenize("The cardiology appointment") == {"cardiology", "appointment"}


def test_rrf_rewards_overlap():
    a = [{"id": "a"}, {"id": "b"}]
    b = [{"id": "b"}, {"id": "c"}]
    assert reciprocal_rank_fusion(a, b)[0]["id"] == "b"
