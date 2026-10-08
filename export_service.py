import csv
import io
from dataclasses import dataclass
from datetime import date

from infrai_client import InfraiClient, infrai


@dataclass(frozen=True)
class Learner:
    learner_id: str
    name: str
    completed: bool
    deadline: date


def build_rows(course: str, learners: list[Learner], today: date):
    rows = []
    for learner in learners:
        status = "complete" if learner.completed else ("overdue" if learner.deadline < today else "open")
        rows.append({"course": course, "learner_id": learner.learner_id, "learner": learner.name, "deadline": learner.deadline.isoformat(), "status": status})
    return rows


def export_report(course: str, learners: list[Learner], client: InfraiClient, today: date | None = None):
    today = today or date.today()
    rows = build_rows(course, learners, today)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["course", "learner_id", "learner", "deadline", "status"])
    writer.writeheader()
    writer.writerows(rows)
    bucket = "edtech-reports"
    key = f"{course.lower().replace(' ', '-')}-{today.isoformat()}.csv"
    infrai.storage.bucket.create(client, bucket)
    object_created = False
    try:
        infrai.storage.object.put(client, bucket, key, "text/csv", output.getvalue().encode())
        object_created = True
        signed = infrai.storage.object.presign(client, bucket, key)
        pdf = infrai.pdf.generate(client, f"# {course} report\n\nLearners: {len(rows)}\n")
        return {"rows": rows, "download_url": signed["url"], "pdf": pdf}
    finally:
        try:
            if object_created:
                infrai.storage.object.delete(client, bucket, key)
        finally:
            infrai.storage.bucket.delete(client, bucket)
