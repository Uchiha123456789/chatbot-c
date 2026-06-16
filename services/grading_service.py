"""grading_service: chấm điểm bài làm theo loại câu hỏi (chiến lược hybrid).

Xem docs/claude/algorithms.md mục 2 để biết lý do thiết kế:
  - mcq:          so khớp chính xác với reference_answer
  - short_answer: kết hợp trùng từ khoá (grading_rubric.keywords) + cosine similarity
                  giữa embedding câu trả lời và embedding đáp án mẫu (tái dùng
                  RagService.embed_text — cùng pipeline embedding với RAG)
  - code:         kiểm tra cấu trúc tĩnh theo grading_rubric.required_patterns;
                  tuỳ chọn biên dịch & chạy trong sandbox (subprocess, timeout
                  chặt, thư mục tạm, không mạng) khi grading_rubric.run_check=true.
                  Phạm vi giới hạn ở snippet C tự chứa đơn giản — thực thi đầy đủ
                  trong container cách ly (Docker/seccomp) là hướng mở rộng.

Mỗi hàm chấm trả về (score ∈ [0,1], detail: dict) — detail được lưu nguyên vào
submissions.grading_detail (JSON) để minh bạch và có thể tái kiểm tra.
"""
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

CODE_RUN_TIMEOUT_SECONDS = 2
COMPILE_TIMEOUT_SECONDS = 5

EmbedFn = Callable[[str], list[float]]

# Token thường gặp trong grading_rubric.required_patterns -> regex tương ứng.
# Token không nằm trong bảng được coi là chuỗi cần xuất hiện nguyên văn (escape).
_REQUIRED_PATTERN_REGEX = {
    "for": r"\bfor\s*\(",
    "while": r"\bwhile\s*\(",
    "if": r"\bif\s*\(",
    "printf": r"\bprintf\s*\(",
    "scanf": r"\bscanf\s*\(",
    "return": r"\breturn\b",
    "include": r"#include",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _parse_rubric(grading_rubric_json: str | None) -> dict:
    if not grading_rubric_json:
        return {}
    try:
        rubric = json.loads(grading_rubric_json)
    except (TypeError, ValueError):
        return {}
    return rubric if isinstance(rubric, dict) else {}


def grade_mcq(student_answer: str, reference_answer: str | None) -> tuple[float, dict]:
    correct = bool(reference_answer) and _normalize(student_answer) == _normalize(reference_answer)
    score = 1.0 if correct else 0.0
    return score, {
        "method": "mcq_exact_match",
        "correct": correct,
        "expected": reference_answer,
        "received": student_answer,
    }


def grade_short_answer(
    student_answer: str,
    reference_answer: str | None,
    rubric: dict,
    embed_fn: EmbedFn,
) -> tuple[float, dict]:
    detail: dict = {"method": "short_answer_hybrid"}
    components: list[float] = []

    keywords = rubric.get("keywords") or []
    if keywords:
        normalized_answer = _normalize(student_answer)
        matched = [kw for kw in keywords if _normalize(kw) in normalized_answer]
        keyword_score = len(matched) / len(keywords)
        detail["keywords"] = {"expected": keywords, "matched": matched, "score": round(keyword_score, 3)}
        components.append(keyword_score)

    if reference_answer:
        try:
            similarity = _cosine_similarity(embed_fn(student_answer), embed_fn(reference_answer))
            similarity = max(0.0, min(1.0, similarity))
            detail["embedding_similarity"] = round(similarity, 3)
            components.append(similarity)
        except Exception as exc:
            detail["embedding_error"] = str(exc)

    score = sum(components) / len(components) if components else 0.0
    detail["score"] = round(score, 3)
    return score, detail


def _check_required_patterns(code: str, required: list[str]) -> tuple[list[str], list[str]]:
    matched, missing = [], []
    for token in required:
        pattern = _REQUIRED_PATTERN_REGEX.get(str(token).lower(), re.escape(str(token)))
        (matched if re.search(pattern, code) else missing).append(token)
    return matched, missing


def _compile_and_run(code: str, expected_output: str | None) -> dict:
    """Biên dịch & chạy snippet C trong thư mục tạm — timeout chặt, không mạng.

    Chỉ dành cho snippet tự chứa đơn giản (xem cảnh báo rủi ro trong algorithms.md).
    Không raise: mọi lỗi/timeout được mô tả trong dict trả về để không làm hỏng
    luồng chấm điểm tổng thể.
    """
    gcc = shutil.which("gcc")
    if gcc is None:
        return {"ran": False, "reason": "Không tìm thấy trình biên dịch gcc trên máy chủ — bỏ qua bước chạy thử"}

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        source_file = tmp_path / "submission.c"
        binary_file = tmp_path / "submission.out"
        source_file.write_text(code, encoding="utf-8")

        try:
            compiled = subprocess.run(
                [gcc, str(source_file), "-o", str(binary_file)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=COMPILE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return {"ran": False, "reason": "Biên dịch quá thời gian cho phép"}

        if compiled.returncode != 0:
            return {"ran": False, "reason": "Lỗi biên dịch", "compiler_output": compiled.stderr[-2000:]}

        try:
            executed = subprocess.run(
                [str(binary_file)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=CODE_RUN_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return {"ran": False, "reason": "Chạy chương trình quá thời gian cho phép"}

        actual_output = executed.stdout.strip()
        result: dict = {"ran": True, "exit_code": executed.returncode, "stdout": actual_output[:2000]}
        if expected_output is not None:
            result["expected_output"] = expected_output
            result["output_matches"] = _normalize(actual_output) == _normalize(expected_output)
        return result


def grade_code(student_answer: str, rubric: dict) -> tuple[float, dict]:
    detail: dict = {"method": "code_static_checks"}
    components: list[float] = []

    required = rubric.get("required_patterns") or []
    if required:
        matched, missing = _check_required_patterns(student_answer, required)
        structure_score = len(matched) / len(required)
        detail["structure"] = {
            "required": required,
            "matched": matched,
            "missing": missing,
            "score": round(structure_score, 3),
        }
        components.append(structure_score)

    if rubric.get("run_check"):
        run_detail = _compile_and_run(student_answer, rubric.get("expected_output"))
        detail["execution"] = run_detail
        if run_detail.get("ran"):
            components.append(1.0 if run_detail.get("output_matches", True) else 0.0)
        else:
            components.append(0.0)

    score = sum(components) / len(components) if components else 0.0
    detail["score"] = round(score, 3)
    return score, detail


def grade_answer(
    question_type: str,
    student_answer: str,
    reference_answer: str | None,
    grading_rubric_json: str | None,
    embed_fn: EmbedFn,
) -> tuple[float, dict]:
    """Điểm vào duy nhất — chọn chiến lược chấm theo question_type.

    Trả về (score ∈ [0,1], detail) để router lưu vào submissions (score, grading_detail).
    """
    rubric = _parse_rubric(grading_rubric_json)

    if question_type == "mcq":
        return grade_mcq(student_answer, reference_answer)
    if question_type == "short_answer":
        return grade_short_answer(student_answer, reference_answer, rubric, embed_fn)
    if question_type == "code":
        return grade_code(student_answer, rubric)

    raise ValueError(f"Loại câu hỏi không được hỗ trợ: {question_type}")
