"""Crawl ANI Open directory JSON and render OpenList UrlTree output."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlsplit, urlunsplit

import httpx

from ani2openlist.utils.openlist import OpenlistUtils


FOLDER = "application/vnd.google-apps.folder"
VIDEO = frozenset(("video/mp4", "video/x-matroska"))
SUBTITLE = frozenset(("application/octet-stream",))
ARCHIVE = frozenset(("application/zip",))
FILES = VIDEO | SUBTITLE | ARCHIVE
SEASON = re.compile(r"\d{4}-(?:1|4|7|10)")
SIZE_UNITS = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
MEDIA_EXTENSIONS = frozenset(("mp4", "mkv"))
FILE_LINE = re.compile(r"^( *)(.*?):(\d+):(\d+):(https?://\S+)$")


def _timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def _size_bytes(value: str) -> int:
    number, unit = value.strip().split()
    return int(float(number) * SIZE_UNITS[unit.upper()])


def _rss_link(url: str, resource_domain: str) -> str:
    parts = urlsplit(url)
    filename = unquote(parts.path.rsplit("/", 1)[-1])
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    rss_extension = parse_qs(parts.query).get("d", [""])[0]
    if rss_extension in MEDIA_EXTENSIONS:
        extension = rss_extension
        path = parts.path
    elif extension in MEDIA_EXTENSIONS:
        path = parts.path[: -(len(extension) + 1)]
    else:
        return url
    sections = path.strip("/").split("/")
    if (
        len(sections) == 2
        and SEASON.fullmatch(sections[0])
        and tuple(map(int, sections[0].split("-"))) <= (2025, 7)
    ):
        title = re.match(r"^\[ANi\]\s*(.+?)\s+-\s+[^\[]+", filename)
        if title:
            folder = quote(title.group(1).strip(), safe="")
            path = f"/{sections[0]}/{folder}/{sections[1]}"
    return urlunsplit(("https", resource_domain, path, f"d={extension}", ""))


def convert_rss_links(
    source: str, resource_domain: str, video_only: bool = False
) -> tuple[str, dict[str, int]]:
    """Convert UrlTree media links to ANI RSS-style links without losing metadata."""
    lines = source.splitlines()
    counts = {"converted": 0, "unchanged": 0, "dropped": 0}
    converted_lines: list[str | None] = []
    for line in lines:
        match = FILE_LINE.fullmatch(line)
        if not match:
            converted_lines.append(line)
            continue
        prefix, name, size, created, url = match.groups()
        new_url = _rss_link(url, resource_domain)
        if new_url == url:
            counts["unchanged"] += 1
            is_video = (
                parse_qs(urlsplit(url).query).get("d", [""])[0] in MEDIA_EXTENSIONS
                or urlsplit(url).path.lower().endswith((".mp4", ".mkv"))
            )
            if video_only and not is_video:
                counts["dropped"] += 1
                converted_lines.append(None)
            else:
                converted_lines.append(line)
            continue
        counts["converted"] += 1
        converted_lines.append(f"{prefix}{name}:{size}:{created}:{new_url}")

    if video_only:
        for index in range(len(converted_lines) - 1, -1, -1):
            line = converted_lines[index]
            if line is None or not line.strip() or FILE_LINE.fullmatch(line):
                continue
            indent = len(line) - len(line.lstrip())
            next_content = next(
                (
                    child
                    for child in converted_lines[index + 1 :]
                    if child is not None and child.strip()
                ),
                None,
            )
            next_indent = (
                len(next_content) - len(next_content.lstrip())
                if next_content is not None
                else -1
            )
            if next_indent <= indent:
                converted_lines[index] = None
        converted_lines = [line for line in converted_lines if line is not None]

    return "\n".join(line for line in converted_lines if line is not None) + "\n", counts


def _quoted_path(value: str) -> str:
    # Preserve upstream bytes that Python decoded with surrogateescape.
    raw = value.encode("utf-8", "surrogateescape")
    return quote(raw, safe="/;:@=&")


def _link(base: str, path: str, resource_domain: str) -> str:
    quoted = _quoted_path(path)
    url = urlunsplit(("https", urlsplit(base).netloc, quoted, "d=true", ""))
    if resource_domain:
        parts = urlsplit(url)
        url = urlunsplit(("https", resource_domain, parts.path, parts.query, ""))
    return url


def _add_file(tree: dict[str, Any], base: str, path: str, item: dict[str, Any], resource_domain: str) -> None:
    current = tree
    for section in path.strip("/").split("/")[:-1]:
        current = current.setdefault(section, {})
    current[item["name"]] = [
        str(item["size"]),
        str(_timestamp(item["createdTime"])),
        _link(base, path + item["name"], resource_domain),
    ]


def _find_folders(value: Any) -> list[str]:
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(child, dict) and SEASON.fullmatch(key):
                found.append(key)
            found.extend(_find_folders(child))
    return found


def _state_file(output_dir: Path, root: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", urlsplit(root).netloc.lower()).strip("-")
    return output_dir / f"{slug}.state.json"


def load_state(output_dir: Path, root: str) -> dict[str, Any] | None:
    path = _state_file(output_dir, root)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def import_response(state: dict[str, Any], url: str, body: str, resource_domain: str) -> None:
    try:
        payload = json.loads(body)
    except ValueError:
        raise ValueError(f"ANI returned non-JSON for {url}") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("files"), list):
        raise ValueError(f"ANI directory response has no files list for {url}")

    state["visited"][url] = "ok"
    for item in payload["files"]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        mime = item.get("mimeType")
        if mime == FOLDER:
            child = url + _quoted_path(item["name"]) + "/"
            if child not in state["queue"] and child not in state["visited"]:
                state["queue"].append(child)
        elif mime in FILES:
            if not {"size", "createdTime"} <= item.keys():
                raise ValueError(f"ANI file metadata is incomplete for {item['name']}")
            _add_file(
                state["tree"], state["root"], urlsplit(url).path, item, resource_domain
            )
    if url in state["queue"]:
        state["queue"].remove(url)
    state["requests"] = len(state["visited"])


def import_rendered_batch(
    state: dict[str, Any], batch: list[dict[str, Any]], resource_domain: str
) -> None:
    """Import files rendered by ANI's own frontend, including folders when present."""
    for entry in batch:
        url = entry.get("url")
        files = entry.get("files")
        folders = entry.get("folders", [])
        if not isinstance(url, str) or not url.startswith(state["root"]):
            raise ValueError("Rendered batch contains an invalid directory URL")
        if not isinstance(files, list):
            raise ValueError(f"Rendered batch has no files list for {url}")
        if not isinstance(folders, list) or not all(isinstance(x, str) for x in folders):
            raise ValueError(f"Rendered batch has invalid folders for {url}")

        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                raise ValueError(f"Rendered file has no name for {url}")
            item = dict(item)
            try:
                if "size" not in item and "sizeText" in item:
                    item["size"] = str(_size_bytes(item["sizeText"]))
                if "createdTime" not in item and "createdTimeText" in item:
                    item["createdTime"] = (
                        datetime.strptime(item["createdTimeText"], "%Y-%m-%d %H:%M:%S")
                        .replace(tzinfo=timezone(timedelta(hours=8)))
                        .isoformat()
                    )
            except (KeyError, TypeError, ValueError):
                raise ValueError(f"Rendered metadata is invalid for {item.get('name')}") from None
            if not {"size", "createdTime"} <= item.keys():
                raise ValueError(f"Rendered metadata is incomplete for {item['name']}")
            _add_file(state["tree"], state["root"], urlsplit(url).path, item, resource_domain)

        for name in folders:
            child = url + _quoted_path(name) + "/"
            if child not in state["queue"] and child not in state["visited"]:
                state["queue"].append(child)

        state["visited"][url] = "ok"
        if url in state["queue"]:
            state["queue"].remove(url)
        state["requests"] = len(state["visited"])


