"""
Server-Side Web Proxy
=====================
Fetches a remote URL on behalf of the browser and returns it with:

  1. X-Frame-Options / CSP frame-ancestor headers stripped.
  2. A <base> tag injected so relative links resolve against the original origin.
  3. All <a href> links rewritten to go through /api/proxy so navigation
     stays inside the proxy iframe.

Why this works
--------------
A browser enforces X-Frame-Options only when the *framed document* sends
the header. If FastAPI fetches the page and re-serves it from localhost,
the browser never sees the remote X-Frame-Options header.

Limitations
-----------
* JavaScript SPAs that XHR/fetch their own API will fail (CORS from real origin).
* Sites that detect bot user-agents may return error pages.
These are fundamental HTTP-proxy limitations, not solvable without a headless browser.
"""

import re
from urllib.parse import urlparse, urljoin, quote

import httpx
from fastapi import APIRouter, Query, Response
from fastapi.responses import HTMLResponse, Response as FastResponse

router = APIRouter()

_TIMEOUT = 15.0

_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}

_STRIP_RESPONSE_HEADERS = {
    "x-frame-options",
    "content-security-policy",
    "content-security-policy-report-only",
    "x-content-type-options",
    "strict-transport-security",
    "transfer-encoding",
    "content-encoding",
    "content-length",
    "connection",
}


def _rewrite_html(html: str, origin: str) -> str:
    # 1. Remove existing <base> tags
    html = re.sub(r'<base[^>]*>', '', html, flags=re.IGNORECASE)

    # 2. Inject our <base> tag right after <head>
    base_tag = f'<base href="{origin}/">'
    if re.search(r'<head[^>]*>', html, re.IGNORECASE):
        html = re.sub(
            r'(<head[^>]*>)',
            r'\1' + base_tag,
            html,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        html = base_tag + html

    # 3. Rewrite <a href> to go through /api/proxy
    def rewrite_href(m: re.Match) -> str:
        quote_char = m.group(1)
        href = m.group(2)
        if re.match(r'^(#|javascript:|mailto:|tel:|data:)', href, re.IGNORECASE):
            return m.group(0)
        abs_href = urljoin(origin + "/", href)
        proxy_href = f"/api/proxy?url={quote(abs_href, safe='')}"
        return f'href={quote_char}{proxy_href}{quote_char}'

    html = re.sub(
        r'href=(["\'])([^"\']*)\1',
        rewrite_href,
        html,
        flags=re.IGNORECASE,
    )

    return html


@router.get(
    "/proxy",
    summary="Server-side web proxy",
    description=(
        "Fetches a remote URL server-side, strips X-Frame-Options/CSP headers, "
        "and returns the rewritten HTML so it can be embedded in an iframe."
    ),
)
async def proxy(url: str = Query(..., description="The remote URL to fetch")) -> Response:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return HTMLResponse(
            content=_error_page(url, "Only http:// and https:// URLs are supported."),
            status_code=400,
        )

    origin = f"{parsed.scheme}://{parsed.netloc}"

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=_TIMEOUT,
            headers=_REQUEST_HEADERS,
            verify=False,
        ) as client:
            remote_resp = await client.get(url)
    except httpx.TimeoutException:
        return HTMLResponse(
            content=_error_page(url, "The request timed out. The site may be slow or unavailable."),
            status_code=504,
        )
    except Exception as exc:
        return HTMLResponse(
            content=_error_page(url, f"Could not reach the site: {exc}"),
            status_code=502,
        )

    content_type = remote_resp.headers.get("content-type", "")

    safe_headers: dict[str, str] = {}
    for k, v in remote_resp.headers.items():
        if k.lower() not in _STRIP_RESPONSE_HEADERS:
            safe_headers[k] = v

    if "text/html" in content_type:
        try:
            html_text = remote_resp.text
        except Exception:
            html_text = remote_resp.content.decode("utf-8", errors="replace")

        rewritten = _rewrite_html(html_text, origin)

        return HTMLResponse(
            content=rewritten,
            status_code=remote_resp.status_code,
            headers=safe_headers,
        )

    return FastResponse(
        content=remote_resp.content,
        status_code=remote_resp.status_code,
        media_type=content_type or "application/octet-stream",
        headers=safe_headers,
    )


def _error_page(url: str, reason: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      min-height: 100vh;
      display: flex; align-items: center; justify-content: center;
      background: radial-gradient(ellipse at 50% 40%, #141a2e 0%, #0d0f17 70%);
      font-family: system-ui, sans-serif;
      color: #e2e8f0;
    }}
    .card {{
      display: flex; flex-direction: column; align-items: center;
      gap: 16px; text-align: center; padding: 40px 32px; max-width: 520px;
    }}
    svg {{ width: 64px; height: 64px; }}
    h2 {{ font-size: 1.3rem; font-weight: 700; }}
    .url {{ font-family: monospace; font-size: 12px; color: #64748b; word-break: break-all; }}
    .reason {{ font-size: 14px; color: #94a3b8; line-height: 1.6; }}
    a {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 10px 22px; border-radius: 10px;
      background: #6366f1; color: #fff;
      font-size: 14px; font-weight: 500; text-decoration: none; margin-top: 8px;
    }}
    a:hover {{ background: #818cf8; }}
  </style>
</head>
<body>
  <div class="card">
    <svg viewBox="0 0 64 64" fill="none">
      <circle cx="32" cy="32" r="28" stroke="#6366f1" stroke-width="3"/>
      <line x1="12" y1="12" x2="52" y2="52" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/>
    </svg>
    <h2>Cannot Load Page</h2>
    <p class="url">{url}</p>
    <p class="reason">{reason}</p>
    <a href="{url}" target="_blank" rel="noopener noreferrer">Open in new tab ↗</a>
  </div>
</body>
</html>"""
