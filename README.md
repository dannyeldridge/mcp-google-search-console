# Google Search Console MCP Server

MCP server for querying Google Search Console data — search performance, top pages, low-CTR opportunities, URL inspection, and sitemaps.

## Setup

**1. Get credentials from Google Cloud Console**

- Create a project at [console.cloud.google.com](https://console.cloud.google.com)
- Enable the **Google Search Console API**
- Create an OAuth 2.0 Desktop App credential
- Download the JSON and save it as `client_secrets.json` in this directory

**2. Add to Claude Desktop**

```json
{
  "mcpServers": {
    "gsc": {
      "command": "uv",
      "args": ["run", "/path/to/server.py"]
    }
  }
}
```

On first run, a browser window will open to authorize access. The token is saved locally to `token.json`.

## Tools

| Tool | Description |
|---|---|
| `list_sites` | List all verified properties in GSC |
| `get_performance` | Clicks, impressions, CTR, position — filterable by query/page/country/device/date |
| `get_top_pages` | Top pages by clicks |
| `get_low_ctr_pages` | Pages with high impressions but low CTR |
| `inspect_url` | Index status, crawl errors, canonical, mobile usability |
| `list_sitemaps` | Sitemaps submitted for a site |

## Requirements

- [uv](https://docs.astral.sh/uv/) — dependencies are managed via inline script metadata, no separate install needed
