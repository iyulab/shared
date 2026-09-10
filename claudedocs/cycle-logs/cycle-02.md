# Cycle 02: P2 소비자 계약 문서화
Date: 2026-09-10
Root: `claudedocs/`
Budget: 10
Start: 1
Status: complete

## Re-plan

트리거 ⚪ NONE. cycle-01 의 Next-Cycle Scope(P2) 그대로.

- Blocked-on-Human 원장: 비어 있음.
- Decisions Ledger: `D-01`~`D-04` 전부 `provisional`, 사람 정정 없음 → 그대로 이월.
- 상속 Actionable: docket #240 코멘트 — 커밋 해시가 필요해 런 종료 시점 작업. 이 사이클 스코프 아님.

## Scope & Implementation

**STEP 1 설계.** 세 문서에 나눠 쓸 때 중복이 생기면 그 자체가 다음 드리프트 지점이 된다. 독자로 갈랐다 — `CONTRIBUTING.md` = 이 리포에 워크플로를 추가하는 사람(규칙), `README.md` = 소비자(계약), `templates/` = 복사해 가는 사람(그 자리에서 필요한 최소 사실 + 포인터).

설계 중 **선행 문제 발견**: `skills/repo-conventions/SKILL.md` 가 `CONTRIBUTING.md` 를 거의 그대로 중복하고 있다(구조 규칙 4개가 겹침). 규칙을 어디에 둘지 정하지 않으면 신규 규칙을 추가하는 순간 드리프트 지점이 하나 더 생기므로, 이 사이클의 스코프를 수행하기 위한 선행 결정으로 처리했다 — 신규 규칙의 정본은 `CONTRIBUTING.md`, 스킬은 포인터만(`D-05`). 기존 4개 항목의 중복 해소는 구조 개선 제안으로 넘긴다(조용히 리팩터링하지 않는다).

**언어**: 각 파일의 기존 언어를 따랐다 — `README.md`·`CONTRIBUTING.md`·`SKILL.md` 는 영문, `templates/*.yml` 은 한국어(기존 `node_version` 주석이 한국어). 리포가 이미 쓰던 언어를 임의로 바꾸지 않는다.

**변경**:
- `CONTRIBUTING.md` — `## Reusable workflows` 절 신설. caller 허용 키 9개와 표현 불가 키 7개를 명시하고, "그 키들은 여기서 선언되거나 아예 존재하지 않는다 → 기본값 상속 대신 명시적으로 선언하라"를 규칙으로. 고정값 우선(입력은 소비자 편차가 실제로 생겼을 때만), 근거 주석 유지까지 포함.
- `skills/repo-conventions/SKILL.md` — `## Reusable workflow guarantees` 절, 세 키를 예시로 들고 "전체 목록과 규칙은 CONTRIBUTING.md — 여기 재기술하지 말 것".
- `README.md` — `### What the reusable workflows own` 절 + 4행 표(Node 기준선 / job 타임아웃 / 게시 동시성 / 게시 멱등성). 각 행은 "소비자에게 무엇을 뜻하는가"로 서술.
- `templates/*.yml` 2개 — caller 가 job 키를 가질 수 없다는 사실 2줄 주석 + README 절 포인터.

## Verification & Defect Resolution

수용 기준을 검사 전에 고정: ① templates 파싱 결과가 HEAD 와 동일(주석만 추가) ② 마크다운 표 열 수 정합 ③ §7 스크럽 — 공개 파일 7개에 내부 토큰 0 ④ 키 목록 정본이 한 곳.

```
① templates 2개: parsed-equal-to-HEAD = True (양쪽)
② README.md: 6 rows, distinct column counts = {3}
③ 최초 검사에서 위반 1건 → 수정 후 PASS (7/7 clean)
④ CONTRIBUTING 전체 키 목록 보유 True · README 재기술 안 함 True · 포인터 존재 True
git diff --numstat: 7개 파일 전부 삭제 0 (추가 전용)
```

**🔴 결함 1건 발견·수정 — 내가 cycle-01 에서 넣은 것.**
`publish-npm.yml` 의 주석에 `20 은 실측 최대치(0.8분)의 25배 여유` 라고 적었다. 이 리포는 공개이고, 저 문장은 소비 리포들을 실측한 내부 데이터를 공개 산출물에 노출하는 **발견 정황 서술**이다(전역 지침 §7 금지 토큰). 라이브러리 관점의 관찰 가능한 서술로 교체했다 — `20 은 이 job 의 정상 소요보다 훨씬 크게 잡은 값이다 — 정확한 값보다 상한의 존재가 요점이다`. 근거는 그대로 살아 있고 내부 수치만 빠졌다.
이 사이클이 §7 스크럽을 검증 기준에 넣지 않았다면 그대로 커밋됐을 것이다.

