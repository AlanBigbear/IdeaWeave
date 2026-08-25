import ipaddress
import re
import socket
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup

MAX_HTML_BYTES = 2_000_000
MAX_TEXT_CHARS = 6000
MAX_REDIRECTS = 3
TIMEOUT = 10.0
TOTAL_DEADLINE = 25.0

# 常见跟踪参数（含 B 站/CN 生态常用的一串）
_TRACKING_PARAMS = {
    "trackid", "track_id", "spm_id_from", "spm", "from_spmid", "from",
    "vd_source", "share_source", "share_medium", "share_plat", "share_tag",
    "share_session_id", "bbid", "ts", "t", "timestamp", "utm_source",
    "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
    "referrer", "referer", "pf", "seid", "request_id", "creative_id",
    "linked_creative_id", "caid", "resource_id", "source_id", "pvid",
    "session_id", "sid", "trace", "click_id", "cvid",
    "adtype", "image_material_id", "title_material_id", "title_encode",
    "duid", "os", "buvid", "idfa", "android_id",
}


def clean_url(url: str) -> str:
    """去掉跟踪参数，保留核心链接（BV 号、专栏 ID 等路径信息不丢）。"""
    url = (url or "").strip()
    try:
        parts = urlsplit(url)
    except ValueError:
        return url
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return url
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in _TRACKING_PARAMS and not value.startswith("__")
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

BROWSER_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

_BILIBILI_VIDEO_RE = re.compile(r"/video/(BV[0-9A-Za-z]+)")
_BILIBILI_AID_RE = re.compile(r"/video/av(\d+)")


class FetchError(ValueError):
    """非法链接或抓取失败。detail 为给用户看的中文提示。"""


@dataclass
class FetchResult:
    url: str
    title: str
    site_name: str
    text: str
    truncated: bool


def _assert_safe_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"}:
        raise FetchError("只支持 http/https 链接")
    host = parts.hostname
    if not host:
        raise FetchError("链接格式不正确")
    try:
        infos = socket.getaddrinfo(host, parts.port or (443 if parts.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise FetchError("域名解析失败，请检查链接") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise FetchError("禁止访问内网或本机地址")


def _meta_content(soup: BeautifulSoup, *names: str, attr: str = "name") -> str:
    for name in names:
        tag = soup.find("meta", attrs={attr: name})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
    return ""


def _extract_text(soup: BeautifulSoup) -> tuple[str, str]:
    for tag in soup(["script", "style", "noscript", "iframe", "svg", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    title = _meta_content(soup, "og:title", attr="property") or (
        soup.title.get_text().strip() if soup.title else ""
    )
    node = soup.find("article") or soup.find("main") or soup.body or soup
    lines = [line.strip() for line in node.get_text("\n").splitlines()]
    text = "\n".join(line for line in lines if line)
    if len(text) < 120:
        fallback = _meta_content(soup, "description") or _meta_content(
            soup, "og:description", attr="property"
        )
        if fallback:
            text = f"{text}\n{fallback}".strip()
    return title, text


def _try_bilibili_api(url: str) -> FetchResult | None:
    """B 站视频/番剧走官方 JSON API，规避数据中心 IP 抓 HTML 被风控返回 412。"""
    host = (urlsplit(url).hostname or "").lower()
    if host not in {"bilibili.com", "www.bilibili.com", "m.bilibili.com", "b23.tv"}:
        return None

    path = urlsplit(url).path
    bvid = aid = None
    m = _BILIBILI_VIDEO_RE.search(path)
    if m:
        bvid = m.group(1)
    else:
        m = _BILIBILI_AID_RE.search(path)
        if m:
            aid = m.group(1)

    # b23.tv 短链先解出真实地址
    if not bvid and not aid and host == "b23.tv":
        try:
            with httpx.Client(headers=BROWSER_HEADERS, follow_redirects=True, timeout=TIMEOUT) as c:
                r = c.head(url)
                m = _BILIBILI_VIDEO_RE.search(r.url.path)
                if m:
                    bvid = m.group(1)
                else:
                    m = _BILIBILI_AID_RE.search(r.url.path)
                    if m:
                        aid = m.group(1)
        except httpx.HTTPError:
            return None

    if not bvid and not aid:
        return None

    params = {"bvid": bvid} if bvid else {"aid": aid}
    try:
        resp = httpx.get(
            "https://api.bilibili.com/x/web-interface/view",
            params=params,
            headers=BROWSER_HEADERS,
            timeout=TIMEOUT,
        )
    except httpx.HTTPError:
        return None
    if resp.status_code != 200:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None
    if data.get("code") != 0 or not data.get("data"):
        return None

    d = data["data"]
    title = str(d.get("title") or "").strip()
    owner = str((d.get("owner") or {}).get("name") or "").strip()
    desc = str(d.get("desc") or "").strip()
    stat = d.get("stat") or {}
    meta = []
    for label, key in (("播放", "view"), ("弹幕", "danmaku"), ("点赞", "like"), ("投币", "coin")):
        if stat.get(key):
            meta.append(f"{label} {stat[key]}")
    lines = [title]
    if owner:
        lines.append(f"UP主：{owner}")
    if desc:
        lines.append(desc)
    if meta:
        lines.append(" / ".join(meta))
    text = "\n".join(line for line in lines if line)
    if not text:
        return None
    truncated = len(text) > MAX_TEXT_CHARS
    return FetchResult(
        url=clean_url(url),
        title=title or "bilibili",
        site_name="bilibili",
        text=text[:MAX_TEXT_CHARS],
        truncated=truncated,
    )


def fetch_webpage(url: str) -> FetchResult:
    url = url.strip()
    # B 站视频优先走官方 JSON API，规避风控
    bili = _try_bilibili_api(url)
    if bili is not None:
        return bili
    current = url
    deadline = time.monotonic() + TOTAL_DEADLINE
    body = b""
    with httpx.Client(
        follow_redirects=False,
        timeout=TIMEOUT,
        headers=BROWSER_HEADERS,
    ) as client:
        response = None
        for _ in range(MAX_REDIRECTS + 1):
            _assert_safe_url(current)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise FetchError("抓取超时，页面响应太慢，试试粘贴文本模式")
            try:
                response = client.get(current)
            except httpx.HTTPError as exc:
                raise FetchError(f"访问失败：{exc.__class__.__name__}") from exc
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location", "")
                if not location:
                    break
                current = urljoin(current, location)
                continue
            break
        if response is None or response.status_code >= 400:
            status = getattr(response, "status_code", "无响应")
            raise FetchError(f"目标页面返回 {status}，无法抓取（需要登录或已被删除的页面抓不到）")
        try:
            # 流式限量读取，避免超大页面被完整下载
            with client.stream("GET", current) as stream:
                for chunk in stream.iter_bytes(chunk_size=65536):
                    body += chunk
                    if len(body) >= MAX_HTML_BYTES:
                        break
        except httpx.HTTPError as exc:
            raise FetchError(f"访问失败：{exc.__class__.__name__}") from exc

    html = body[:MAX_HTML_BYTES].decode(response.encoding or "utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    title, text = _extract_text(soup)
    site_name = _meta_content(soup, "og:site_name", attr="property") or urlsplit(current).netloc
    if not text:
        raise FetchError("页面没有可分析的正文（可能是纯 JS 渲染页面，试试粘贴文本模式）")
    truncated = len(text) > MAX_TEXT_CHARS
    return FetchResult(
        url=clean_url(current),
        title=title or site_name,
        site_name=site_name,
        text=text[:MAX_TEXT_CHARS],
        truncated=truncated,
    )
