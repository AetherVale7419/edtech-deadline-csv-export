from datetime import date, timedelta

from export_service import Learner, build_rows, export_report


class FakeClient:
    def __init__(self):
        self.deleted = []

    def storage_bucket_create(self, name):
        return {}
    def storage_bucket_delete(self, bucket):
        self.deleted.append(("bucket", bucket))
    def storage_object_put(self, bucket, key, content_type, data):
        return {}
    def storage_object_delete(self, bucket, key):
        self.deleted.append(("object", bucket, key))
    def storage_object_presign(self, bucket, key, expires_seconds=900):
        return {"url": "https://download.example/report.csv"}
    def pdf_generate(self, markdown):
        return {"url": "https://download.example/report.pdf"}


def test_deadline_decision_and_export_link():
    today = date(2026, 9, 12)
    learners = [Learner("1", "A", False, today - timedelta(days=1)), Learner("2", "B", False, today)]
    rows = build_rows("Course", learners, today)
    assert [row["status"] for row in rows] == ["overdue", "open"]
    client = FakeClient()
    report = export_report("Course", learners, client, today)
    assert report["download_url"].startswith("https://download.example/")
    assert client.deleted == [
        ("object", "edtech-reports", "course-2026-09-12.csv"),
        ("bucket", "edtech-reports"),
    ]
