"""Sao lưu CSDL SQLite (+ tuỳ chọn vector store Chroma) — Giai đoạn 5.

Dùng Online Backup API của sqlite3 (`Connection.backup()`): chụp ảnh nhất quán
của CSDL ngay cả khi ứng dụng đang chạy và ghi dữ liệu (khác với copy file thô,
có thể chụp giữa lúc đang ghi và tạo ra file hỏng).

Sau khi sao lưu xong, áp dụng thuật toán xoay vòng (rotation) theo tầng để giữ
số lượng bản sao lưu ở mức hợp lý:
  - Giữ TẤT CẢ bản sao lưu trong KEEP_DAILY_DAYS ngày gần nhất
  - Với các bản cũ hơn, mỗi tuần chỉ giữ lại bản sớm nhất, trong KEEP_WEEKLY_WEEKS tuần
  - Xoá phần còn lại

Chạy: python scripts/backup_db.py [--with-chroma]
"""
import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import settings  # noqa: E402

BACKUP_DIR = ROOT_DIR / "backups"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
DB_BACKUP_PREFIX = "app_"
CHROMA_BACKUP_PREFIX = "chroma_"

KEEP_DAILY_DAYS = 14
KEEP_WEEKLY_WEEKS = 4


def backup_sqlite(db_path: Path, dest_path: Path) -> None:
    """Chụp ảnh nhất quán bằng Online Backup API — an toàn khi app đang ghi DB.

    CSDL gốc chạy ở chế độ WAL (xem database.py), nên trang tiêu đề được sao
    chép cũng mang cờ WAL — nếu giữ nguyên, bản sao lưu sẽ kéo theo các file
    phụ trợ `-wal`/`-shm` và không còn là một file độc lập. Sau khi backup,
    chuyển bản sao lưu sang `journal_mode=DELETE` (rollback journal mặc định)
    rồi VACUUM để gộp mọi thứ về đúng một file `.db` duy nhất, dễ lưu trữ/di chuyển.
    """
    source = sqlite3.connect(str(db_path))
    dest = sqlite3.connect(str(dest_path))
    try:
        with dest:
            source.backup(dest)
        dest.execute("PRAGMA journal_mode=DELETE")
        dest.execute("VACUUM")
    finally:
        dest.close()
        source.close()


def backup_chroma(chroma_dir: Path, dest_zip_base: Path) -> Path:
    """Nén thư mục chroma_db/ thành file .zip — KHÔNG chạy đồng thời với ingest.py
    (tránh chụp giữa lúc thư mục đang ở trạng thái nửa vời)."""
    archive_path = shutil.make_archive(str(dest_zip_base), "zip", root_dir=str(chroma_dir))
    return Path(archive_path)


def _parse_timestamp(name: str, prefix: str) -> datetime | None:
    if not name.startswith(prefix):
        return None
    stem = Path(name).stem  # bỏ đuôi .db / .zip
    raw = stem[len(prefix):]
    try:
        return datetime.strptime(raw, TIMESTAMP_FORMAT)
    except ValueError:
        return None


def _list_backups(backup_dir: Path, prefix: str) -> list[tuple[datetime, Path]]:
    items = []
    for path in backup_dir.iterdir():
        ts = _parse_timestamp(path.name, prefix)
        if ts is not None:
            items.append((ts, path))
    items.sort(key=lambda pair: pair[0], reverse=True)
    return items


def apply_retention(backup_dir: Path, prefix: str, *, now: datetime | None = None) -> list[Path]:
    """Áp dụng xoay vòng theo tầng (daily + weekly), trả về danh sách file đã xoá."""
    now = now or datetime.now()
    daily_cutoff = now - timedelta(days=KEEP_DAILY_DAYS)
    weekly_cutoff = now - timedelta(weeks=KEEP_WEEKLY_WEEKS)

    backups = _list_backups(backup_dir, prefix)
    keep: set[Path] = set()
    seen_weeks: set[tuple[int, int]] = set()

    for ts, path in backups:
        if ts >= daily_cutoff:
            keep.add(path)
            continue
        if ts >= weekly_cutoff:
            week_key = ts.isocalendar()[:2]
            if week_key not in seen_weeks:
                seen_weeks.add(week_key)
                keep.add(path)
        # cũ hơn weekly_cutoff → không giữ

    removed = []
    for _ts, path in backups:
        if path not in keep:
            path.unlink()
            removed.append(path)
    return removed


def run_backup(*, with_chroma: bool = False, now: datetime | None = None) -> dict:
    now = now or datetime.now()
    timestamp = now.strftime(TIMESTAMP_FORMAT)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    db_path = Path(settings.db_path)
    db_dest = BACKUP_DIR / f"{DB_BACKUP_PREFIX}{timestamp}.db"
    print(f"Sao lưu CSDL {db_path} -> {db_dest} (Online Backup API)...")
    backup_sqlite(db_path, db_dest)
    removed_db = apply_retention(BACKUP_DIR, DB_BACKUP_PREFIX, now=now)

    result = {"db_backup": db_dest, "removed_db_backups": removed_db}

    if with_chroma:
        chroma_dir = Path(settings.chroma_dir)
        chroma_dest_base = BACKUP_DIR / f"{CHROMA_BACKUP_PREFIX}{timestamp}"
        print(f"Nén vector store {chroma_dir} -> {chroma_dest_base}.zip...")
        chroma_zip = backup_chroma(chroma_dir, chroma_dest_base)
        removed_chroma = apply_retention(BACKUP_DIR, CHROMA_BACKUP_PREFIX, now=now)
        result["chroma_backup"] = chroma_zip
        result["removed_chroma_backups"] = removed_chroma

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Sao lưu CSDL SQLite (+ tuỳ chọn Chroma)")
    parser.add_argument(
        "--with-chroma",
        action="store_true",
        help="Đồng thời nén thư mục chroma_db/ — KHÔNG dùng khi ingest.py đang chạy",
    )
    args = parser.parse_args()

    result = run_backup(with_chroma=args.with_chroma)

    print(f"\nĐã tạo: {result['db_backup']}")
    if result["removed_db_backups"]:
        print(f"Đã xoá {len(result['removed_db_backups'])} bản CSDL cũ (ngoài chính sách lưu trữ):")
        for path in result["removed_db_backups"]:
            print(f"  - {path.name}")

    if "chroma_backup" in result:
        print(f"Đã tạo: {result['chroma_backup']}")
        if result["removed_chroma_backups"]:
            print(f"Đã xoá {len(result['removed_chroma_backups'])} bản Chroma cũ:")
            for path in result["removed_chroma_backups"]:
                print(f"  - {path.name}")

    print("\nHoàn tất sao lưu.")


if __name__ == "__main__":
    main()
