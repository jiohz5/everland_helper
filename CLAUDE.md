# 에버랜드 방문 내비게이터 Agent 팀

## WHY
정기권 방문(월 1~2회) 준비 정보 확인을 자동화하고, 출발 전 브리핑부터 파크 안 동선까지 하나의 대시보드로 내비게이터처럼 쓴다.

## WHAT
- 입력 자료: `업무설계서.md` 2장 (에버랜드 공식 웹·스마트예약, 주차·발렛 상태, 대기시간 이력, 기상청 예보, 후기, 자주 가는 식당)
- Sub Agent (`.claude/agents/`): `parking-strategy`(AI ③ 주차 전략) · `briefing-writer`(AI ① 동선·브리핑 작성) · `briefing-evaluator`(브리핑 검토) · `park-navigator`(AI ② 파크 안 재추천)
- 결과물: Task 7 코드(`tools/build_dashboard.py`)가 만드는 단일 HTML 대시보드 `output/<방문일>-everland-navigator.html` (중간 산출물 `data/<방문일>/`, 구조 기준 `reference/example.html`, 전체 흐름 `my-agent-team.html`)

## HOW
- Workflow는 `workflow.md`를 따른다: 코드 Task 2~5 → Router A(출발 전/파크 안) → Router B(발렛 확보/미확보) → AI ③ → AI ① ⇄ Evaluator(최대 3회, 초과 시 사람 확인) → Task 7
- 각 Sub Agent에는 전달받은 입력 파일 경로만 넘기고, 자기 역할 밖의 일은 위임하지 않는다.
- 공통 규칙
  - 입력 자료에 없는 숫자·시각·내용을 만들지 않고, 근거와 출처를 붙인다.
  - 더미 데이터(파크 밖 식당 혼잡 시간대)는 '더미'로 표시한다.
  - 로그인·예약·결제는 사람이 하며, 로그인은 전용 Edge 프로필(`.edge-profile`)만 쓴다.
  - 결과는 한국어로 작성한다.
