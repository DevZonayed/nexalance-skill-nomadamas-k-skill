#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import unittest
from io import StringIO
from unittest import mock

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import startup_support  # noqa: E402


def make_args(**overrides: object) -> argparse.Namespace:
    defaults = {
        "region": "서울특별시",
        "keyword": "청년",
        "support_type": None,
        "deadline_only": False,
        "page": 1,
        "per_page": 5,
        "text": False,
        "dry_run": False,
        "timeout": 30,
        "proxy_base_url": "https://proxy.example",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class StartupSupportHelperTests(unittest.TestCase):
    def test_build_query_maps_startup_terms_to_kstartup_announcements(self) -> None:
        args = make_args(deadline_only=True, support_type="사업화")

        query = startup_support.build_query(args)

        self.assertEqual(query["supt_regin"], "서울특별시")
        self.assertEqual(query["biz_pbanc_nm"], "청년")
        self.assertEqual(query["supt_biz_clsfc"], "사업화")
        self.assertEqual(query["rcrt_prgs_yn"], "Y")
        self.assertEqual(query["page"], 1)
        self.assertEqual(query["perPage"], 5)
        self.assertEqual(query["returnType"], "json")

    def test_build_query_rejects_bad_page_size(self) -> None:
        with self.assertRaises(startup_support.HelperError):
            startup_support.build_query(make_args(per_page=0))
        with self.assertRaises(startup_support.HelperError):
            startup_support.build_query(make_args(per_page=101))

    def test_dry_run_uses_hosted_proxy_without_requests_dependency_or_api_key(self) -> None:
        out = StringIO()

        with mock.patch.object(sys, "stdout", out):
            rc = startup_support.run([
                "--region", "서울특별시",
                "--keyword", "청년",
                "--deadline-only",
                "--per-page", "5",
                "--dry-run",
                "--proxy-base-url", "https://proxy.example",
            ])

        self.assertEqual(rc, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["operation"], "announcements")
        self.assertTrue(payload["url"].startswith("https://proxy.example/v1/kstartup/announcements?"))
        self.assertIn("rcrt_prgs_yn=Y", payload["url"])
        self.assertNotIn("ServiceKey", payload["url"])

    def test_dry_run_uses_env_proxy_base_url_when_cli_option_is_absent(self) -> None:
        out = StringIO()

        with mock.patch.dict(os.environ, {"KSKILL_PROXY_BASE_URL": "https://env-proxy.example"}):
            with mock.patch.object(sys, "stdout", out):
                rc = startup_support.run(["--dry-run"])

        self.assertEqual(rc, 0)
        payload = json.loads(out.getvalue())
        self.assertTrue(payload["url"].startswith("https://env-proxy.example/v1/kstartup/announcements?"))

    def test_search_helper_uses_env_proxy_base_url_when_argument_is_absent(self) -> None:
        payload = {"data": []}
        calls = []

        def fake_http_get(url: str, *, timeout: int) -> tuple[int, str, str]:
            calls.append((url, timeout))
            return 200, "application/json", json.dumps(payload)

        with mock.patch.dict(os.environ, {"KSKILL_PROXY_BASE_URL": "https://env-proxy.example"}):
            with mock.patch.object(startup_support, "http_get", side_effect=fake_http_get):
                result = startup_support.search_startup_support()

        self.assertEqual(result, [])
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0][0].startswith("https://env-proxy.example/v1/kstartup/announcements?"))

    def test_search_startup_support_parses_proxy_payload_and_filters_deadline(self) -> None:
        payload = {
            "data": [
                {
                    "pbanc_sn": "A1",
                    "biz_pbanc_nm": "서울 청년 창업 지원",
                    "sprv_inst": "창업진흥원",
                    "supt_regin": "서울",
                    "supt_biz_clsfc": "사업화",
                    "pbanc_rcpt_bgng_dt": "20260601",
                    "pbanc_rcpt_end_dt": "20260630",
                    "aply_trgt": "예비창업자",
                    "detl_pg_url": "https://www.k-startup.go.kr/detail/A1",
                },
                {
                    "pbanc_sn": "B1",
                    "biz_pbanc_nm": "부산 청년 창업 지원",
                    "supt_regin": "부산",
                    "pbanc_rcpt_end_dt": "20260630",
                    "detl_pg_url": "https://www.k-startup.go.kr/detail/B1",
                },
                {
                    "pbanc_sn": "C1",
                    "biz_pbanc_nm": "전국 창업 지원",
                    "supt_regin": "전국",
                    "pbanc_rcpt_end_dt": "20260630",
                    "detl_pg_url": "https://www.k-startup.go.kr/detail/C1",
                }
            ]
        }

        with mock.patch.object(startup_support, "http_get", return_value=(200, "application/json", json.dumps(payload))):
            result = startup_support.search_startup_support(
                region="서울특별시",
                keyword="청년",
                deadline_only=True,
                proxy_base_url="https://proxy.example",
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "A1")
        self.assertEqual(result[0]["title"], "서울 청년 창업 지원")
        self.assertEqual(result[0]["deadline"], "2026-06-30")
        self.assertEqual(result[0]["url"], "https://www.k-startup.go.kr/detail/A1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
