"""Khôi phục CSDL SQLite từ một bản sao lưu — Giai đoạn 5.

QUAN TRỌNG: dừng ứng dụng (uvicorn) trước khi chạy script này — restore trong
lúc app đang ghi DB có thể gây hỏng dữ liệu hoặc xung đột khoá file.

Quy trình (runbook):
  1. Kiểm tra file backup được chỉ định tồn tại và là CSDL SQLite hợp lệ
  2. Sao lưu "an toàn" bản hiện tại sang data/app.db.before_restore
     (phòng trường hợp chọn nhầm file — luôn có đường lùi)
  3. Copy file backup đè lên data/app.db
  4. In hướng dẫn khởi động lại ứng dụng để kiểm tra dữ liệu

Chạy: python scripts/restore_db.py backups/app_20260101_020000.db
"""
import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import settings  # noqa: E402

SAFETY_SUFFIX = ".before_restore"


def _is_valid_sqlite_db(path: Path) -> bool:
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            conn.execute("PRAGMA schema_version").fetchone()
            return True
        finally:
            conn.close()
    except sqlite3.Error:
        return False


def restore(backup_path: Path, db_path: Path) -> Path:
    """Thực hiện khôi phục, trả về đường dẫn file sao lưu an toàn đã tạo."""
    if not backup_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file sao lưu: {backup_path}")
    if not _is_valid_sqlite_db(backup_path):
        raise ValueError(f"File không phải CSDL SQLite hợp lệ: {backup_path}")

    safety_path = db_path.with_suffix(db_path.suffix + SAFETY_SUFFIX)
    if db_path.is_file():
        print(f"Sao lưu an toàn bản hiện tại: {db_path} -> {safety_path}")
        shutil.copy2(db_path, safety_path)

    print(f"Khôi phục: {backup_path} -> {db_path}")
    shutil.copy2(backup_path, db_path)
    return safety_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Khôi phục CSDL SQLite từ bản sao lưu")
    parser.add_argument("backup_file", help="Đường dẫn tới file backup (vd backups/app_20260101_020000.db)")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Bỏ qua xác nhận thủ công (dùng cho script tự động/CI)",
    )
    args = parser.parse_args()

    backup_path = Path(args.backup_file)
    db_path = Path(settings.db_path)

    print("!!! Hãy chắc chắn ứng dụng (uvicorn) đã được DỪNG trước khi tiếp tục !!!")
    print(f"Sẽ khôi phục: {backup_path}")
    print(f"Ghi đè lên : {db_path}")
    if not args.yes:
        answer = input("Tiếp tục? (gõ 'yes' để xác nhận): ").strip().lower()
        if answer != "yes":
            print("Đã huỷ — không có thay đổi nào được thực hiện.")
            return

    safety_path = restore(backup_path, db_path)

    print("\nHoàn tất khôi phục.")
    print(f"Bản trước khi khôi phục được giữ tại: {safety_path}")
    print("Tiếp theo: khởi động lại ứng dụng (uvicorn main:app) và kiểm tra dữ liệu.")


if __name__ == "__main__":
    main()
