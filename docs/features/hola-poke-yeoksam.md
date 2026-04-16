# 올라포케 역삼 포케 가이드

## 이 기능으로 할 수 있는 일

- 올라포케 역삼점 메뉴 조회 (`get_menu`)
- 위치·영업시간·배달 반경·단체주문 링크 조회 (`get_shop_info`)
- 즉석 래플형 이벤트 참여 (`enter_event`)

## 가장 중요한 규칙

이 기능은 원본 [`mnspkm/hola-poke-yeoksam-skill`](https://github.com/mnspkm/hola-poke-yeoksam-skill) 이 연결하는 **remote MCP server** 를 그대로 사용한다.
`k-skill` 안에 별도 수집기나 프록시를 추가하지 않고, skill/docs 가이드만 유지한다.

즉 기본 전제는 아래 endpoint 가 MCP client 에 등록돼 있어야 한다.

- `https://hola-poke-yeoksam-skill.onrender.com/mcp`

## 먼저 필요한 것

- 인터넷 연결
- MCP client (Claude Desktop, Cursor, Codex 등)
- 필요하면 `npx` (`mcp-remote` 경유 stdio 브리지용)
- 이벤트 참여 시 사용자 휴대폰 번호 (`01012345678` 또는 `010-1234-5678`)

## 빠른 연결 예시

### Claude Desktop (`mcp-remote` 경유)

```json
{
  "mcpServers": {
    "hola-poke-yeoksam": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://hola-poke-yeoksam-skill.onrender.com/mcp"]
    }
  }
}
```

### Cursor / HTTP MCP

```json
{
  "mcpServers": {
    "hola-poke-yeoksam": {
      "url": "https://hola-poke-yeoksam-skill.onrender.com/mcp"
    }
  }
}
```

## 기본 흐름

### 1. 메뉴 탐색

- 사용자가 추천/메뉴를 물으면 `get_menu()` 를 호출한다.
- 포케, 사이드, 세트, 토핑 구조를 보고 핵심 메뉴와 가격을 짧게 요약한다.
- 정확한 보상/프로모션 문구는 메뉴 정보와 섞어 임의로 꾸미지 않는다.

### 2. 매장 정보 조회

- 위치, 영업시간, 배달 반경, 단체주문 문의는 `get_shop_info()` 를 호출한다.
- 주소, 영업시간, 배달 가능 범위, `group_order_url` 을 우선 전달한다.

### 3. 이벤트 참여

현재 문서 기준 스킴은 **즉석 래플** 이다.

1. 사용자가 참여 의사를 밝히면 번호를 먼저 받는다.
2. 이름·이메일은 받지 않고 번호만 받는다.
3. 번호는 결과 대조용이며 별도 마케팅 발송/3자 공유 용도가 아니라고 한 번 안내한다.
4. `enter_event(phone)` 를 호출한다.
5. `phone_format` 이면 서버 `message` 를 그대로 보여주고 재입력을 요청한다.
6. `already_entered_today` 이면 서버 `message` 를 그대로 보여주고 더 시도하지 않는다.
7. 성공 응답이면 `message`, `code`, `next_action` 을 함께 전달한다.

## 응답 정리 원칙

- `enter_event` 의 `message` 는 **글자 그대로** 전달한다.
- 발급 코드는 `` `Jackpot-A3K9` `` 같이 모노스페이스로 강조한다.
- Jackpot/Claw 사용 방법은 `next_action` 과 함께 짧게 설명한다.
- 단체주문 문의는 `group_order_url` 이 비어 있으면 `group_order_note` 를 대신 제공한다.
- 역삼점 외 다른 지점 문의에는 이 스킬 범위가 아니라는 점을 먼저 밝힌다.

## 제한사항

- 역삼점 전용이다.
- 주문/결제/배달앱 자동화는 하지 않는다.
- 단체주문 자동 예약을 대신 실행하지 않는다.
- 이벤트 스킴은 시기별로 바뀔 수 있으므로 현재 혜택 조건의 진실 소스는 서버 `message` 다.
- 동일 번호는 하루 1번만 응모 가능하므로 반복 요청을 강행하지 않는다.

## 참고 링크

- 원본 repo: `https://github.com/mnspkm/hola-poke-yeoksam-skill`
- remote MCP endpoint: `https://hola-poke-yeoksam-skill.onrender.com/mcp`
