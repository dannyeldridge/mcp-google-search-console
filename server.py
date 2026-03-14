#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastmcp",
#   "google-api-python-client",
#   "google-auth-oauthlib",
#   "google-auth-httplib2",
# ]
# ///
"""Google Search Console MCP Server"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from fastmcp import FastMCP
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
DIR = Path(__file__).parent
CLIENT_SECRETS_FILE = DIR / "client_secrets.json"
TOKEN_FILE = DIR / "token.json"

mcp = FastMCP("Google Search Console")


def get_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("searchconsole", "v1", credentials=creds)


@mcp.tool()
def list_sites() -> str:
    """List all verified sites/properties in Google Search Console."""
    service = get_service()
    result = service.sites().list().execute()
    return json.dumps(result.get("siteEntry", []), indent=2)


@mcp.tool()
def get_performance(
    site_url: str,
    start_date: str = None,
    end_date: str = None,
    dimensions: list[str] = None,
    row_limit: int = 50,
) -> str:
    """Get search performance data (clicks, impressions, CTR, position).

    Args:
        site_url: The site property URL (e.g. 'https://example.com/')
        start_date: YYYY-MM-DD (defaults to 28 days ago)
        end_date: YYYY-MM-DD (defaults to today)
        dimensions: Group by dimensions — 'query', 'page', 'country', 'device', 'date'
        row_limit: Rows to return (max 25000)
    """
    service = get_service()
    if not start_date:
        start_date = (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not dimensions:
        dimensions = ["query"]

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions,
        "rowLimit": row_limit,
        "startRow": 0,
    }
    result = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    return json.dumps(result, indent=2)


@mcp.tool()
def inspect_url(site_url: str, page_url: str) -> str:
    """Inspect a URL — index status, crawl errors, canonical, mobile usability, etc.

    Args:
        site_url: The site property URL in GSC
        page_url: The full URL of the page to inspect
    """
    service = get_service()
    result = (
        service.urlInspection()
        .index()
        .inspect(body={"inspectionUrl": page_url, "siteUrl": site_url})
        .execute()
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def list_sitemaps(site_url: str) -> str:
    """List all sitemaps submitted for a site.

    Args:
        site_url: The site property URL in GSC
    """
    service = get_service()
    result = service.sitemaps().list(siteUrl=site_url).execute()
    return json.dumps(result, indent=2)


@mcp.tool()
def get_top_pages(
    site_url: str,
    start_date: str = None,
    end_date: str = None,
    row_limit: int = 50,
) -> str:
    """Get top pages by clicks over a date range.

    Args:
        site_url: The site property URL in GSC
        start_date: YYYY-MM-DD (defaults to 28 days ago)
        end_date: YYYY-MM-DD (defaults to today)
        row_limit: Number of pages to return
    """
    service = get_service()
    if not start_date:
        start_date = (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["page"],
        "rowLimit": row_limit,
        "orderBy": [{"fieldName": "clicks", "sortOrder": "DESCENDING"}],
    }
    result = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    return json.dumps(result, indent=2)


@mcp.tool()
def get_low_ctr_pages(
    site_url: str,
    min_impressions: int = 100,
    start_date: str = None,
    end_date: str = None,
    row_limit: int = 50,
) -> str:
    """Find pages with high impressions but low CTR — opportunities to improve titles/descriptions.

    Args:
        site_url: The site property URL in GSC
        min_impressions: Only include pages with at least this many impressions
        start_date: YYYY-MM-DD (defaults to 28 days ago)
        end_date: YYYY-MM-DD (defaults to today)
        row_limit: Number of pages to return
    """
    service = get_service()
    if not start_date:
        start_date = (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["page"],
        "rowLimit": 1000,
        "orderBy": [{"fieldName": "impressions", "sortOrder": "DESCENDING"}],
    }
    result = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    rows = result.get("rows", [])

    low_ctr = [
        r for r in rows if r.get("impressions", 0) >= min_impressions
    ]
    low_ctr.sort(key=lambda r: r.get("ctr", 1))
    return json.dumps({"rows": low_ctr[:row_limit]}, indent=2)


if __name__ == "__main__":
    mcp.run()
