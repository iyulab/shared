# Cycle 01: docket #240 이행 — 재사용 워크플로 timeout-minutes
Date: 2026-09-10
Root: `claudedocs/`
Budget: 10
Start: 1
Status: complete

## Re-plan

트리거 ⚪ NONE. 대화 컨텍스트(최우선)에서 docket #240 트라이지가 **ACCEPT** 로 끝나 있고, 그 판정이 곧 이 사이클의 스코프다 — `iyulab/shared` topic, requester `iyulab/node-packages`, 이 세션에서 `iyulab/shared` 로 claim 완료. `ROADMAP.md` P1 에 해당한다.

이 런이 처음이라 상속 Carry-Forward 없음. 직전 런 중단 여부 해당 없음.

**부수 조치**: `iyulab/shared` topic 에 등록된 워커가 없었다(#186 코멘트가 지적한 상태 그대로) — `turn=assignee` 인 아이템이 아무의 `mine` 에도 뜨지 않는다. `iyulab/shared` 를 이 topic 워커로 등록해 닫았다.

## Scope & Implementation

두 재사용 워크플로의 job 에 `timeout-minutes: 20` 선언.

- `.github/workflows/publish-npm.yml` — `jobs.publish`
- `.github/workflows/cleanup-expired-artifacts.yml` — `jobs.cleanup`

**STEP 1 설계**: 대부분 트라이지 단계에서 이미 조사됨(caller 허용 키 목록, `Unexpected value 'timeout-minutes'`, 값 근거). 이 사이클에서 추가로 판단한 것 하나 — cleanup 에 step-level timeout 도 둘 것인가. job 이 사실상 단일 스텝이라 중복이므로 job-level 만 둔다(D-03).

**근거 주석을 함께 남겼다.** 이 리포의 확립된 관례다(`node_version` 기본값 옆 주석, #186 의 "다음에 이 줄을 만지는 사람이 근거 없이 되돌리지 않게"). 주석 언어는 바로 위 기존 주석과 맞춰 한국어 — 리포의 기존 언어를 임의로 바꾸지 않는다.

주석이 담은 두 가지 사실: ⑴ caller 는 이 키를 가질 수 없다(그래서 여기 있어야 한다) ⑵ 없으면 6시간 기본값이고, `concurrency` 그룹이 소비자 리포 단위라 행 걸린 run 하나가 그 패키지의 후속 게시를 그만큼 봉쇄한다.

## Verification & Defect Resolution

수용 기준을 검사 **전에** 고정: ① YAML 파싱 통과 ② `timeout-minutes === 20` 이고 문자열이 아닌 int ③ 기존 키 불변 ④ 추가 전용 diff · CRLF 유지 ⑤ 린터(있으면).

HEAD 와 파싱 구조를 직접 대조한 결과 (PyYAML):

```
publish-npm.yml   job keys added {'timeout-minutes': 20} · removed [] · changed {} · steps 10/10
cleanup-…yml      job keys added {'timeout-minutes': 20} · removed [] · changed {} · steps 1/1
top-level (added, removed, changed) = (set(), set(), set())   ← 양쪽 모두
git diff --numstat: 7+/0-, 5+/0-      file: 양쪽 CRLF 유지
RESULT: PASS
```

- ⑤ **미실행**: 이 환경에 `actionlint`·`yamllint` 없음. 이것 하나 때문에 의존성을 추가하지 않는다.
- **실제 표면 구동 미실행**: 워크플로의 실제 표면은 GitHub Actions run 이고, push 없이는 구동할 수 없다(push 는 사람 게이트). "동작 확인"이 아니라 "구조 검증"까지가 이 사이클의 증거다 — 그 이상을 주장하지 않는다.

첫 검증 시도에서 실패가 하나 났는데 **파일이 아니라 내가 적은 기대치가 틀린 것**이었다(publish 스텝 수를 9로 적었으나 실제 10). HEAD 대조 방식으로 바꿔 재검증했고, 그 방식이 애초에 더 강한 증거다.

정의상 결함 발견 0건.

## Reflection

**1. 스코프 적합** — #240 의 요청("declare `timeout-minutes` on the job(s) inside `publish-npm.yml` (and any sibling reusable workflows in this repo)")을 문자 그대로 충족. sibling 은 정확히 하나였다.

**2. 잠재 결함** — 하나 있으나 결함이 아니라 **의도된 열화**로 판단:
cleanup job 은 아티팩트 전체를 페이지네이션한 뒤 개별 삭제를 루프로 돈다. 만료 아티팩트가 매우 많은 리포라면 20분에 걸려 중도 종료될 수 있다. 다만 ⑴ 전역 지침상 이 조직의 아티팩트는 `retention-days` 1–7 로 짧게 잡혀 있어 누적량이 작고 ⑵ 주간 cron 이라 잘린 잔량은 다음 주 run 이 이어 받는다(삭제는 멱등). ⇒ "20분 걸려 일부만 지움" 이 "6시간 매달림" 보다 낫다. 로그에 남기고 임계 신호가 나오면 조정한다.

**3. 구조 개선 기회** — 근거 주석이 5줄로 길다. 클래스 규칙이 `CONTRIBUTING.md` 에 한 번 적혀 있으면 각 워크플로 주석은 한 줄 포인터로 줄어든다. 이건 별도 제안이 아니라 **다음 사이클 스코프(P2)** 자체다.

**4. 철학 드리프트** — 없음. 소비자 도메인 개념 유입 0, 신규 입력 표면 0, 하위호환(소비자가 아무것도 안 해도 됨). 재사용 워크플로가 자기 실행 가드를 소유하는 것은 이미 `concurrency` 로 확립된 패턴의 연장.

**5. 로드맵 영향 · 창발 스코프**
- (a) P1 의 미결 항목 해소 → `HISTORY.md` 로 이관. P1 은 "같은 클래스의 다른 키가 더 필요한가(조사 필요)" 만 남는다.
- (b) 세 렌즈에서 도출:
  - **소비자 렌즈** — 소비 리포는 `@a812e48` SHA 핀이라 이 수정을 **받을 수 없다**(P4, 이 리포 밖). 더 근본적으로: 소비자가 "`shared@main` 이 무엇을 대신 소유하고 무엇이 바뀌었나"를 볼 곳이 이 리포에 없다. #186 도 #240 도 그 정보 부재에서 나왔다.
  - **개발자 렌즈** — 🔴 **이 리포에는 자기 워크플로를 검증하는 CI 가 전혀 없다.** `.github/workflows/` 에 있는 것은 재사용 워크플로 2개뿐이고, push/PR 트리거 검증 워크플로가 없다. 방금 YAML 파싱을 손으로 돌려야 했던 것이 그 부재의 증거다. 다음에 같은 클래스의 키가 새도 아무도 잡지 못한다.
  - **운영자 렌즈** — 6시간 → 20분은 그 자체로 관측 가능성 개선이다. 추가 요구는 현재 근거 없음.

**6. 사용자 대면 품질** — 이 워크플로의 "사용자"는 소비 리포다. 계약 변경 없음, 액션 불필요, 하위호환. 좋음.

고아(미사용 코드·문서) 발견 0건.

## Carry-Forward

- **Actionable**:
  - docket #240 에 로컬 커밋 해시와 함께 진행 코멘트를 남긴다(런 종료 커밋 이후 — 해시가 생긴 뒤에 한 번만).
  - #240 트라이지 코멘트가 requester 에게 넘긴 것: grep 기반 timeout 체커가 `uses:` job 14개를 항구적 false positive 로 안고 가게 된다. 우리 쪽 작업 아님, 전달만 완료.
- **Decisions Ledger (L1 self-decisions)**:
  - `D-01` · timeout 값 **20** 채택 · 대안 30 / 60(요청서가 제시한 20–60 범위) · trade-off: 낮을수록 행 걸림을 빨리 드러내지만 느린 소비자를 자를 위험이 커진다 · 근거: 실측 최대치 0.8분의 25배 여유이고, 이 소비자군 최장 워크플로(11.2분)보다도 넉넉하다; 60 은 실패를 늦게 드러낼 뿐 아무것도 더 사주지 않는다; 두 워크플로에 같은 숫자를 써 다음 드리프트 지점을 만들지 않는다 · 되돌리기 비용: 한 줄 · status **provisional**
  - `D-02` · caller-tunable `timeout_minutes` **입력 미도입** · 대안: optional input 추가(요청서가 함께 제안) · trade-off: 소비자별 편차를 표현할 수 없게 된다 · 근거: 측정된 소비자가 예외 없이 1분 미만이라 편차 수요 증거가 없고 요청자 본인도 불필요하다고 적었다; 더 결정적으로 job-level `timeout-minutes` 가 표현식을 거부한다는 보고가 있어(actions/runner#1555, `Unexpected value '${{ inputs.… }}'`) **구현 가능성 자체가 미확인**이다 — 채택할 이유가 없어 실측까지 가지 않았다 · 되돌리기 비용: 입력 추가는 semver minor, 단 위 실측이 선행돼야 함 · status **provisional**
  - `D-03` · cleanup 에 **step-level timeout 미추가** · 대안: 스텝에도 bound · trade-off: 나중에 두 번째 스텝이 추가되면 job 상한만으로는 어느 스텝이 매달렸는지 안 드러난다 · 근거: 현재 job 이 단일 스텝이라 완전한 중복이고, 중복 상한은 두 숫자가 갈리는 드리프트 지점을 하나 더 만든다 · 되돌리기 비용: 한 줄 · status **provisional**
  - `D-04` · `claudedocs/` 를 이 **공개 리포에 커밋** · 대안: `.gitignore` 처리 · trade-off: 개발 추적 문서가 공개된다 · 근거: 전역 지침이 "엄브렐러 없는 독립 OSS 리포는 그 리포의 `claudedocs/` 를 쓴다"로 이미 정했고, 이 리포를 담을 엄브렐러가 없어 ignore 하면 연속성 문서가 세션 간에 소실된다; 운영 값(호스트·자격증명·토큰)은 어떤 경우에도 적지 않는다는 규칙은 그대로 지킨다 · 되돌리기 비용: 낮음(ignore + 이력 유지) · status **provisional**
- **Blocked-on-Human (ledger)**: None
- **Structural Improvement Proposals**: None — 이 사이클에서 나온 구조 개선(주석 → CONTRIBUTING 클래스 규칙)은 제안이 아니라 다음 사이클 스코프로 직행한다.
- **Pending Human Decisions**:
  - **push 시점** — 이 수정은 push 전까지 어디에도 도달하지 않고, push 는 사람 게이트다.
  - **소비자 SHA 핀 전진** — 세션 워크스페이스 밖 리포의 코드 변경이라 여기서 수행 불가(P4). 사람이 그 리포 세션에서 결정·실행할 사항.
- **Emergent Next Capability**: `FRONTIER-OPEN: P2 소비자 계약 문서화 — CONTRIBUTING 에 "caller 가 표현할 수 없는 키는 called 가 소유한다"를 클래스 규칙으로, README 에 "이 워크플로가 당신 대신 소유하는 것" 절, templates 에 caller 한계 주석 [autonomous]`
- **Roadmap Revisions**: P1 의 미결 항목(`timeout-minutes` 부재)이 해소되어 `HISTORY.md` 로 이관. P1 에는 "같은 클래스의 다른 키 조사"만 남긴다. 개발자 렌즈에서 나온 **P5(이 리포 자체의 검증 CI 부재)**를 백로그에 신규 추가.
- **Next-Cycle Scope**: **P2 소비자 계약 문서화.** `CONTRIBUTING.md` 에 재사용 워크플로가 보장해야 하는 것을 클래스 규칙으로 명문화(`timeout-minutes` 개별 패치가 아니라 caller-표현불가 키 전체), `README.md` 에 소비자가 `uses:` 한 줄로 무엇을 받는지 적는 절 추가, `templates/*.yml` 에 caller 한계 주석. 도출 게이트: 부재가 결함으로 읽히고(소비자가 45일치 run 을 실측해야 누락을 발견했다), 이 리포의 선언된 역할(공유 자산 + 그 사용법) 안이며, trade-off 없는 추가 작업 → autonomous-eligible.
