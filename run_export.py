from datetime import date, timedelta

from export_service import Learner, export_report
from infrai_client import InfraiClient


if __name__ == "__main__":
    today = date(2026, 9, 12)
    learners = [
        Learner("l-100", "Ava Chen", True, today - timedelta(days=2)),
        Learner("l-101", "Noah Singh", False, today + timedelta(days=3)),
    ]
    result = export_report("Python Foundations", learners, InfraiClient(), today)
    print(result["download_url"])
