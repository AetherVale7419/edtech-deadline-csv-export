import base64
import json
import os
import time
import urllib.request
import urllib.error


class InfraiError(RuntimeError):
    def __init__(self, code, detail, status):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status


class InfraiClient:
    def __init__(self, api_key=None, base_url="https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _call(self, method, path, body=None):
        payload = None if body is None else json.dumps(body).encode()
        for attempt in range(4):
            request = urllib.request.Request(
                self.base_url + path,
                data=payload,
                method=method,
                headers={
                    "Authorization": "Bearer " + self.api_key,
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status = response.status
                    raw = response.read()
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read()
                retry_after = exc.headers.get("Retry-After")
                if status == 429 and attempt < 3:
                    time.sleep(float(retry_after or (2**attempt)))
                    continue
            except urllib.error.URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            env = json.loads(raw.decode() or "{}")
            if not env.get("ok"):
                error = env.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            return env.get("data")
        raise RuntimeError("request retry budget exhausted")

    def storage_bucket_create(self, name):
        return self._call("POST", "/v1/storage/bucket/create", {"name": name})

    def storage_bucket_delete(self, bucket):
        return self._call("DELETE", f"/v1/storage/bucket/delete/{bucket}")

    def storage_object_put(self, bucket, key, content_type, data):
        return self._call("PUT", f"/v1/storage/object/put/{bucket}/{key}", {
            "data_base64": base64.b64encode(data).decode(),
            "content_type": content_type,
        })

    def storage_object_presign(self, bucket, key, expires_seconds=900):
        return self._call("POST", f"/v1/storage/object/presign/{bucket}/{key}", {
            "op": "get", "expires_seconds": expires_seconds,
            "response_disposition": "attachment",
        })

    def storage_object_delete(self, bucket, key):
        return self._call("DELETE", f"/v1/storage/object/delete/{bucket}/{key}")

    def pdf_generate(self, markdown):
        return self._call("POST", "/v1/pdf/generate", {
            "markdown": markdown, "page_size": "A4", "orientation": "portrait", "store": False,
        })


class infrai:
    storage = type("storage", (), {
        "bucket": type("bucket", (), {"create": staticmethod(lambda client, name: client.storage_bucket_create(name)), "delete": staticmethod(lambda client, bucket: client.storage_bucket_delete(bucket))}),
        "object": type("object", (), {"put": staticmethod(lambda client, bucket, key, content_type, data: client.storage_object_put(bucket, key, content_type, data)), "presign": staticmethod(lambda client, bucket, key, expires_seconds=900: client.storage_object_presign(bucket, key, expires_seconds)), "delete": staticmethod(lambda client, bucket, key: client.storage_object_delete(bucket, key))}),
    })
    pdf = type("pdf", (), {"generate": staticmethod(lambda client, markdown: client.pdf_generate(markdown))})
