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
results.json as `octen_refs`.

Stdlib only — no pip install required.
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
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
    403: "Insufficient account balance.",
    413: "Input too large (image > 5MB, or query too long).",
    415: "Unsupported input media type.",
    422: "Input unreadable, invalid, or unsupported topic.",
    429: "Rate limit exceeded. Wait and retry.",
    500: "Server error. Retry later.",
}


def image_input(ref):
    """Turn a local path or URL into an inputs[] image entry."""
    if ref.startswith("http://") or ref.startswith("https://"):
        return {"type": "image", "url": ref}
    p = Path(ref)
    if not p.is_file():
        sys.exit(f"Image reference not found: {ref}")
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return {"type": "image", "data": data}


def build_payload(args, topic):
    inputs = []
    if args.query:
        inputs.append({"type": "text", "data": args.query[:500]})
    if args.image:
        inputs.append(image_input(args.image))
    payload = {
        "inputs": inputs,
        "topic": topic,
        "output_modalities": ["image"],
        "count": args.count,
        # Only honored for topic=design; harmless for general.
        "html_snippet": {"enable": True, "max_tokens": args.max_snippet_tokens},
    }
    return payload


def call_api(payload, api_key):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "x-api-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        hint = ERROR_HINTS.get(e.code, "")
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            detail = ""
        sys.exit(f"API error {e.code}: {hint} {detail}".strip())
    except urllib.error.URLError as e:
        sys.exit(f"Network error reaching the image search API: {e.reason}")


def download_image(url, dest_stem):
    """Download an image URL to dest_stem.<ext>. Returns the path or None."""
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ui-design-search/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "")
        ext = mimetypes.guess_extension(ctype.split(";")[0].strip()) or ".jpg"
        if ext == ".jpe":
            ext = ".jpg"
        path = dest_stem.with_suffix(ext)
        path.write_bytes(data)
        return str(path)
    except Exception:
        return None


def collect_topic(topic, args, api_key):
    """Query one topic and return its raw image results (list of dicts)."""
    resp = call_api(build_payload(args, topic), api_key)
    results = (resp.get("data") or {}).get("results") or []
    # The image-search endpoint returns image hits with no `type` field; keep
    # any entry that has an image URL (do NOT filter on type == "image").
    return [r for r in results if r.get("url")]


def fetch_one_image(topic, i, r, out):
    """Download a single result's image (with thumbnail fallback). Thread-safe."""
    # Primary image is `url` (full-res). For general, the foreign-host image
    # may be huge or hotlink-blocked, so fall back to the octen-proxied
    # `thumbnail` when the original download fails.
    img_path = download_image(r.get("url"), out / f"{topic}_{i}")
    used_thumbnail = False
    if img_path is None and r.get("thumbnail"):
        img_path = download_image(r.get("thumbnail"), out / f"{topic}_{i}")
        used_thumbnail = img_path is not None
    return img_path, used_thumbnail


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
        img_path, used_thumbnail = images.get(i, (None, False))

        snippet = r.get("html_snippet")
        snippet_path = None
        if snippet:
            snippet_path = str(out / f"{topic}_snippet_{i}.html")
            Path(snippet_path).write_text(snippet, encoding="utf-8")

        refs.append({
            "topic": topic,
            "index": i,
            "title": r.get("title"),
            "source_page": r.get("source_page"),
            "image_url": r.get("url"),
            "thumbnail_url": r.get("thumbnail") or None,
            "local_image": img_path,
            "local_image_is_thumbnail": used_thumbnail,
            "description": r.get("description"),
            "summary": r.get("summary"),
            "html_snippet_file": snippet_path,
            "width": r.get("width"),
            "height": r.get("height"),
        })
    return refs


def print_topic_report(topic, refs, heading):
    print("=" * 64)
    print(heading)
    print("=" * 64)
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
            print(f"    image  : (download failed) {ref.get('image_url')}")
        if ref.get("description"):
            print(f"    desc   : {ref['description']}")
        if ref.get("summary"):
            print(f"    style  : {ref['summary']}")
        if ref.get("html_snippet_file"):
            print(f"    snippet: {ref['html_snippet_file']}   <-- read it; use fully if detailed, else as structure only")
        print("-" * 64)


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
        help="Reference image for image-based search: local path (sent as base64) or public URL.",
    )
    parser.add_argument("--count", type=int, default=5, help="Number of results PER TOPIC, 1-100 (default 5).")
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

    if not args.query and not args.image:
        sys.exit("Provide a text query and/or --image.")

    api_key = os.environ.get("OCTEN_API_KEY")
    if not api_key:
        sys.exit(
            "OCTEN_API_KEY is not set. Export it before running "
            "(do NOT paste the key into the chat)."
        )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Query  : {args.query or '[image search]'}")
    print(f"Topics : {', '.join(args.topics)}")

    octen_refs = []
    per_topic = {}
    for topic in args.topics:
        raw = collect_topic(topic, args, api_key)
        refs = process_topic(topic, raw, args, out)
        per_topic[topic] = refs
        octen_refs.extend(refs)

    print(f"Results: {len(octen_refs)} total "
          f"({', '.join(f'{t}={len(per_topic.get(t, []))}' for t in args.topics)})")

    if not octen_refs:
        print(
            "NO RESULTS. Proceed using your own design judgment, tell the user no "
            "reference was found, and consider broadening the query."
        )
        (out / "results.json").write_text(
            json.dumps({"query": args.query, "topics": args.topics, "octen_refs": []},
                       ensure_ascii=False, indent=2)
        )
        return

    headings = {
        "design": "DESIGN refs (primary — structured summary + html_snippet)",
        "general": "GENERAL refs (supplementary — visual inspiration only)",
    }
    # design first (primary), then general (supplementary), then any other topics.
    ordered = [t for t in ("design", "general") if t in per_topic]
    ordered += [t for t in args.topics if t not in ordered]
    for topic in ordered:
        print_topic_report(topic, per_topic.get(topic, []),
                           headings.get(topic, f"{topic.upper()} refs"))

    (out / "results.json").write_text(
        json.dumps({"query": args.query, "topics": args.topics, "octen_refs": octen_refs},
                   ensure_ascii=False, indent=2)
    )
    print(f"Manifest: {out / 'results.json'}  (key: octen_refs)")


if __name__ == "__main__":
    main()
