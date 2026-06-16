def chunk_text(text: str, chunk_size: int = 300, overlap: int = 30) -> list[str]:
    """Chia văn bản thành các đoạn theo cửa sổ trượt tính bằng số từ.

    chunk_size: số từ mỗi đoạn; overlap: số từ chồng lấp giữa hai đoạn liên tiếp
    (giữ ngữ cảnh ở ranh giới đoạn).
    """
    words = text.split()
    chunks, i = [], 0
    step = chunk_size - overlap
    while i < len(words):
        chunks.append(" ".join(words[i:i + chunk_size]))
        i += step
    return chunks
