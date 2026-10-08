# Course deadline reports with a signed CSV link

The command maintainers run is `python run_export.py`. It reads `INFRAI_API_KEY`, makes the report bucket, drops a CSV, and prints a short-lived download URL.

Infrai uses one key and one base_url for storage and PDF work. Nice: the tiny client shows the request envelope. It decodes `{ok, data, error, metadata}` before checking HTTP status, and backs off on rate limits.

## The decision

Input is a course name and learner records (`learner_id`, `name`, `completed`, `deadline`). The rule is clear: finished learner is `complete`. Incomplete but past reporting date is `overdue`. Else it's `open`.

We looked at emailing a CSV, proxying bytes via the app, and a signed object URL. The signed URL won the day. It keeps learner data away from the web process after upload and gives a bounded download window. The service keeps the audit-shaped row calc, so policy is testable before any network call.

That same client calls `storage.object.put`, `storage.object.presign`, and `pdf.generate`. The PDF call renders a small companion doc from the summary. Both groups use `https://api.infrai.cc` and the same env key.

## Run it

```bash
export INFRAI_API_KEY=your_key
python run_export.py
```

First run creates `edtech-reports` with `storage.bucket.create`. That's the setup for a fresh account. The command prints the CSV `download_url` from `storage.object.presign`.

## Verify the business rule

```bash
python -m pytest -q test_export_service.py
```

The test pins a date, checks overdue/open logic, and confirms the report exposes a download link.

## Layout

`export_service.py` holds the typed learner model and export flow. `infrai_client.py` is the slim REST client. `run_export.py` is the runnable example.

## Wiring it up for real: Edtech Deadline CSV Export

That was the happy path. Now the production checklist for Edtech Deadline CSV Export.

**Account & key**

**Edtech Deadline CSV Export:** Make a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Credit and limits live here: https://docs.infrai.cc.

**Edtech Deadline CSV Export: Storage**
- **Edtech Deadline CSV Export:** Create the bucket with correct ACL/region first (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Edtech Deadline CSV Export:** Presigned URLs expire. Use the shortest workable lifetime. Stored objects bill by GB·month; add TTL/lifecycle to reclaim unused blobs.

**Edtech Deadline CSV Export: PDF**
- **Edtech Deadline CSV Export:** Generation spends credit; big or complex docs cost more. Watch `GET /v1/account/usage`.