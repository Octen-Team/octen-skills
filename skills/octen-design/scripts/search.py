#!/usr/bin/env python3
"""
Query the octen.ai image-search API for UI reference designs.

Searches TWO topics and merges them into one set of references (octen_refs):

  * topic=design  — curated UI design corpus. Each hit carries a reference
    screenshot plus structured `summary` (design tokens) and an `html_snippet`.
    These are the primary refs for implementation.
  * topic=general — broad general-web image search. Wider visual coverage, but
    NO summary / html_snippet (and usually empty description). These are
    supplementary visual inspiration / style references.

Reads the API key from the OCTEN_API_KEY environment variable. Downloads result
images locally, writes each design-style summary and reusable HTML/CSS snippet to
an output directory, then prints a concise report to stdout (design refs first,
general refs after) so the model can act on it. The merged manifest is written to
results.json as `octen_refs`, with `partial` / `topic_errors` recording any
topic-level failures.

Stdlib only — no pip install required.
"""

import argparse
import base64
import hashlib
import http.client
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Image downloads run concurrently within a topic; one slow/blocked host (e.g. a
# proxy resetting a CDN) no longer serializes behind the others. Per-download
# timeout is unchanged — this only overlaps the waiting.
DOWNLOAD_WORKERS = 8

# Endpoint. Override with OCTEN_API_URL if the path/host changes.
# NOTE: the working path is `/image-search` (NOT `/v1/image-search`, which 404s).
API_URL = os.environ.get("OCTEN_API_URL", "https://api.octen.ai/image-search")

# Topics queried by default. `design` = curated UI corpus (rich metadata);
# `general` = broad web image search (visual inspiration only).
DEFAULT_TOPICS = ["design", "general"]

ERROR_HINTS = {
    400: "Missing or malformed parameter.",
    401: "Invalid API key. Check the OCTEN_API_KEY environment variable.",
    403: "No beta access for this endpoint, or insufficient account balance "
         "(the server message below says which).",
    413: "Input too large (image > 5MB base64-encoded, or query too long).",
    415: "Unsupported input media type.",
    422: "Input unreadable, invalid, or unsupported topic.",
    429: "Rate limit exceeded. Wait and retry.",
    500: "Server error. Retry later.",
}

# Retry policy for transient failures: statuses retried, retries after the
# first attempt, base backoff.
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRIES = 2
RETRY_BASE_DELAY = 1.0

# Cap on a single downloaded image (per download; up to DOWNLOAD_WORKERS may be
# in flight at once); guards memory against oversized files from arbitrary
# general-topic hosts.
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024  # 20 MB

# Cap on a local reference image sent inline. The OpenAPI contract sets the
# limit on the base64-ENCODED payload ("at most 5MB after encoding"), so the
# pre-check measures encoded size; failing locally avoids burning a request.
MAX_LOCAL_IMAGE_BYTES = 5 * 1024 * 1024


class APICallError(Exception):
    """One topic's API call failed definitively (retries exhausted, or a
    non-retryable error); other topics may still work."""


def image_input(ref):
    """Turn a local path or URL into an inputs[] image entry."""
    scheme = urllib.parse.urlsplit(ref).scheme.lower()
    if scheme in ("http", "https"):
        return {"type": "image", "url": ref}
    p = Path(ref)
    if not p.is_file():
        sys.exit(f"Image reference not found: {ref}")
    size = p.stat().st_size
    encoded_size = 4 * ((size + 2) // 3)  # base64 output size for `size` raw bytes
    if encoded_size > MAX_LOCAL_IMAGE_BYTES:
        sys.exit(
            f"Image {ref} is {size / 1048576:.1f}MB "
            f"({encoded_size / 1048576:.1f}MB base64-encoded); the API accepts "
            "at most 5MB after encoding — pass a public https URL instead."
        )
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return {"type": "image", "data": data}


def build_payload(args, topic):
    # The API accepts exactly ONE input per request (OpenAPI: "either one text
    # input or one image input"; two inputs are rejected with 400).
    if args.image:
        inputs = [image_input(args.image)]
    else:
        inputs = [{"type": "text", "data": args.query[:500]}]
    payload = {
        "inputs": inputs,
        "topic": topic,
        "count": args.count,
        # Only honored for topic=design; harmless for general.
        "html_snippet": {"enable": True, "max_tokens": args.max_snippet_tokens},
    }
    return payload


def call_api(payload, api_key):
    """POST to the API with retries on transient failures.

    Raises APICallError on any definitive failure — HTTP error, exhausted
    retries, network/read failure, or an unreadable response body — so the
    caller can decide whether to continue with other topics (a 403 on one
    topic must not discard results already fetched for another).
    """
    body = json.dumps(payload).encode("utf-8")
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        req = urllib.request.Request(
            API_URL,
            data=body,
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        server_delay = None
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
            try:
                return json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                last_error = (
                    f"Unreadable (non-JSON) response body from the image "
                    f"search API: {e}"
                )
                break
        except urllib.error.HTTPError as e:
            hint = ERROR_HINTS.get(e.code, "")
            try:
                detail = e.read().decode("utf-8", "replace").strip()
            except Exception:
                detail = ""
            last_error = f"API error {e.code}: {hint} {detail or '(no response body)'}".strip()
            if e.code not in RETRYABLE_STATUSES:
                break
            retry_after = e.headers.get("Retry-After") if e.headers else None
            if retry_after:
                try:
                    server_delay = min(float(retry_after), 30.0)
                except ValueError:
                    pass
        except (urllib.error.URLError, http.client.HTTPException, OSError) as e:
            # Read-phase failures (timeout, reset, truncated body) surface as
            # raw OSError/HTTPException rather than URLError; all transient.
            last_error = f"Network error reaching the image search API: {getattr(e, 'reason', e)}"
        if attempt < MAX_RETRIES:
            delay = max(RETRY_BASE_DELAY * (2 ** attempt), server_delay or 0)
            print(
                f"WARNING: image search API attempt {attempt + 1}/{MAX_RETRIES + 1} "
                f"failed ({last_error}); retrying in {delay:.0f}s",
                file=sys.stderr,
            )
            time.sleep(delay)
    raise APICallError(last_error or "unknown error")


class _HttpOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse redirects to any non-http(s) scheme (urllib itself would follow
    a redirect to ftp://)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme.lower() not in ("http", "https"):
            raise urllib.error.URLError(f"redirect to non-http(s) URL blocked: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_DOWNLOAD_OPENER = urllib.request.build_opener(_HttpOnlyRedirectHandler)


def download_image(url, dest_stem):
    """Download an image URL to dest_stem.<ext>.

    Returns (path, None) on success or (None, reason) on failure, so the
    caller can record WHY an image is missing. Only http(s) URLs are fetched
    — enforced across redirects too — and reads are capped at
    MAX_DOWNLOAD_BYTES so an oversized file from an arbitrary host cannot
    exhaust memory.
    """
    if not url:
        return None, "no image URL in the API response"
    scheme = urllib.parse.urlsplit(url).scheme.lower()
    if scheme not in ("http", "https"):
        return None, f"blocked non-http(s) URL scheme: {scheme or '(none)'}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ui-design-search/1.0"})
        with _DOWNLOAD_OPENER.open(req, timeout=60) as resp:
            data = resp.read(MAX_DOWNLOAD_BYTES + 1)
            if len(data) > MAX_DOWNLOAD_BYTES:
                return None, "image exceeds the 20MB download cap"
            ctype = resp.headers.get("Content-Type", "")
    except Exception as e:
        return None, f"download failed: {e.__class__.__name__}: {e}"
    ext = mimetypes.guess_extension(ctype.split(";")[0].strip()) or ".jpg"
    if ext == ".jpe":
        ext = ".jpg"
    path = dest_stem.with_suffix(ext)
    try:
        path.write_bytes(data)
    except OSError as e:
        return None, f"cannot write {path} locally: {e}"
    return str(path), None


def safe_topic_slug(topic):
    """Filesystem-safe slug for a topic used in output filenames.

    --topics is user input that gets interpolated into paths; strip anything
    that could escape the output directory (e.g. "../evil"). Sanitized slugs
    get a short hash suffix so distinct topics that sanitize to the same text
    ("a b" vs "a_b") cannot overwrite each other's files.
    """
    slug = re.sub(r"[^A-Za-z0-9_-]", "_", topic) or "topic"
    if slug != topic:
        slug += "-" + hashlib.md5(topic.encode("utf-8")).hexdigest()[:6]
    return slug


def collect_topic(topic, args, api_key):
    """Query one topic and return its raw image results (list of dicts)."""
    resp = call_api(build_payload(args, topic), api_key)
    if not isinstance(resp, dict) or not isinstance(resp.get("data"), dict):
        got = sorted(resp) if isinstance(resp, dict) else type(resp).__name__
        raise APICallError(
            "Unexpected response envelope from the image search API "
            f"(no 'data' object; got: {got})"
        )
    results = resp["data"].get("results") or []
    # The image-search endpoint returns image hits with no `type` field; keep
    # any entry that has an image URL (do NOT filter on type == "image").
    return [r for r in results if isinstance(r, dict) and r.get("url")]


def fetch_one_image(topic, i, r, out):
    """Download a single result's image (with thumbnail fallback). Thread-safe.

    Returns (path, used_thumbnail, error); error is set only when no image
    could be saved at all.
    """
    # Primary image is `url` (full-res). For general, the foreign-host image
    # may be huge or hotlink-blocked, so fall back to the octen-proxied
    # `thumbnail` when the original download fails.
    slug = safe_topic_slug(topic)
    img_path, primary_error = download_image(r.get("url"), out / f"{slug}_{i}")
    used_thumbnail = False
    error = None
    if img_path is None:
        if r.get("thumbnail"):
            img_path, thumb_error = download_image(r.get("thumbnail"), out / f"{slug}_{i}")
            used_thumbnail = img_path is not None
            if img_path is None:
                error = f"original: {primary_error}; thumbnail: {thumb_error}"
        else:
            error = primary_error
    if error:
        print(f"WARNING: [{topic}:{i}] image not saved — {error}", file=sys.stderr)
    return img_path, used_thumbnail, error


def process_topic(topic, results, args, out):
    """Download images/snippets for one topic; return that topic's octen_refs."""
    # Fan out the image downloads concurrently; results keyed by index so the
    # output order is preserved regardless of completion order.
    images = {}
    if results:
        with ThreadPoolExecutor(max_workers=min(DOWNLOAD_WORKERS, len(results))) as ex:
            futures = {
                ex.submit(fetch_one_image, topic, i, r, out): i
                for i, r in enumerate(results)
            }
            for fut in futures:
                images[futures[fut]] = fut.result()

    refs = []
    for i, r in enumerate(results):
        img_path, used_thumbnail, image_error = images.get(i, (None, False, None))

        snippet = r.get("html_snippet")
        snippet_path = None
        snippet_error = None
        if snippet:
            if not isinstance(snippet, str):
                snippet_error = f"unexpected html_snippet type: {type(snippet).__name__}"
            else:
                snippet_path = str(out / f"{safe_topic_slug(topic)}_snippet_{i}.html")
                try:
                    Path(snippet_path).write_text(snippet, encoding="utf-8")
                except OSError as e:
                    snippet_path = None
                    snippet_error = f"cannot write snippet locally: {e}"
            if snippet_error:
                print(f"WARNING: [{topic}:{i}] {snippet_error}", file=sys.stderr)

        refs.append({
            "topic": topic,
            "index": i,
            "title": r.get("title"),
            "source_page": r.get("source_page"),
            "image_url": r.get("url"),
            "thumbnail_url": r.get("thumbnail") or None,
            "local_image": img_path,
            "local_image_is_thumbnail": used_thumbnail,
            "image_error": image_error,
            "description": r.get("description"),
            "summary": r.get("summary"),
            "html_snippet_file": snippet_path,
            "snippet_error": snippet_error,
            "width": r.get("width"),
            "height": r.get("height"),
        })
    return refs


def print_topic_report(topic, refs, heading, error=None):
    print("=" * 64)
    print(heading)
    print("=" * 64)
    if error:
        print(f"(TOPIC FAILED: {error})")
        return
    if not refs:
        print("(no results for this topic)")
        return
    for ref in refs:
        i = ref["index"]
        print(f"[{topic}:{i}] {ref.get('title') or '(untitled)'}")
        print(f"    source : {ref.get('source_page') or ref.get('image_url')}")
        if ref.get("local_image"):
            tag = " (thumbnail)" if ref.get("local_image_is_thumbnail") else ""
            print(f"    image  : {ref['local_image']}{tag}   <-- view this")
        else:
            print(f"    image  : (not saved: {ref.get('image_error')}) {ref.get('image_url')}")
        if ref.get("description"):
            print(f"    desc   : {ref['description']}")
        if ref.get("summary"):
            print(f"    style  : {ref['summary']}")
        if ref.get("html_snippet_file"):
            print(f"    snippet: {ref['html_snippet_file']}   <-- read it; use fully if detailed, else as structure only")
        print("-" * 64)


def write_manifest(out, query, topics, octen_refs, topic_errors):
    """Write results.json atomically: a crash mid-write must not leave a
    truncated manifest, and a failed run must not leave a stale one."""
    manifest = {
        "query": query,
        "topics": topics,
        "partial": bool(topic_errors),
        "topic_errors": topic_errors,
        "octen_refs": octen_refs,
    }
    tmp = out / "results.json.tmp"
    try:
        tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        os.replace(tmp, out / "results.json")
    except OSError as e:
        sys.exit(f"Cannot write {out / 'results.json'}: {e}")


def count_arg(value):
    n = int(value)
    if not 1 <= n <= 10:
        raise argparse.ArgumentTypeError("must be between 1 and 10 (the API's documented range)")
    return n


def main():
    parser = argparse.ArgumentParser(
        description="Search UI design references via the octen.ai image-search API (design + general topics)."
    )
    parser.add_argument(
        "query", nargs="?", default="",
        help="Text query (<=500 chars). Describe the component AND its style/theme.",
    )
    parser.add_argument(
        "--image",
        help="Reference image for image-based search: local path (sent as base64) "
             "or public URL. Cannot be combined with a text query.",
    )
    parser.add_argument("--count", type=count_arg, default=5, help="Number of results PER TOPIC, 1-10 (default 5).")
    parser.add_argument(
        "--topics", nargs="+", default=DEFAULT_TOPICS,
        help="Topics to query (default: design general). design = curated UI corpus; general = broad web images.",
    )
    parser.add_argument(
        "--max-snippet-tokens", type=int, default=5000,
        help="Max tokens per html_snippet (default 5000; raise for complex components).",
    )
    parser.add_argument(
        "--out", default="./.ui-refs",
        help="Output directory for downloaded images, snippets, and results.json.",
    )
    args = parser.parse_args()

    if args.query and args.image:
        sys.exit(
            "The image-search API accepts a single input per request: pass a "
            "text query OR --image, not both. Run the script twice to combine "
            "text and image references."
        )
    if not args.query and not args.image:
        sys.exit("Provide a text query or --image.")

    api_key = os.environ.get("OCTEN_API_KEY")
    if not api_key:
        sys.exit(
            "OCTEN_API_KEY is not set. Export it before running "
            "(do NOT paste the key into the chat)."
        )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # Duplicate topics would query the same corpus twice and overwrite each
    # other's files; keep the first occurrence of each.
    topics = list(dict.fromkeys(args.topics))
    if len(topics) < len(args.topics):
        print("WARNING: duplicate --topics values ignored", file=sys.stderr)

    print(f"Query  : {args.query or '[image search]'}")
    print(f"Topics : {', '.join(topics)}")

    octen_refs = []
    per_topic = {}
    topic_errors = {}
    for topic in topics:
        try:
            raw = collect_topic(topic, args, api_key)
        except APICallError as e:
            # One topic failing (e.g. 403 no beta access) must not discard
            # results already fetched for other topics.
            topic_errors[topic] = str(e)
            print(f"WARNING: topic '{topic}' failed: {e}", file=sys.stderr)
            per_topic[topic] = []
            continue
        refs = process_topic(topic, raw, args, out)
        per_topic[topic] = refs
        octen_refs.extend(refs)

    if topic_errors and not octen_refs:
        # Nothing was retrieved and at least one topic failed outright. Exit
        # non-zero with the failure — NOT "no results": broadening the query
        # is the wrong remedy for e.g. a 403.
        write_manifest(out, args.query, topics, octen_refs, topic_errors)
        details = "; ".join(f"{t}: {err}" for t, err in topic_errors.items())
        sys.exit(f"No results — {len(topic_errors)} of {len(topics)} topic(s) failed. {details}")

    status = ", ".join(
        f"{t}=FAILED" if t in topic_errors else f"{t}={len(per_topic.get(t, []))}"
        for t in topics
    )
    print(f"Results: {len(octen_refs)} total ({status})")
    if topic_errors:
        print(
            f"NOTE: partial results — {len(topic_errors)} topic(s) failed: "
            + "; ".join(f"{t}: {err}" for t, err in topic_errors.items())
        )

    if not octen_refs:
        print(
            "NO RESULTS. Proceed using your own design judgment, tell the user no "
            "reference was found, and consider broadening the query."
        )
        write_manifest(out, args.query, topics, octen_refs, topic_errors)
        return

    headings = {
        "design": "DESIGN refs (primary — structured summary + html_snippet)",
        "general": "GENERAL refs (supplementary — visual inspiration only)",
    }
    # design first (primary), then general (supplementary), then any other topics.
    ordered = [t for t in ("design", "general") if t in per_topic]
    ordered += [t for t in topics if t not in ordered]
    for topic in ordered:
        print_topic_report(topic, per_topic.get(topic, []),
                           headings.get(topic, f"{topic.upper()} refs"),
                           error=topic_errors.get(topic))

    write_manifest(out, args.query, topics, octen_refs, topic_errors)
    print(f"Manifest: {out / 'results.json'}  (key: octen_refs)")


if __name__ == "__main__":
    main()
