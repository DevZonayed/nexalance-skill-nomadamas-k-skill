# startup-support

`startup-support` helps agents answer Korean startup support-program questions by searching K-Startup announcement data through `k-skill-proxy`.

Use it for questions such as:

- "서울 청년 창업 지원사업 찾아줘"
- "모집 중인 사업화 지원 공고 알려줘"
- "이번 달 확인할 K-Startup 공고를 요약해줘"

Do not use it for application submission, legal eligibility decisions, payment automation, or grant amount calculation. The final source of truth is always the official announcement URL returned in each result.

## Data Flow

The helper calls:

```text
GET /v1/kstartup/announcements
```

It maps user-friendly terms onto the K-Startup query fields:

- `region` -> `supt_regin`
- `keyword` -> `biz_pbanc_nm`
- `support_type` -> `supt_biz_clsfc`
- `deadline_only` -> `rcrt_prgs_yn=Y`

The hosted proxy injects the data.go.kr API key. A user running the helper does not need `DATA_GO_KR_API_KEY`.

## CLI

```bash
python3 startup-support/scripts/startup_support.py \
  --region 서울특별시 \
  --keyword 청년 \
  --deadline-only \
  --per-page 5 \
  --text
```

Use dry-run when reviewing request construction without network access:

```bash
python3 startup-support/scripts/startup_support.py \
  --region 서울특별시 \
  --keyword 청년 \
  --deadline-only \
  --dry-run
```

## Output

The helper normalizes K-Startup announcement rows into:

```json
{
  "programs": [
    {
      "id": "A1",
      "title": "서울 청년 창업 지원",
      "organization": "창업진흥원",
      "region": "서울",
      "support_type": "사업화",
      "amount": "공식 공고 확인",
      "deadline": "2026-06-30",
      "target": "예비창업자",
      "contact": "",
      "url": "https://www.k-startup.go.kr/...",
      "source": "K-Startup",
      "last_updated": "2026-06-01"
    }
  ]
}
```

## Verification

```bash
python3 -m py_compile startup-support/scripts/startup_support.py startup-support/scripts/test_startup_support.py
PYTHONPATH=startup-support/scripts python3 -m unittest discover -s startup-support/scripts -p 'test_startup_support.py'
python3 startup-support/scripts/startup_support.py --region 서울특별시 --keyword 청년 --deadline-only --dry-run
```

The root `npm run ci` also compiles and runs this helper's tests.

## Failure Modes

- `400 bad_request`: invalid query parameter rejected by `k-skill-proxy`.
- `503 upstream_not_configured`: proxy lacks a configured `DATA_GO_KR_API_KEY`.
- `502 upstream_error` or `upstream_invalid_response`: data.go.kr returned an error, non-JSON body, or invalid payload.
- Empty `programs`: no matching announcements in the selected page. Broaden filters or check additional pages.