def render_state(state: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _state_file(output_dir, state["root"]).write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "ani-open-url-tree.txt").write_text(
        OpenlistUtils.dict2structure(state["tree"]), encoding="utf-8"
    )
    (output_dir / "ani-open-address-tree.json").write_text(
        json.dumps(state["tree"], ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def crawl(
    root: str,
    output_dir: Path,
    max_requests: int = 50,
    concurrency: int = 3,
    timeout: float = 30,
    user_agent: str = "",
    cookies: dict[str, str] | None = None,
    resource_domain: str = "",
    serve: str = "",
) -> dict[str, Any]:
    root = root.rstrip("/") + "/"
    output_dir.mkdir(parents=True, exist_ok=True)
    state = load_state(output_dir, root)
    if state is None:
        state = {
            "version": 1,
            "root": root,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "queue": [root],
            "visited": {},
            "tree": {},
            "requests": 0,
            "complete": False,
        }
    if concurrency < 1 or max_requests < 1:
        raise ValueError("max_requests and concurrency must be positive")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": user_agent,
        "Cookie": "; ".join(f"{key}={value}" for key, value in (cookies or {}).items()),
    }
    headers = {key: value for key, value in headers.items() if value}
    semaphore = asyncio.Semaphore(concurrency)
    started = asyncio.get_running_loop().time()

    async with httpx.AsyncClient(
        trust_env=False, timeout=timeout, follow_redirects=False, headers=headers
    ) as client:
        async def one(url: str) -> tuple[str, str, list[Any]]:
            async with semaphore:
                if serve:
                    import subprocess

                    command = ("curl", "--noproxy", "*", "-sS", "-X", "POST", url)
                    result = await asyncio.to_thread(
                        subprocess.run, command, capture_output=True, text=True, timeout=timeout
                    )
                    if result.returncode:
                        raise RuntimeError(f"curl failed for {url}: {result.stderr[:200]}")
                    text = result.stdout
                else:
                    response = await client.post(url, content=b"{}")
                    text = response.text
                    if response.status_code != 200:
                        raise RuntimeError(f"ANI returned HTTP {response.status_code} for {url}")
                try:
                    payload = json.loads(text)
                except ValueError:
                    raise ValueError(f"ANI returned non-JSON for {url}") from None
                if not isinstance(payload, dict) or not isinstance(payload.get("files"), list):
                    raise ValueError(f"ANI directory response has no files list for {url}")
                items = []
                for item in payload["files"]:
                    if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                        continue
                    mime = item.get("mimeType")
                    if mime == FOLDER:
                        items.append({"kind": "folder", "name": item["name"], "item": item})
                    elif mime in FILES:
                        if not {"size", "createdTime"} <= item.keys():
                            raise ValueError(f"ANI file metadata is incomplete for {item['name']}")
                        items.append({"kind": "file", "name": item["name"], "item": item})
                return url, "ok", items

        exhausted = False
        while state["queue"] and state["requests"] < max_requests:
            batch = []
            for _ in range(min(concurrency, max_requests - state["requests"])):
                if not state["queue"]:
                    break
                url = state["queue"].popleft()
                if url not in state["visited"]:
                    batch.append(url)
            if not batch:
                continue
            results = await asyncio.gather(*(one(url) for url in batch))
            for parent, status, files in results:
                state["requests"] += 1
                state["visited"][parent] = status
                for entry in files:
                    if entry["kind"] == "file":
                        relative = urlsplit(parent).path
                        _add_file(
                            state["tree"], root, relative, entry["item"], resource_domain
                        )
                    else:
                        child = parent + _quoted_path(entry["name"]) + "/"
                        if child not in state["queue"] and child not in state["visited"]:
                            state["queue"].append(child)
            _state_file(output_dir, root).write_text(
                json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(
                f"requests={state['requests']} pending={len(state['queue'])} "
                f"visited={len(state['visited'])}",
                file=sys.stderr,
                flush=True,
            )
            if asyncio.get_running_loop().time() - started > 50:
                exhausted = True
                break

    state["complete"] = not state["queue"]
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    render_state(state, output_dir)
    return state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="https://openani.an-i.workers.dev/")
    parser.add_argument("--output-dir", type=Path, default=Path("exports"))
    parser.add_argument("--max-requests", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--user-agent", default="")
    parser.add_argument("--cookie", action="append", default=[])
    parser.add_argument("--resource-domain", default="")
    parser.add_argument("--import-response", type=Path)
    parser.add_argument(
        "--import-batch",
        type=Path,
        help="JSON array of {url,status,body} captured by the verified browser",
    )
    parser.add_argument(
        "--import-rendered",
        type=Path,
        help="JSON array of {url,files,folders} read from the verified browser DOM",
    )
    parser.add_argument("--url")
    parser.add_argument("--serve", default="", help="curl prefix for a temporary local relay")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--convert-rss", type=Path, help="Existing UrlTree backup to convert")
    parser.add_argument("--rss-output", type=Path, help="Converted UrlTree output path")
    parser.add_argument(
        "--video-only",
        action="store_true",
        help="With --convert-rss, omit non-video files unsupported by RSS feeds",
    )
    args = parser.parse_args()
    if args.convert_rss:
        if not args.rss_output:
            raise SystemExit("--rss-output is required with --convert-rss")
        domain = args.resource_domain or "resources.ani.rip"
        converted, counts = convert_rss_links(
            args.convert_rss.read_text(encoding="utf-8", errors="surrogateescape"),
            domain,
            args.video_only,
        )
        args.rss_output.write_text(
            converted, encoding="utf-8", errors="surrogateescape"
        )
        print(json.dumps(counts, ensure_ascii=False))
        return 0
    if args.summary:
        state = load_state(args.output_dir, args.root.rstrip("/") + "/")
        if state is None:
            raise SystemExit("No crawl state")
        print(json.dumps({
            "complete": state["complete"],
            "requests": state["requests"],
            "pending": len(state["queue"]),
            "visited": len(state["visited"]),
            "seasons": sorted(_find_folders(state["tree"])),
        }, ensure_ascii=False, indent=2))
        return 0 if state["complete"] else 2
    if args.import_response or args.import_batch or args.import_rendered:
        if sum(bool(x) for x in (args.import_response, args.import_batch, args.import_rendered)) != 1:
            raise SystemExit("Use only one import option")
        if args.import_rendered:
            batch = json.loads(
                args.import_rendered.read_text(encoding="utf-8", errors="surrogateescape")
            )
            root = args.root.rstrip("/") + "/"
            state = load_state(args.output_dir, root)
            if state is None:
                state = {
                    "version": 1,
                    "root": root,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "queue": [root],
                    "visited": {},
                    "tree": {},
                    "requests": 0,
                    "complete": False,
                }
            import_rendered_batch(state, batch, args.resource_domain)
            state["complete"] = not state["queue"]
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            render_state(state, args.output_dir)
            print(json.dumps({
                "complete": state["complete"], "requests": state["requests"],
                "pending": len(state["queue"]),
            }))
            return 0 if state["complete"] else 2
        if args.import_batch:
            if str(args.import_batch) == "-":
                    if hasattr(sys.stdin, "reconfigure"):
                        sys.stdin.reconfigure(encoding="utf-8", errors="surrogateescape")
                    batch = json.load(sys.stdin)
            else:
                batch = json.loads(
                    args.import_batch.read_text(encoding="utf-8", errors="surrogateescape")
                )
            root = args.root.rstrip("/") + "/"
            state = load_state(args.output_dir, root)
            if state is None:
                state = {
                    "version": 1,
                    "root": root,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "queue": [root],
                    "visited": {},
                    "tree": {},
                    "requests": 0,
                    "complete": False,
                }
            for entry in batch:
                if entry.get("status") != 200:
                    raise SystemExit(f"Captured response failed for {entry.get('url')}")
                import_response(
                    state, entry["url"], entry["body"], args.resource_domain
                )
            state["complete"] = not state["queue"]
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            render_state(state, args.output_dir)
            print(json.dumps({
                "complete": state["complete"], "requests": state["requests"],
                "pending": len(state["queue"]),
            }))
            return 0 if state["complete"] else 2
        if not args.url:
            raise SystemExit("--url is required with --import-response")
        root = args.root.rstrip("/") + "/"
        state = load_state(args.output_dir, root)
        if state is None:
            raise SystemExit("Start or import the root directory first")
        import_response(
            state, args.url, args.import_response.read_text(encoding="utf-8"), args.resource_domain
        )
        state["complete"] = not state["queue"]
        render_state(state, args.output_dir)
        print(json.dumps({
            "complete": state["complete"], "requests": state["requests"],
            "pending": len(state["queue"]),
        }))
        return 0 if state["complete"] else 2
    cookies = dict(cookie.split("=", 1) for cookie in args.cookie if "=" in cookie)
    state = asyncio.run(crawl(
        args.root, args.output_dir, args.max_requests, args.concurrency, args.timeout,
        args.user_agent, cookies, args.resource_domain, args.serve,
    ))
    print(json.dumps({
        "complete": state["complete"],
        "requests": state["requests"],
        "pending": len(state["queue"]),
    }))
    return 0 if state["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
