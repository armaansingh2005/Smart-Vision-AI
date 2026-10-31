import os
import time

from utils.helpers import cleanup_old_artifacts


def test_cleanup_removes_only_expired_generated_files(tmp_path):
    uploads = tmp_path / "uploads"
    results = tmp_path / "results"
    uploads.mkdir()
    results.mkdir()
    expired_upload = uploads / f"{'a' * 32}.jpg"
    expired_report = results / f"{'b' * 32}.json"
    recent_report = results / f"{'c' * 32}.json"
    unrelated = results / "notes.json"
    for path in (expired_upload, expired_report, recent_report, unrelated):
        path.write_text("test", encoding="utf-8")
    expired_time = time.time() - 8 * 24 * 60 * 60
    os.utime(expired_upload, (expired_time, expired_time))
    os.utime(expired_report, (expired_time, expired_time))

    cleanup_old_artifacts(uploads, results, retention_hours=168)

    assert not expired_upload.exists()
    assert not expired_report.exists()
    assert recent_report.exists()
    assert unrelated.exists()
