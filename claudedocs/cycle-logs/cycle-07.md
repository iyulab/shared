# Cycle 07: P1 잔여 — caller 표현 불가 키 감사
Date: 2026-09-10
Root: `claudedocs/`
Budget: 10
Start: 1
Status: complete

## Re-plan

트리거 ⚪ NONE. cycle-06 의 Next-Cycle Scope 그대로. Blocked 원장 비어 있음, `D-01`~`D-08` 전부 `provisional` 유지.

## Scope & Implementation

**STEP 1 — 조사 먼저.** 감사를 하려면 기준 목록이 정확해야 하는데, 그 목록은 cycle-02 에서 이슈 본문을 근거로 적은 것이었다. 공식 레퍼런스로 다시 확인했다.

**🔴 기준 자체가 낡아 있었다.** GitHub 은 caller 허용 키에 **`cache-mode`** 를 추가했다. `CONTRIBUTING.md` 가 공표한 9개 목록과 `scripts/ci/check-workflows.py` 의 `CALLER_ALLOWED` 가 둘 다 그것을 빠뜨리고 있었다. 결과는 단순한 문서 오류가 아니다 — **정당하게 `cache-mode` 를 쓰는 템플릿을 CI 가 "표현 불가 키"로 판정해 막는다.** 이 리포가 소비자에게 잘못된 규칙을 공표하면서 그 규칙을 강제까지 하고 있던 셈이다.

**변경 ⑴ — 목록 정정**: `CONTRIBUTING.md` 와 `CALLER_ALLOWED` 양쪽에 `cache-mode` 추가(10개). 목록이 앞으로도 늘어날 것이라는 사실을 양쪽 주석에 적어, 다음에 검사기가 "표현 불가 키"를 보고할 때 그것이 **회피 대상이 아니라 레퍼런스를 다시 읽으라는 신호**임이 드러나게 했다.

**변경 ⑵ — 일회성 수정을 불변식으로.** 방금 고친 결함의 본질은 "같은 목록이 두 곳에 있고 조용히 벌어졌다"이다. 정정만 하면 같은 일이 반복된다. ⇒ 검사기가 `CONTRIBUTING.md` 의 공표 목록을 파싱해 `CALLER_ALLOWED` 와 대조한다. 문장 자체가 바뀌어 파싱이 실패하면 그것도 **조용히 통과하지 않고 보고**하며, 어디를 고치면 되는지까지 메시지에 적는다.

**변경 ⑶ — 소비자가 바꿀 수 없는 것을 계약에 명시.** `README.md` 에 `### What a caller cannot change` 표 신설 — 러너(`ubuntu-latest`), 레지스트리(공개 npm, `--access public` 고정), 설치 전략(`npm install`, lock 파일 있을 때만 캐시). 각 행에 "다르게 필요하면 어떻게 되는가"를 함께 적었다.

**감사 결과 — 추가로 선언해야 할 키는 없다.** 근거를 갖고 판정했고, 없다는 것이 결과다.

| 키 | 판정 | 근거 |
|---|---|---|
| `timeout-minutes` | **선언 완료** | cycle-01 |
| `runs-on` | 선언 완료 | 양쪽 `ubuntu-latest` |
| `env` | 불필요 | 필요한 유일한 값(`NODE_AUTH_TOKEN`)이 이미 스텝 단위 `env` 로 붙어 있다. job 단위로 올리면 필요 없는 스텝까지 토큰을 보게 된다 — 지금이 더 좁다. |
| `defaults` | 불필요 | `run:` 스텝이 bash 문법에 의존하는데 `ubuntu-latest` 의 기본 셸이 이미 bash 다. `runs-on` 이 바뀔 때를 대비해 명시하는 것은 근거 없는 선제 추가라 하지 않는다. |
| `continue-on-error` | **부적절** | 게시 실패는 크게 드러나야 한다. 추가하면 안 되는 키다. |
| `container` · `services` | 불필요 | 두 워크플로 모두 외부 서비스나 컨테이너를 쓰지 않는다. |

## Verification & Defect Resolution

수용 기준을 검사 전에 고정: ① 자가 테스트 전부 통과 + `cache-mode` 템플릿이 **오탐되지 않음** ② 문서/코드 목록 드리프트가 실제로 잡힘 ③ 문장 변형 시 조용히 통과하지 않음 ④ 실제 리포 그린.

```
자가 테스트: 19 case(s), 0 failure(s)   (16 -> 19, 신규 3케이스)
  ok  template caller may use cache-mode                              <- 오탐 방지(기대 0건)
  ok  CONTRIBUTING dropping a key from the published list is caught   <- 드리프트 탐지
  ok  CONTRIBUTING wording change is reported, not silently skipped   <- 파싱 실패의 fail-loud
실제 리포: contract OK (exit=0) · 스크립트 테스트 20/20
문서/코드 목록 대조: 양쪽 10개 동일
```

**결함 1건 발견·수정**: 낡은 허용 키 목록(위 참조). 🟠 급 — 공개 문서가 틀렸고 그 틀린 규칙을 CI 가 강제하고 있었다.

