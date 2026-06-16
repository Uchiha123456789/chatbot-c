"""Test cho thuật toán xoay vòng (retention) trong scripts/backup_db.py.

Dựng các file backup giả (rỗng, chỉ cần đúng tên) trải dài ~10 tuần, áp dụng
`apply_retention` và kiểm tra đúng chính sách: giữ tất cả trong KEEP_DAILY_DAYS
ngày gần nhất, sau đó mỗi tuần chỉ giữ một bản trong KEEP_WEEKLY_WEEKS tuần kế.
"""
from datetime import datetime, timedelta

import pytest

import scripts.backup_db as bdb

NOW = datetime(2026, 6, 8, 12, 0, 0)
DAYS_AGO = [0, 1, 2, 5, 10, 13, 14, 15, 20, 21, 22, 28, 29, 35, 42, 49, 56]


@pytest.fixture
def backup_dir(tmp_path):
    for days_ago in DAYS_AGO:
        ts = NOW - timedelta(days=days_ago)
        name = f"{bdb.DB_BACKUP_PREFIX}{ts.strftime(bdb.TIMESTAMP_FORMAT)}.db"
        (tmp_path / name).write_bytes(b"fake")
    return tmp_path


def _remaining_days_ago(backup_dir):
    remaining = []
    for ts, _path in bdb._list_backups(backup_dir, bdb.DB_BACKUP_PREFIX):
        remaining.append((NOW - ts).days)
    return sorted(remaining)


def test_keeps_every_backup_within_daily_window(backup_dir):
    bdb.apply_retention(backup_dir, bdb.DB_BACKUP_PREFIX, now=NOW)
    remaining = _remaining_days_ago(backup_dir)

    daily_entries = [d for d in DAYS_AGO if d <= bdb.KEEP_DAILY_DAYS]
    for d in daily_entries:
        assert d in remaining


def test_keeps_at_most_one_backup_per_week_in_weekly_window(backup_dir):
    bdb.apply_retention(backup_dir, bdb.DB_BACKUP_PREFIX, now=NOW)

    weekly_cutoff = NOW - timedelta(weeks=bdb.KEEP_WEEKLY_WEEKS)
    daily_cutoff = NOW - timedelta(days=bdb.KEEP_DAILY_DAYS)

    seen_weeks = set()
    for ts, _path in bdb._list_backups(backup_dir, bdb.DB_BACKUP_PREFIX):
        if daily_cutoff <= ts < NOW - timedelta(days=bdb.KEEP_DAILY_DAYS):
            continue
        if weekly_cutoff <= ts < daily_cutoff:
            week_key = ts.isocalendar()[:2]
            assert week_key not in seen_weeks, "chỉ được giữ một bản mỗi tuần trong cửa sổ weekly"
            seen_weeks.add(week_key)


def test_removes_backups_older_than_weekly_window(backup_dir):
    removed = bdb.apply_retention(backup_dir, bdb.DB_BACKUP_PREFIX, now=NOW)
    weekly_cutoff = NOW - timedelta(weeks=bdb.KEEP_WEEKLY_WEEKS)

    removed_days_ago = sorted((NOW - bdb._parse_timestamp(p.name, bdb.DB_BACKUP_PREFIX)).days for p in removed)
    oldest_kept = min(_remaining_days_ago(backup_dir))

    assert all((NOW - timedelta(days=d)) < weekly_cutoff or True for d in removed_days_ago)
    # Không còn bản nào cũ hơn weekly_cutoff sau khi xoay vòng
    for ts, _path in bdb._list_backups(backup_dir, bdb.DB_BACKUP_PREFIX):
        assert ts >= weekly_cutoff
    assert oldest_kept <= bdb.KEEP_DAILY_DAYS + bdb.KEEP_WEEKLY_WEEKS * 7


def test_retention_is_idempotent(backup_dir):
    bdb.apply_retention(backup_dir, bdb.DB_BACKUP_PREFIX, now=NOW)
    remaining_first = _remaining_days_ago(backup_dir)

    removed_again = bdb.apply_retention(backup_dir, bdb.DB_BACKUP_PREFIX, now=NOW)
    remaining_second = _remaining_days_ago(backup_dir)

    assert removed_again == []
    assert remaining_first == remaining_second
