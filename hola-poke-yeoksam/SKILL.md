---
name: hola-poke-yeoksam
description: 올라포케 역삼점의 메뉴·매장 정보·이벤트 참여 흐름을 remote MCP 서버 기준으로 안내한다.
license: MIT
metadata:
  category: food
  locale: ko-KR
  phase: v1
---

# Hola Poke Yeoksam

## What this skill does

올라포케 역삼점 전용 remote MCP server(`https://hola-poke-yeoksam-skill.onrender.com/mcp`)를 기준으로 아래 작업을 처리한다.

- `get_menu()` 로 포케·사이드·세트·토핑 메뉴를 안내한다.
- `get_shop_info()` 로 위치, 영업시간, 배달 반경, 단체주문 URL을 안내한다.
- `enter_event(phone)` 로 즉석 래플형 이벤트 참여를 돕는다.

## When to use

- "올라포케 메뉴 뭐 있어?"
- "역삼 포케 추천해줘"
- "올라포케 역삼점 어디야?"
- "올라포케 단체주문 링크 줘"
- "올라포케 이벤트 참여해줘"

## When not to use

- 역삼점이 아닌 다른 올라포케 지점 문의
- 주문/결제/배달앱 자동화는 하지 않는다.
- 단체주문 자동 예약 실행
- 사용자 동의 없는 번호 수집 또는 반복 응모 시도

## Prerequisites

- remote MCP server 연결
- 메뉴/매장 정보 조회용 MCP client
- `enter_event` 호출 시 사용자 휴대폰 번호 (`01012345678` 또는 `010-1234-5678`)

## Workflow

### 1. 메뉴/매장 정보 조회

- 메뉴가 궁금하면 `get_menu()` 를 호출한다.
- 위치·영업시간·단체주문 문의는 `get_shop_info()` 를 호출한다.
- 응답은 메뉴명, 가격, 주소, 영업시간, URL 같은 핵심 정보 위주로 짧게 정리한다.

### 2. 이벤트 참여

현재 스킴은 **즉석 래플** 이다. 식사 주문 시 쓸 수 있는 혜택 코드가 발급될 수 있고, 동일 번호는 하루 1번만 응모할 수 있다.

1. 사용자가 참여 의사를 밝히면 휴대폰 번호를 먼저 받는다.
2. 이름·이메일은 받지 않고 번호만 받는다.
3. 번호는 결과 대조용이며 별도 마케팅 발송/3자 공유 용도가 아니라고 한 번 고지한다.
4. `enter_event(phone)` 를 호출한다.
5. `phone_format` 이면 서버 `message` 를 그대로 보여주고 다시 받는다.
6. `already_entered_today` 이면 서버 `message` 를 그대로 보여주고 더 이상 재시도하지 않는다.
7. 정상 응답이면 `message`, `code`, `next_action` 을 함께 전달한다.

### 3. 응답 원칙

- `enter_event` 의 `message` 는 글자 그대로 전달한다.
- 발급 코드는 `` `Jackpot-A3K9` `` 같은 모노스페이스로 강조한다.
- Jackpot/Claw 사용 경로는 `next_action` 과 함께 안내한다.
- 단체주문 문의는 `get_shop_info()` 의 `group_order_url` 이 비어 있으면 `group_order_note` 를 대신 안내한다.

## Remote MCP setup note

이 스킬은 자체 수집기를 vendoring 하지 않는다. 원본 참고 repo와 동일하게 아래 remote MCP endpoint 를 붙여 사용하는 전제다.

- endpoint: `https://hola-poke-yeoksam-skill.onrender.com/mcp`
- reference repo: `https://github.com/mnspkm/hola-poke-yeoksam-skill`

## Done when

- 메뉴/매장 정보 요청에 핵심 정보를 전달했다.
- 이벤트 참여 요청에 번호 확인 → `enter_event` → 결과 전달 흐름을 지켰다.
- 반복 응모 제한과 서버 `message` 원문 전달 원칙을 지켰다.

## Notes

- 역삼점 전용 스킬이다.
- 이벤트 스킴은 시기별로 달라질 수 있으므로 보상 조건의 진실 소스는 서버 응답의 `message` 필드다.
- Jackpot 당첨은 번호 주인 확인이 필요할 수 있다.
- 동일 번호는 KST 기준 하루 1번만 응모한다.
