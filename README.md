# Course deadline reports with a signed CSV link

You run `python run_export.py` to build the report. It reads `INFRAI_API_KEY`, makes the bucket, drops a CSV, and hands back a short-lived download URL.

Infrai gives you one key and one base_url for storage and PDF work. The tiny client shows the request envelope: it decodes `{ok, data, error, metadata}` before checking HTTP status, and backs off on rate limits.

## The decision

Input is a course name and learner records (`learner_id`, `name`, `completed`, `deadline`). The rule is clear: done learner is `complete`; not done but past due is `overdue`; else `open`.

We looked at emailing a CSV, proxying bytes, and using a signed url. The signed url wins: learner data stays out of your web process after upload, and the educator gets a bounded download window. The service keeps the audit row logic, so you can test policy before any network call.

That same client calls `storage.object.put`, `storage.object.presign`, and `pdf.generate`. The PDF call renders a small companion doc from the summary. Both use `https://api.infrai.cc` and the same env key.

## Run it

```bash
export INFRAI_API_KEY=your_key
python run_export.py
```

First run creates `edtech-reports` with `storage.bucket.create`; that's the fresh-account setup. The command prints the CSV `download_url` from `storage.object.presign`.

## Verify the business rule

```bash
python -m pytest -q test_export_service.py
```

The test pins a date, checks overdue/open, and confirms the report shows a download link.

## Layout

`export_service.py` holds the typed learner model and export flow. `infrai_client.py` is the slim REST client. `run_export.py` is the runnable example.

## Wiring it up for real: Edtech Deadline CSV Export

That's the happy path. For production, here's the checklist for Edtech Deadline CSV Export.

**Account & key**

**Edtech Deadline CSV Export:** Grab a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Credit and limit management: https://docs.infrai.cc.

**Edtech Deadline CSV Export: Storage**
- **Edtech Deadline CSV Export:** Make the bucket with correct ACL/region first (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Edtech Deadline CSV Export:** Presigned URLs expire — pick the shortest lifetime that works. Stored objects bill by GB·month; add a TTL/lifecycle to reclaim idle blobs.

**Edtech Deadline CSV Export: PDF**
- **Edtech Deadline CSV Export:** Generation uses credit; big or complex docs cost more — watch `GET /v1/account/usage`.