**줄바꿈 조사(오탐 정정 포함).** `git show | grep $'\r'` 가 모든 파일을 CRLF 로 보고해 `scripts/github/validate-tag.sh` 가 CRLF 로 커밋된 것처럼 보였다(그랬다면 ubuntu 러너에서 `bash` 실행이 깨진다). **오탐이었다** — Git-for-Windows 가 stdout 을 파이프로 낼 때 생긴 아티팩트다. raw blob 을 파일로 뽑아 `file`·`bash -n` 통과를 확인했고, 결정적으로 러너 조건으로 실제 구동해 4케이스 전부 정상이었다:

```
v1.2.3         -> TAG_VERSION=1.2.3 내보냄, exit 0
1.2.3          -> 거절, exit 1
v1.2.3-beta.1  -> 거절, exit 1
vnot-a-version -> 거절, exit 1
```

CRLF 스크립트라면 실행 자체가 실패하므로 이 구동이 blob 이 LF 임의 증거이기도 하다. `core.autocrlf=true` + `.gitattributes` 부재이나, 저장된 blob 은 LF 이고 `git diff` 가 7개 파일 모두 삭제 0 을 보이므로 현재 커밋 경로에 줄바꿈 재작성은 없다.

**프리릴리스 태그 거절은 결함이 아니다.** `v1.2.3-beta.1` 이 거절되는데, publish 스텝이 `npm publish --access public` 만 하고 `--tag` 를 주지 않으므로 프리릴리스가 통과하면 `latest` dist-tag 로 나간다 — 지금 거절하는 것이 정합적이다. 관찰로만 기록(P3).

## Reflection

**1. 스코프 적합** — P2 세 항목(README 절 · CONTRIBUTING 규칙 · templates 주석) 모두 충족. cycle-01 이 예상한 "주석이 길다"는 문제도 함께 해소됐다: 이제 클래스 규칙이 CONTRIBUTING 에 있으므로 워크플로 주석은 그 인스턴스만 설명한다.

**2. 잠재 결함** — 위 §7 위반 1건(수정 완료). 그 외 신규 없음.

**3. 구조 개선 기회** — `CONTRIBUTING.md` 와 `skills/repo-conventions/SKILL.md` 의 구조 규칙 4개가 여전히 중복이다. 스킬 자신이 "Do not duplicate implementation files inside skills/" 와 "Keep skill content aligned with the actual implementation" 을 규칙으로 갖고 있어, 자기 규칙을 자기가 어기는 모양이다. 이번엔 신규 규칙만 정본화했고 기존 중복은 손대지 않았다 — 제안으로 넘긴다.

**4. 철학 드리프트** — 없음. 다만 이 사이클 자체가 한 번 위반했다(위 §7 결함). 공개 리포라는 사실이 검증 기준에 상시로 들어가야 한다는 신호이고, 그것이 아래 P5 로 이어진다.

**5. 로드맵 영향 · 창발 스코프**
- (a) P2 완료 → `HISTORY.md` 이관.
- (b) 세 렌즈:
  - **소비자 렌즈** — 이제 "무엇을 받는가"는 읽을 수 있다. 다음으로 없는 것은 "무엇이 바뀌었는가"다 — 이 리포에 `CHANGELOG.md` 가 없어, SHA 를 전진시킬지 판단할 근거가 소비자에게 없다. 실제 신호이나 릴리스 관례를 새로 도입하는 성격이라 **discussion**.
  - **개발자 렌즈** — 🔴 P5. 이 사이클이 손으로 돌린 검증(YAML 파싱·표 열 수·§7 스크럽·스크립트 구동)은 전부 기계가 할 수 있는 것이고, 지금은 아무도 하지 않는다. 특히 §7 스크럽은 사람이 매번 기억해야 하는 종류라 반드시 샌다.
  - **운영자 렌즈** — `.gitattributes` 부재. 지금 blob 은 LF 로 깨끗하지만, `core.autocrlf` 가 다르게 설정된 기여자가 `validate-tag.sh` 를 CRLF 로 커밋하면 12곳 게시 파이프라인이 전부 깨진다. 조용하고 폭발 반경이 크며, 한 파일로 막힌다.