자가 테스트의 `build()` 도 함께 고쳤다. 종전에는 `CONTRIBUTING.md` 를 빈 파일로 만들었는데, 새 검사가 그 파일을 읽으므로 **실제 파일을 복사**하도록 바꿨다 — 빈 파일이면 새 검사가 테스트 트리에서 아무 일도 하지 않아, 검사를 검사하지 못하게 된다.

## Reflection

**1. 스코프 적합** — P1 의 조사 항목 충족. "없으면 없다가 결과"를 실제로 적용했고, 대신 그 판정 근거를 표로 남겨 다음 사람이 같은 조사를 반복하지 않게 했다.

**2. 잠재 결함** — 신규 없음. 새 검사의 프로즈 파싱은 취약할 수 있으나, 취약함이 **조용한 통과가 아니라 시끄러운 실패**로 나타나도록 설계했고 그것을 테스트로 고정했다.

**3. 구조 개선 기회** — 기존 3건 이월. 신규 없음.

**4. 철학 드리프트** — 없음. 오히려 이 사이클이 "표면 수정에서 멈추지 않는다"의 사례다: 목록을 고치는 데서 끝냈다면 다음 키 추가 때 똑같이 벌어졌을 것이다.

**5. 로드맵 영향 · 창발 스코프**
- (a) P1 완료 → `HISTORY.md` 이관. 로드맵에는 **P4(이 리포 밖)만** 남는다.
- (b) 세 렌즈:
  - **소비자 렌즈** — 계약 문서가 이제 "무엇을 받는가"·"무엇을 못 바꾸는가"·"무엇을 하지 않는가"를 모두 말한다. 이 축에서 더 도출되는 것 없음.
  - **개발자 렌즈** — cycle-04 부터 이월 중인 것 하나가 남아 있다: `scripts/ci/` 검사가 셋인데 기여자가 push 전에 무엇을 돌려야 하는지 어디에도 없다. CONTRIBUTING 이 규칙을 적고 CI 가 강제하는데 로컬 확인 경로만 비어 있다.
  - **운영자 렌즈** — 추가 요구 없음.

**6. 사용자 대면 품질** — 새 README 표의 세 번째 열을 "If you need it different" 로 잡았다. 제약만 나열하면 소비자는 막다른 길을 보지만, 다음 행동이 함께 있으면 이슈로 이어진다 — 그것이 이 리포가 실제로 원하는 흐름이다(수요가 모여야 입력을 추가할지 판단할 수 있다).

고아 발견 0건.

## Carry-Forward

- **Actionable**: docket #240 에 커밋 해시와 함께 코멘트(런 종료 커밋 이후, 1회) — cycle-01 부터 이월.
- **Decisions Ledger (L1 self-decisions)**:
  - `D-01`~`D-08` 전부 **provisional** 유지, 이번 사이클 변동 없음
  - `D-09` · 검사기가 `CONTRIBUTING.md` 의 **프로즈를 파싱해** 코드와 대조 · 대안: 목록을 한 곳(코드)에만 두고 문서는 링크만, 또는 대조를 포기 · trade-off: 문장이 바뀌면 무관한 문서 편집이 CI 를 깨뜨릴 수 있다 · 근거: 목록은 소비자용 문서에 실제로 필요하고(기여자가 코드를 열어야 규칙을 아는 것은 나쁘다), 두 곳에 두는 이상 대조 없이는 반드시 벌어진다 — 이번 결함이 그 증거다; 깨질 때 조용하지 않고 고칠 위치를 알려주므로 감수 가능하다 · 되돌리기 비용: 낮음(검사 블록 제거) · status **provisional**
- **Blocked-on-Human (ledger)**: None
- **Structural Improvement Proposals**: *(이월 3건)* CONTRIBUTING↔SKILL 중복 · actionlint 도입 · `rewrite-exports` 의 `main`/`types` 처리 여부
- **Pending Human Decisions**: *(전부 이월)* push 시점 · 소비자 SHA 핀 전진(P4) · `CHANGELOG.md` 도입 여부 · `cleanup-expired-artifacts.yml` 존폐
- **Emergent Next Capability**: `FRONTIER-OPEN: 로컬 검증 진입점 — scripts/ci/ 검사 3종을 한 번에 돌리는 경로와 CONTRIBUTING 의 안내; CI 가 강제하는 규칙을 기여자가 push 전에 확인할 방법이 현재 없다 [autonomous]`
- **Roadmap Revisions**: P1 완료 → `HISTORY.md` 이관. 로드맵에 남는 것은 P4 뿐이며, P4 는 이 리포에서 실행할 수 없는 항목이다.
- **Next-Cycle Scope**: **로컬 검증 진입점.** `scripts/ci/` 의 검사 3종(계약 검사·검사기 자가 테스트·스크립트 계약 테스트)을 한 명령으로 돌리는 경로를 만들고, `CONTRIBUTING.md` 에 "push 전에 이것을 돌린다"를 적는다. CI 의 스텝 목록과 로컬 진입점이 갈리지 않도록 한쪽이 다른 쪽을 부르는 형태로 만든다 — 두 곳에 검사 목록을 나열하면 이번 사이클이 고친 것과 같은 종류의 드리프트가 생긴다.
