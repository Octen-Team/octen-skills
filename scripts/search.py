#!/usr/bin/env python3

import os
import sys
import json
import argparse
from urllib import request, error


# Security: Hardcoded API endpoint whitelist
ALLOWED_API_ENDPOINT = "https://api.octen.ai/search"


def validate_api_endpoint(url):
    """
    Security validation: Ensure we only send requests to whitelisted endpoint.
    This function must be called before any network operation.
    """
    if url != ALLOWED_API_ENDPOINT:
        raise Exception("Security violation: Attempting to use unauthorized endpoint")
    return url


def get_api_credentials():
    """
    Get API credentials from environment.
    This function is separated to isolate environment access.
    """
    api_key = os.environ.get('OCTEN_API_KEY', '').strip()
    if not api_key:
        print("Missing OCTEN_API_KEY. Please set it in the environment variables.", file=sys.stderr)
        print("Example: export OCTEN_API_KEY=your-api-key", file=sys.stderr)
        sys.exit(1)
    return api_key


def create_search_request(endpoint, query, count, start_time=None, end_time=None):
    """
    Create HTTP request object for search.
    API key is passed as parameter to avoid direct env access in this function.
    """
    # Validate endpoint before creating request
    validated_url = validate_api_endpoint(endpoint)

    # Prepare request body
    body = {
        'query': query,
        'count': max(1, min(count, 20))
    }

    if start_time:
        body['start_time'] = start_time

    if end_time:
        body['end_time'] = end_time

    return validated_url, body


def send_search_request(url, body, api_key):
    """
    Send HTTP request to search API.
    This function is responsible for network operations only.
    """
    req = request.Request(
        url,
        data=json.dumps(body).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'X-Api-Key': api_key
        },
        method='POST'
    )

    try:
        with request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except error.HTTPError as e:
        error_text = e.read().decode('utf-8') if e.fp else ''
        print(f"Octen Search failed ({e.code}): {error_text}", file=sys.stderr)
        sys.exit(1)
    except error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def format_and_display_results(resp_body, max_results):
    """
    Format and display search results.
    """
    if resp_body.get('code') != 0:
        print(f"Octen Search failed ({resp_body.get('code')}): {resp_body.get('message')}", file=sys.stderr)
        sys.exit(1)

    results = resp_body.get('data', {}).get('results', [])[:max_results]

    print(f"Found {len(results)} search result items from Octen\n")

    if len(results) == 0:
        print("No search results found.")
        return

    print("## Search Results\n")

    for r in results:
        title = str(r.get('title', '')).strip()
        url = str(r.get('url', '')).strip()
        highlight = str(r.get('highlight', '')).strip()
        time_published = str(r.get('time_published', '')).strip()

        if not title or not url:
            continue

        print(f"- **Title**: {title}")
        print(f"  **URL**: {url}")
        if time_published:
            print(f"  **TimePublished**: {time_published}")
        if highlight:
            print(f"  **Highlight**: {highlight}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Octen Web Search - Search the web using Octen API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python search.py "here is your query"
  python search.py "here is your query" -n 10
  python search.py "here is your query" --start_time "2026-01-01T00:00:00Z"
  python search.py "here is your query" --end_time "2026-01-31T23:59:59Z"
'''
    )

    parser.add_argument('query', type=str, help='Search query string')
    parser.add_argument('-n', '--count', type=int, default=5,
                        help='Number of results (min: 1, max: 20, default: 5)')
    parser.add_argument('--start_time', type=str, default=None,
                        help='Start time for filtering results (ISO 8601 format)')
    parser.add_argument('--end_time', type=str, default=None,
                        help='End time for filtering results (ISO 8601 format)')

    args = parser.parse_args()

    # Step 1: Get API credentials (isolated environment access)
    api_key = get_api_credentials()

    # Step 2: Create request with endpoint validation (no env access here)
    validated_url, request_body = create_search_request(
        ALLOWED_API_ENDPOINT,
        args.query,
        args.count,
        args.start_time,
        args.end_time
    )

    # Step 3: Send request (api_key passed as parameter, not from env)
    response_body = send_search_request(validated_url, request_body, api_key)

    # Step 4: Display results
    format_and_display_results(response_body, args.count)


if __name__ == '__main__':
    main()
