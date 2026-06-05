# startup-support data sources

## Primary Source

- K-Startup announcement data through `k-skill-proxy` `/v1/kstartup/announcements`
- Upstream dataset: 공공데이터포털 창업진흥원 K-Startup 조회서비스 (`15125364`)
- Authentication: proxy server injects `DATA_GO_KR_API_KEY`
- Update cadence: official K-Startup/data.go.kr feed cadence, not realtime monitoring

## Helper Scope

The helper searches announcement rows and returns the official detail URL for each result. It does not crawl local-government sites directly and does not synthesize eligibility, required documents, contacts, or award amounts when upstream data omits them.

## Fallback Order

1. Hosted proxy from `KSKILL_PROXY_BASE_URL` or `https://k-skill-proxy.nomadamas.org`
2. User-provided self-host proxy via `--proxy-base-url`
3. Dry-run URL inspection when network, proxy configuration, or upstream credentials are unavailable

For direct data.go.kr calls with a user-held key, use the narrower `kstartup-search` helper's `--direct` mode.

## Failure Modes

- Empty result page: no matching K-Startup announcements for the selected filters/page.
- HTTP 400: invalid query accepted by the helper but rejected by proxy validation.
- HTTP 503: proxy has no configured `DATA_GO_KR_API_KEY`.
- HTTP 502: upstream data.go.kr error or invalid response.
- Missing detail fields: answer with the returned official URL instead of inventing requirements, amounts, or contacts.
