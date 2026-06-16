"""Benchmark thủ công: chạy bộ câu hỏi mẫu qua RagService và lưu kết quả ra JSON."""
import json
import sys
from datetime import datetime

from services.rag_service import get_rag_service

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def main():
    rag = get_rag_service()

    with open("test_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    results = []
    print(f"Bắt đầu test {len(questions)} câu hỏi...\n")
    print("=" * 60)

    for idx, item in enumerate(questions):
        question = item["question"]
        topic = item["topic"]
        print(f"[{idx+1}/{len(questions)}] {question}")

        answer, chunk_ids = rag.ask(question)
        print(f"Trả lời: {answer[:200]}...\n")

        results.append({
            "stt": idx + 1,
            "topic": topic,
            "question": question,
            "answer": answer,
            "retrieved_chunk_ids": chunk_ids,
        })

    output_file = f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print(f"XONG! Kết quả lưu tại: {output_file}")


if __name__ == "__main__":
    main()
