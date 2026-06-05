---
name: startup-support
description: Search Korean K-Startup government startup support announcements through k-skill-proxy. Use when users ask about 창업 지원, 스타트업 지원금, 중소기업 지원, 정부 지원사업, or 모집 중인 창업 공고.
license: MIT
metadata:
  category: business-support
  locale: ko-KR
  phase: v1
---

# 스타트업 지원사업 조회

## What This Skill Does

`startup-support` searches K-Startup announcement data through the hosted or self-hosted `k-skill-proxy` `/v1/kstartup/announcements` route and summarizes matching startup support programs.

Use it for:

- "서울 청년 창업 지원사업 알려줘"
- "모집 중인 사업화 지원 공고 찾아줘"
- "정부 창업 지원사업 마감일 확인해줘"
- "예비창업자 대상 K-Startup 공고 요약해줘"

Do not use it for:

- Application submission or account/payment automation
- Final legal eligibility decisions
- Inventing requirements, award amounts, contacts, or application steps not present in upstream data
- Local-government site crawling outside K-Startup

## Data Source And Credentials

- Source: 공공데이터포털 창업진흥원 K-Startup 조회서비스 (`15125364`)
- Proxy route: `/v1/kstartup/announcements`
- User credential requirement: none for normal hosted-proxy use
- Proxy operator credential: `DATA_GO_KR_API_KEY`

Set `KSKILL_PROXY_BASE_URL` or pass `--proxy-base-url` only when using a self-host proxy. For direct data.go.kr calls with a user key, use `kstartup-search` and its `--direct` mode.

## Workflow

1. Translate the user request into K-Startup announcement filters.
2. Run a small bounded search first.
3. Check each returned row's official `url` before making eligibility-sensitive claims.
4. Cite the official URL when summarizing.

Common filter mapping:

- region -> `supt_regin`
- keyword -> `biz_pbanc_nm`
- support type -> `supt_biz_clsfc`
- deadline-only / recruiting-only -> `rcrt_prgs_yn=Y`

## CLI

```bash
python3 scripts/startup_support.py \
  --region 서울특별시 \
  --keyword 청년 \
  --deadline-only \
  --per-page 5 \
  --text
```

Dry-run request construction without network or credentials:

```bash
python3 scripts/startup_support.py \
  --region 서울특별시 \
  --keyword 청년 \
  --deadline-only \
  --dry-run
```

## Output

The helper returns:

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

## Failure Modes

- Empty result page: broaden filters or inspect additional pages.
- `400 bad_request`: invalid query rejected by proxy validation.
- `503 upstream_not_configured`: proxy lacks `DATA_GO_KR_API_KEY`.
- `502 upstream_error` or invalid response: data.go.kr returned an upstream error or non-JSON body.

## Maintainer Checks

```bash
python3 -m py_compile startup-support/scripts/startup_support.py startup-support/scripts/test_startup_support.py
PYTHONPATH=startup-support/scripts python3 -m unittest discover -s startup-support/scripts -p 'test_startup_support.py'
python3 startup-support/scripts/startup_support.py --region 서울특별시 --keyword 청년 --deadline-only --dry-run
```
