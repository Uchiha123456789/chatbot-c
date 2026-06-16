import sys
from pathlib import Path

# Cho phép `from services... / from models...` khi chạy `pytest tests/` từ thư mục gốc dự án.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