**6. 사용자 대면 품질** — 문서 변경뿐이고 계약은 그대로. README 표는 소비자가 `uses:` 한 줄에서 갖는 실제 질문("내가 뭘 받고 뭘 못 바꾸나")의 순서로 배열했다.

고아 발견 0건.

## Carry-Forward

- **Actionable**:
  - docket #240 에 로컬 커밋 해시와 함께 코멘트(런 종료 커밋 이후, 1회) — cycle-01 에서 이월.
- **Decisions Ledger (L1 self-decisions)**:
  - `D-01` · timeout 값 20 · status **provisional** *(cycle-01 이월, 변동 없음)*
  - `D-02` · caller-tunable 입력 미도입 · status **provisional** *(cycle-01 이월, 변동 없음)*
  - `D-03` · cleanup step-level timeout 미추가 · status **provisional** *(cycle-01 이월, 변동 없음)*
  - `D-04` · `claudedocs/` 를 공개 리포에 커밋 · status **provisional** *(cycle-01 이월, 변동 없음)*
  - `D-05` · 재사용 워크플로 규칙의 **정본을 `CONTRIBUTING.md`** 로 두고 `SKILL.md` 은 포인터만 · 대안: 스킬을 정본으로, 또는 양쪽에 전문 기재 · trade-off: 에이전트용 스킬이 자기완결적이지 않게 된다(포인터를 따라가야 함) · 근거: 양쪽 전문 기재는 확실한 드리프트이고, 스킬을 정본으로 삼으면 사람 기여자가 표준 위치(`CONTRIBUTING.md`)에서 규칙을 못 찾는다; 스킬 자신이 "중복 금지"와 "구현과 정합 유지"를 규칙으로 갖고 있어 포인터가 그 규칙과 일관된다 · 되돌리기 비용: 낮음(문단 이동) · status **provisional**
- **Blocked-on-Human (ledger)**: None
- **Structural Improvement Proposals**:
  - `CONTRIBUTING.md` ↔ `skills/repo-conventions/SKILL.md` 의 구조 규칙 4개 중복 해소. 권장 접근: `CONTRIBUTING.md` 를 유일 정본으로 두고 스킬은 에이전트가 필요로 하는 만큼만 요약 + 링크. 이번 사이클에서 신규 규칙에 대해 이미 그 형태를 택했으므로(`D-05`) 기존 항목도 같은 형태로 맞추는 일이다. 조용히 하지 않고 제안으로 남긴다.
- **Pending Human Decisions**:
  - **push 시점** *(이월)* · **소비자 SHA 핀 전진** *(이월, ROADMAP P4)*
  - **`CHANGELOG.md` 도입 여부** — 소비자가 SHA 전진 판단 근거를 가질 수 있게 되지만, 이 리포에 없던 릴리스 관례를 새로 들이는 결정이다. 도출 게이트상 **discussion** — 자율 스코프로 잡지 않는다.
- **Emergent Next Capability**: `FRONTIER-OPEN: P5 이 리포 자체의 검증 CI + .gitattributes — 이 사이클이 손으로 돌린 검증(YAML 파싱·§7 스크럽·공유 스크립트 구동)을 push/PR 트리거로 고정하고, 줄바꿈 정규화를 파일로 못박는다 [autonomous]`
- **Roadmap Revisions**: P2 완료 → `HISTORY.md` 이관. P3 에 프리릴리스 태그 관찰 기록 추가. P5 에 `.gitattributes` 부재를 같은 스코프로 편입(예방=`.gitattributes`, 탐지=CI 로 짝이 맞는다).
- **Next-Cycle Scope**: **P5 — 이 리포가 자기 산출물을 검증한다.** ⑴ `.gitattributes` 로 줄바꿈 정규화 고정(`*.sh` 는 반드시 `eol=lf`) ⑵ push/PR 트리거 검증 워크플로 신설 — 워크플로/템플릿 YAML 파싱, 공유 스크립트 구동 스모크, §7 내부 토큰 스크럽. 도구 선택(외부 린터 액션 도입 vs 러너 기본 제공 도구만으로 자립)에 실제 trade-off 가 있으므로 STEP 1 에서 다섯 렌즈로 결정하고 `D-06` 으로 기록한다. 전역 지침상 CI 워크플로에서 artifact 업로드는 하지 않는다.
