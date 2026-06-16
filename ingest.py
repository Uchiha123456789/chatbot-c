import os
import sys
import time

import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pypdf import PdfReader

from config import settings
from services.chunking import chunk_text

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PDF_PATH = os.environ.get("INGEST_PDF_PATH", "data/source/ky_thuat_lap_trinh_c.pdf")


def main():
    print("Đang đọc PDF...")
    reader = PdfReader(PDF_PATH)
    full_text = ""
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            full_text += f"\n--- Trang {i+1} ---\n" + text

    print(f"Tổng ký tự: {len(full_text)}")
    chunks = chunk_text(full_text)
    print(f"Số chunks: {len(chunks)}")

    print("Đang kết nối Google Generative AI...")
    embedding = GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key,
    )

    chroma_client = chromadb.PersistentClient(path=settings.chroma_dir)
    try:
        chroma_client.delete_collection(settings.chroma_collection)
    except Exception:
        pass
    collection = chroma_client.create_collection(settings.chroma_collection)

    batch_size = 10
    for i in range(0, len(chunks), batch_size):
        batch = [c[:1500] for c in chunks[i:i + batch_size]]
        ids = [f"doc_{j}" for j in range(i, i + len(batch))]
        for attempt in range(6):
            try:
                embeddings = embedding.embed_documents(batch)
                collection.add(embeddings=embeddings, documents=batch, ids=ids)
                print(f"Đã nạp chunk {i}..{i + len(batch) - 1}")
                break
            except Exception as e:
                wait = 10 * (attempt + 1)
                print(f"Lỗi ở batch {i} (lần {attempt + 1}/6): {e} — thử lại sau {wait}s")
                time.sleep(wait)
        else:
            print(f"Bỏ qua batch {i} sau 6 lần thử")
        time.sleep(3)

    print("\nHOÀN TẤT! ChromaDB đã sẵn sàng!")


if __name__ == "__main__":
    main()
