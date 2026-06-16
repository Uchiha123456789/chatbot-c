"""CLI smoke-test cho RagService — dùng để kiểm tra nhanh pipeline RAG mà không cần web server."""
import sys

from services.rag_service import get_rag_service

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def main():
    rag = get_rag_service()
    print("Chatbot dạy lập trình C đã sẵn sàng!")
    print("Gõ 'thoát' để kết thúc\n")

    history: list[dict] = []
    while True:
        question = input("Bạn hỏi: ")
        if question.lower() == "thoát":
            break
        answer, chunk_ids = rag.ask(question, history)
        print(f"\nChatbot: {answer}")
        print(f"(Ngữ cảnh dùng: {chunk_ids})\n")
        print("-" * 50)
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
