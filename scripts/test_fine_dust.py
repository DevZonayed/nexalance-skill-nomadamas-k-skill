import io
import json
import pathlib
import unittest
from contextlib import redirect_stdout
from unittest import mock

import fine_dust


FIXTURES = pathlib.Path(__file__).with_name("fixtures")


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FineDustTests(unittest.TestCase):
    def test_wgs84_coordinates_are_converted_to_air_korea_tm(self):
        tm_x, tm_y = fine_dust.wgs84_to_air_korea_tm(37.5665, 126.9780)

        self.assertAlmostEqual(tm_x, 198245.053, places=3)
        self.assertAlmostEqual(tm_y, 451586.838, places=3)

    def test_pick_station_prefers_nearest_station_for_coordinates(self):
        stations = load_fixture("fine-dust-stations.json")

        station = fine_dust.pick_station(
            fine_dust.extract_items(stations),
            lat=37.5665,
            lon=126.9780,
        )

        self.assertEqual(station["stationName"], "중구")

    def test_pick_station_prefers_specific_region_token_over_generic_city_token(self):
        stations = load_fixture("fine-dust-stations.json")

        station = fine_dust.pick_station(
            fine_dust.extract_items(stations),
            region_hint="서울 강남구",
        )

        self.assertEqual(station["stationName"], "강남구")

    def test_pick_station_falls_back_to_region_hint_without_coordinates(self):
        stations = load_fixture("fine-dust-stations.json")

        station = fine_dust.pick_station(
            fine_dust.extract_items(stations),
            region_hint="강남",
        )

        self.assertEqual(station["stationName"], "강남구")

    def test_build_report_combines_station_and_measurement_summary(self):
        stations = load_fixture("fine-dust-stations.json")
        measurements = load_fixture("fine-dust-measurements.json")

        report = fine_dust.build_report(
            station_items=fine_dust.extract_items(stations),
            measurement_items=fine_dust.extract_items(measurements),
            lat=37.5665,
            lon=126.9780,
        )

        self.assertEqual(report["station_name"], "중구")
        self.assertEqual(report["pm10"], {"value": "42", "grade": "보통"})
        self.assertEqual(report["pm25"], {"value": "19", "grade": "보통"})
        self.assertEqual(report["measured_at"], "2026-03-27 21:00")

    def test_cli_report_supports_fixture_inputs(self):
        station_path = FIXTURES / "fine-dust-stations.json"
        measurement_path = FIXTURES / "fine-dust-measurements.json"
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            fine_dust.main([
                "report",
                "--station-file",
                str(station_path),
                "--measurement-file",
                str(measurement_path),
                "--lat",
                "37.5665",
                "--lon",
                "126.9780",
            ])

        rendered = stdout.getvalue()
        self.assertIn("측정소: 중구", rendered)
        self.assertIn("PM10: 42 (보통)", rendered)
        self.assertIn("PM2.5: 19 (보통)", rendered)

    def test_live_station_lookup_converts_lat_lon_before_nearby_request(self):
        args = fine_dust.parse_args(["report", "--lat", "37.5665", "--lon", "126.9780"])
        recorded_calls = []

        def fake_fetch_json(url, params):
            recorded_calls.append((url, params))
            return {"response": {"body": {"items": [{"stationName": "중구", "addr": "서울 중구 서소문로 124"}]}}}

        with (
            mock.patch.object(fine_dust, "get_required_secret", return_value="test-secret"),
            mock.patch.object(fine_dust, "fetch_json", side_effect=fake_fetch_json),
        ):
            payload = fine_dust.fetch_station_payload(args)

        items = fine_dust.extract_items(payload)
        self.assertEqual(items[0]["stationName"], "중구")
        self.assertEqual(len(recorded_calls), 1)

        request_url, request_params = recorded_calls[0]
        self.assertTrue(request_url.endswith("/getNearbyMsrstnList"))
        self.assertAlmostEqual(request_params["tmX"], 198245.053, places=3)
        self.assertAlmostEqual(request_params["tmY"], 451586.838, places=3)
        self.assertNotIn("dmX", request_params)
        self.assertNotIn("dmY", request_params)

    def test_live_station_lookup_falls_back_to_region_search_after_empty_nearby_result(self):
        args = fine_dust.parse_args(["report", "--lat", "37.5665", "--lon", "126.9780", "--region-hint", "서울 강남구"])
        recorded_calls = []

        def fake_fetch_json(url, params):
            recorded_calls.append((url, params))
            if url.endswith("/getNearbyMsrstnList"):
                return {"response": {"body": {"items": []}}}
            if url.endswith("/getMsrstnList"):
                return {"response": {"body": {"items": [{"stationName": "강남구", "addr": "서울 강남구 학동로 426"}]}}}
            raise AssertionError(f"unexpected URL: {url}")

        with (
            mock.patch.object(fine_dust, "get_required_secret", return_value="test-secret"),
            mock.patch.object(fine_dust, "fetch_json", side_effect=fake_fetch_json),
        ):
            payload = fine_dust.fetch_station_payload(args)

        items = fine_dust.extract_items(payload)
        self.assertEqual(items[0]["stationName"], "강남구")
        self.assertEqual([url.rsplit("/", 1)[-1] for url, _ in recorded_calls], ["getNearbyMsrstnList", "getMsrstnList"])
        fallback_params = recorded_calls[1][1]
        self.assertEqual(fallback_params["addr"], "서울 강남구")


if __name__ == "__main__":
    unittest.main()
