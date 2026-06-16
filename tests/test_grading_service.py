"""Test cho grading_service — chiến lược chấm điểm hybrid theo loại câu hỏi.

Không phụ thuộc DB/HTTP/Ollama: dùng embed_fn giả lập (vector cố định) để
kiểm tra logic cosine similarity / kết hợp điểm thành phần một cách tất định.
"""
import json

import pytest

from services.grading_service import (
    _cosine_similarity,
    _normalize,
    grade_answer,
    grade_code,
    grade_mcq,
    grade_short_answer,
)

# embed_fn giả: ánh xạ một số câu cố định sang vector đã biết trước,
# để cosine similarity có thể tính tay và so sánh chính xác.
_FAKE_VECTORS = {
    "vòng lặp for": [1.0, 0.0],
    "for loop": [1.0, 0.0],
    "con trỏ": [0.0, 1.0],
}


def fake_embed(text: str) -> list[float]:
    return _FAKE_VECTORS.get(_normalize(text), [0.5, 0.5])


def test_normalize_collapses_whitespace_and_case():
    assert _normalize("  Vòng   Lặp\nFOR  ") == "vòng lặp for"


def test_cosine_similarity_identical_vectors_is_one():
    assert _cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors_is_zero():
    assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector_is_zero_not_nan():
    assert _cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


# --- MCQ -------------------------------------------------------------------

def test_grade_mcq_exact_match_scores_full():
    score, detail = grade_mcq("do-while", "do-while")
    assert score == 1.0
    assert detail["correct"] is True


def test_grade_mcq_case_and_whitespace_insensitive():
    score, _ = grade_mcq("  Do-While ", "do-while")
    assert score == 1.0


def test_grade_mcq_wrong_answer_scores_zero():
    score, detail = grade_mcq("while", "do-while")
    assert score == 0.0
    assert detail["correct"] is False


def test_grade_mcq_missing_reference_scores_zero():
    score, _ = grade_mcq("do-while", None)
    assert score == 0.0


# --- short_answer -----------------------------------------------------------

def test_grade_short_answer_combines_keyword_and_embedding_components():
    rubric = {"keywords": ["vòng lặp", "điều kiện"]}
    score, detail = grade_short_answer("Vòng lặp for", "vòng lặp for", rubric, fake_embed)

    # keyword: chỉ "vòng lặp" khớp -> 1/2 = 0.5 ; embedding: cùng vector -> similarity 1.0
    assert detail["keywords"]["matched"] == ["vòng lặp"]
    assert detail["keywords"]["score"] == pytest.approx(0.5)
    assert detail["embedding_similarity"] == pytest.approx(1.0)
    assert score == pytest.approx((0.5 + 1.0) / 2)


def test_grade_short_answer_without_keywords_uses_embedding_only():
    score, detail = grade_short_answer("con trỏ", "con trỏ", {}, fake_embed)
    assert "keywords" not in detail
    assert score == pytest.approx(1.0)


def test_grade_short_answer_no_signal_scores_zero():
    score, detail = grade_short_answer("không biết", None, {}, fake_embed)
    assert score == 0.0
    assert detail["score"] == 0.0


# --- code (static checks, không cần gcc) ------------------------------------

def test_grade_code_all_required_patterns_present_scores_full():
    rubric = {"required_patterns": ["for", "printf"]}
    code = "for (int i = 0; i < 5; i++) { printf(\"%d\", i); }"
    score, detail = grade_code(code, rubric)
    assert score == 1.0
    assert detail["structure"]["matched"] == ["for", "printf"]
    assert detail["structure"]["missing"] == []


def test_grade_code_partial_patterns_scores_proportionally():
    rubric = {"required_patterns": ["for", "while", "scanf"]}
    code = "for (int i = 0; i < 5; i++) { printf(\"%d\", i); }"
    score, detail = grade_code(code, rubric)
    assert score == pytest.approx(1 / 3)
    assert detail["structure"]["matched"] == ["for"]
    assert set(detail["structure"]["missing"]) == {"while", "scanf"}


def test_grade_code_without_rubric_scores_zero():
    score, detail = grade_code("int main() { return 0; }", {})
    assert score == 0.0
    assert detail["score"] == 0.0


# --- grade_answer (điểm vào duy nhất) ---------------------------------------

def test_grade_answer_dispatches_by_question_type():
    score, _ = grade_answer("mcq", "do-while", "do-while", None, fake_embed)
    assert score == 1.0


def test_grade_answer_parses_rubric_json_string():
    rubric_json = json.dumps({"required_patterns": ["for"]})
    score, detail = grade_answer("code", "for (;;) {}", None, rubric_json, fake_embed)
    assert score == 1.0
    assert detail["structure"]["matched"] == ["for"]


def test_grade_answer_unknown_type_raises():
    with pytest.raises(ValueError):
        grade_answer("essay", "...", None, None, fake_embed)
