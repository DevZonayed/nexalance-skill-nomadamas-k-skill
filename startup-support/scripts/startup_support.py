#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Sequence

DEFAULT_PROXY_BASE_URL = "https://k-skill-proxy.nomadamas.org"
REGION_ALIASES = {
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "경기도": "경기",
    "강원특별자치도": "강원",
    "강원도": "강원",
    "충청북도": "충북",
    "충청남도": "충남",
    "전북특별자치도": "전북",
    "전라북도": "전북",
    "전라남도": "전남",
    "경상북도": "경북",
    "경상남도": "경남",
    "제주특별자치도": "제주",
}


class HelperError(RuntimeError):
    pass


def _compact(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _yyyymmdd_to_iso(value: str | None) -> str:
    if not value:
        return ""
    digits = "".join(char for char in value if char.isdigit())
    if len(digits) != 8:
        return value
    return f"{digits[0:4]}-{digits[4:6]}-{digits[6:8]}"


def build_query(args: argparse.Namespace) -> dict[str, str | int]:
    if args.page < 1:
        raise HelperError("--page must be >= 1")
    if args.per_page < 1 or args.per_page > 100:
        raise HelperError("--per-page must be in [1, 100]")

    query: dict[str, str | int] = {
        "page": args.page,
        "perPage": args.per_page,
        "returnType": "json",
    }
    region = _compact(args.region)
    keyword = _compact(args.keyword)
    support_type = _compact(args.support_type)
    if region and region != "전국":
        query["supt_regin"] = region
    if keyword:
        query["biz_pbanc_nm"] = keyword
    if support_type:
        query["supt_biz_clsfc"] = support_type
    if args.deadline_only:
        query["rcrt_prgs_yn"] = "Y"
    return query


def build_url(query: dict[str, str | int], proxy_base_url: str = DEFAULT_PROXY_BASE_URL) -> str:
    base = proxy_base_url.rstrip("/")
    encoded = urllib.parse.urlencode([(key, str(value)) for key, value in query.items()])
    return f"{base}/v1/kstartup/announcements?{encoded}"


def http_get(url: str, *, timeout: int) -> tuple[int, str, str]:
    request = urllib.request.Request(
        url,
        headers={
            "accept": "application/json",
            "user-agent": "k-skill/startup-support",
        },
        method="GET",
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, response.headers.get("content-type", ""), body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        content_type = exc.headers.get("content-type", "") if exc.headers else ""
        return exc.code, content_type, body
    except urllib.error.URLError as exc:
        raise HelperError(f"network error: {exc.reason}") from exc


def _rows_from_payload(payload: dict[str, object]) -> list[dict[str, object]]:
    rows = payload.get("data", [])
    if not isinstance(rows, list):
        raise HelperError("proxy response data must be a list")
    normalized: list[dict[str, object]] = []
    for row in rows:
        if isinstance(row, dict):
            normalized.append(row)
    return normalized


def _text(row: dict[str, object], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _canonical_region(value: str | None) -> str:
    text = _compact(value)
    if not text:
        return ""
    compacted = text.replace(" ", "")
    return REGION_ALIASES.get(compacted, compacted)


def _region_parts(value: str) -> list[str]:
    return [
        _canonical_region(part)
        for part in value.replace("/", ",").replace("|", ",").split(",")
        if _canonical_region(part)
    ]


def _matches_region(row: dict[str, object], requested_region: str | None) -> bool:
    requested = _canonical_region(requested_region)
    if not requested or requested == "전국":
        return True
    row_region = _text(row, "supt_regin", "region")
    if not row_region:
        return False
    return requested in _region_parts(row_region)


def _program_from_row(row: dict[str, object]) -> dict[str, str]:
    program_id = _text(row, "pbanc_sn", "id")
    title = _text(row, "biz_pbanc_nm", "title")
    end_date = _text(row, "pbanc_rcpt_end_dt", "deadline")
    return {
        "id": program_id,
        "title": title,
        "organization": _text(row, "sprv_inst", "organization"),
        "region": _text(row, "supt_regin", "region", "전국"),
        "support_type": _text(row, "supt_biz_clsfc", "support_type", "기타"),
        "amount": _text(row, "supt_cn", "amount", "공식 공고 확인"),
        "deadline": _yyyymmdd_to_iso(end_date),
        "target": _text(row, "aply_trgt", "target"),
        "contact": _text(row, "biz_gdnc_url", "contact"),
        "url": _text(row, "detl_pg_url", "url"),
        "source": "K-Startup",
        "last_updated": _yyyymmdd_to_iso(_text(row, "pbanc_rcpt_bgng_dt", "last_updated")),
    }


def search_startup_support(
    region: str = "전국",
    keyword: str | None = None,
    support_type: str | None = None,
    deadline_only: bool = False,
    *,
    page: int = 1,
    per_page: int = 10,
    proxy_base_url: str | None = None,
    timeout: int = 30,
) -> list[dict[str, str]]:
    args = argparse.Namespace(
        region=region,
        keyword=keyword,
        support_type=support_type,
        deadline_only=deadline_only,
        page=page,
        per_page=per_page,
    )
    base_url = proxy_base_url or os.environ.get("KSKILL_PROXY_BASE_URL", DEFAULT_PROXY_BASE_URL)
    url = build_url(build_query(args), proxy_base_url=base_url)
    status, _, body = http_get(url, timeout=timeout)
    if status < 200 or status >= 300:
        raise HelperError(f"proxy returned HTTP {status}: {body[:300]}")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HelperError("proxy response was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise HelperError("proxy response must be a JSON object")
    rows = [row for row in _rows_from_payload(payload) if _matches_region(row, region)]
    return [_program_from_row(row) for row in rows]


def get_startup_program_detail(program_id: str) -> None:
    return None


class StartupSupportAPI:
    def search_programs(
        self,
        region: str = "전국",
        keyword: str | None = None,
        support_type: str | None = None,
        deadline_only: bool = False,
    ) -> list[dict[str, str]]:
        return search_startup_support(region, keyword, support_type, deadline_only)

    def get_program_detail(self, program_id: str) -> None:
        return get_startup_program_detail(program_id)


def _print_text(programs: Sequence[dict[str, str]]) -> None:
    if not programs:
        print("일치하는 K-Startup 지원사업 공고가 없습니다.")
        return
    for index, program in enumerate(programs, start=1):
        deadline = program["deadline"] or "마감일 공고 확인"
        url = program["url"] or "상세 URL 없음"
        print(f"{index}. {program['title']} | {program['region']} | {deadline}")
        print(f"   {url}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="K-Startup 창업 지원사업 공고 조회")
    parser.add_argument("--region", default="전국")
    parser.add_argument("--keyword")
    parser.add_argument("--support-type")
    parser.add_argument("--deadline-only", action="store_true")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--per-page", type=int, default=10)
    parser.add_argument("--text", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--proxy-base-url", default=os.environ.get("KSKILL_PROXY_BASE_URL", DEFAULT_PROXY_BASE_URL))
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        query = build_query(args)
        url = build_url(query, proxy_base_url=args.proxy_base_url)
        if args.dry_run:
            print(json.dumps({"operation": "announcements", "query": query, "url": url}, ensure_ascii=False, indent=2))
            return 0
        programs = search_startup_support(
            region=args.region,
            keyword=args.keyword,
            support_type=args.support_type,
            deadline_only=args.deadline_only,
            page=args.page,
            per_page=args.per_page,
            proxy_base_url=args.proxy_base_url,
            timeout=args.timeout,
        )
    except HelperError as exc:
        parser.error(str(exc))
    if args.text:
        _print_text(programs)
    else:
        print(json.dumps({"programs": programs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
