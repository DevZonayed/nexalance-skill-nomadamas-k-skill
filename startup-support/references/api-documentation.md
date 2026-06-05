# startup-support API surface

`startup-support` is a read-only helper over the existing K-Startup proxy route. It does not add independent proxy endpoints.

## Proxy route used

```text
GET /v1/kstartup/announcements
```

Common query mapping:

- `region` -> `supt_regin`
- `keyword` -> `biz_pbanc_nm`
- `support_type` -> `supt_biz_clsfc`
- `deadline_only=true` -> `rcrt_prgs_yn=Y`
- `page` -> `page`
- `per_page` -> `perPage`

Authentication is handled by hosted or self-hosted `k-skill-proxy`. Users do not pass a data.go.kr service key to this helper.

## Python helper

```python
programs = search_startup_support(
    region="서울특별시",
    keyword="청년",
    support_type="사업화",
    deadline_only=True,
)
```

The CLI exposes the same search:

```bash
python3 startup-support/scripts/startup_support.py \
  --region 서울특별시 \
  --keyword 청년 \
  --deadline-only \
  --per-page 5 \
  --text
```

For request inspection without network or credentials:

```bash
python3 startup-support/scripts/startup_support.py \
  --region 서울특별시 \
  --keyword 청년 \
  --deadline-only \
  --dry-run
```

Detailed eligibility and application steps must be confirmed from each result's official `url`.
