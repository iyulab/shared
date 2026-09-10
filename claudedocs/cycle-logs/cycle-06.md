# Cycle 06: 발견의 소비자 계약 반영 + P3 잔여
Date: 2026-09-10
Root: `claudedocs/`
Budget: 10
Start: 1
Status: complete

## Re-plan

트리거 ⚪ NONE. cycle-05 의 Next-Cycle Scope 그대로. Blocked 원장 비어 있음, `D-01`~`D-08` 전부 `provisional` 유지.

## Scope & Implementation

**STEP 1 — 설계 생략(패턴 추종).** cycle-02 가 확립한 배치(README = 소비자 계약, templates = 그 자리에서 필요한 최소 사실 + 포인터)를 그대로 따른다.

cycle-05 의 발견은 이 리포 안에서만 참이면 소용이 없다. 소비자가 보는 자리에 도달시키는 것이 이 사이클이다.

- **`README.md`** — `### What cleanup-expired-artifacts.yml does not do` 절 신설. 무엇을 지우는지, 왜 용량이 회수되지 않는지(만료 시 콘텐츠 삭제, 다운로드는 `410`), 레코드에 남는 `size_in_bytes` 로 잰 수치가 왜 아무것도 측정하지 않는지, 그리고 **실제 손잡이는 업로드 쪽 `retention-days`** 라는 것까지. 발견 정황 없이 관찰 가능한 사실로만 서술했다(공개 리포).
- **`templates/cleanup-expired-artifacts.yml`** — 같은 사실을 파일 머리에 3줄. 이 템플릿을 복사해 가는 사람이 "아티팩트 정리 = 용량 관리"라고 믿는 것을 그 자리에서 끊는다. 겸해서 cycle-02 에서 넣은 caller 주석의 들여쓰기가 `cleanup:` 과 같은 열이라 소속이 모호했던 것을 4칸으로 교정.
- **`README.md` (assets)** — "reference files in `assets/` directly via raw URL" 이라고만 적혀 있어 소비자가 URL 형태를 추측해야 했다. 실제 raw URL 예시 한 줄 추가.

**P3 잔여 — `assets/brand/` 점검 결과: 결함 없음.** `favicon.ico`·`iyulab.png`·`iyulab.svg` 3개가 README 서술("company logo and icon files")대로 존재하고, 리포 안의 모든 `assets/` 언급이 실제 경로와 일치한다. 고칠 것이 없어 고치지 않았다 — 관찰 하나만 남긴다: `favicon.ico` 가 270 KB 로 favicon 치고 크다(다중 해상도 ICO 라면 정상 범위일 수 있다). 브랜드 자산은 이 리포가 재생성할 권한이 있는 대상이 아니므로 판단하지 않고 기록만 한다.

## Verification & Defect Resolution

수용 기준을 검사 전에 고정: ① 템플릿 파싱 결과가 HEAD 와 동일(주석·들여쓰기만 변경) ② README 표 열 수 정합 ③ 전체 검사 스위트 그린.

```
templates/cleanup-expired-artifacts.yml: parsed-equal-to-HEAD = True · jobs.cleanup keys = ['uses']
README.md: 6 rows, distinct cols = {3}
계약 검사기 contract OK (exit=0) · 자가 테스트 16/16 · 스크립트 테스트 20/20
```

`.gitattributes` 가 이제 실제로 동작하는 것도 부수적으로 확인됐다 — git 이 `README.md` 에 대해 "CRLF will be replaced by LF" 를 보고한다(cycle-03 에서 의도한 정규화).

결함 발견 0건.

## Reflection

**1. 스코프 적합** — 세 항목 모두 충족. P3 잔여도 닫혔다(조사 결과 무결함).

**2. 잠재 결함** — 신규 없음.

**3. 구조 개선 기회** — 기존 3건 이월. 신규 없음.

**4. 철학 드리프트** — 없음. "고칠 것이 없으면 고치지 않는다"를 P3 에서 실제로 적용했다 — 점검했고 무결함이라는 사실 자체가 결과다.

**5. 로드맵 영향 · 창발 스코프**
- (a) P3 완료 → `HISTORY.md` 이관. 남은 것은 P1 의 조사 항목과 P4(리포 밖)뿐이다.
- (b) 세 렌즈:
  - **소비자 렌즈** — cycle-05 의 발견이 이제 소비자가 보는 자리에 있다. 남은 미확인 질문: **caller 가 표현할 수 없는 키 중 소비자가 실제로 바꾸고 싶어 할 것이 더 있는가**(P1 의 "조사 필요"). 예를 들어 `runs-on` 을 다르게 하고 싶은 소비자는 지금 아무 방법이 없고, 그 사실이 어디에도 적혀 있지 않다.
  - **개발자 렌즈** — `scripts/ci/` 검사 셋이 셋이 됐는데 로컬에서 무엇을 어떻게 돌리는지가 어디에도 없다(cycle-04 부터 이월 중). CONTRIBUTING 이 규칙을 적고 CI 가 강제하는데, 기여자가 push 전에 확인할 경로가 문서화되지 않았다.
  - **운영자 렌즈** — 추가 요구 없음.

**6. 사용자 대면 품질** — README 절 제목을 "What it does **not** do" 로 잡았다. 소비자가 이 워크플로에 대해 갖는 오해가 정확히 "용량을 정리해 준다"이므로, 부정형이 그 오해를 바로 겨냥한다.

고아 발견 0건.

## Carry-Forward

- **Actionable**: docket #240 에 커밋 해시와 함께 코멘트(런 종료 커밋 이후, 1회) — cycle-01 부터 이월.
- **Decisions Ledger (L1 self-decisions)**: `D-01`~`D-08` 전부 **provisional** 유지, 이번 사이클 변동 없음. 신규 없음(패턴 추종 사이클).
- **Blocked-on-Human (ledger)**: None
- **Structural Improvement Proposals**: *(이월 3건)* CONTRIBUTING↔SKILL 중복 · actionlint 도입 · `rewrite-exports` 의 `main`/`types` 처리 여부
- **Pending Human Decisions**: *(전부 이월)* push 시점 · 소비자 SHA 핀 전진(P4) · `CHANGELOG.md` 도입 여부 · `cleanup-expired-artifacts.yml` 존폐
- **Emergent Next Capability**: `FRONTIER-OPEN: P1 잔여 조사 — caller 가 표현할 수 없는 키(env·defaults·runs-on·continue-on-error·container·services) 중 이 두 워크플로가 실제로 선언해야 하는 것이 더 있는지, 그리고 소비자가 바꾸고 싶어 할 만한데 방법이 없는 것이 무엇인지 확인해 결과를 계약 문서에 반영한다 [autonomous]`
- **Roadmap Revisions**: P3 완료 → `HISTORY.md` 이관.
- **Next-Cycle Scope**: **P1 잔여 — caller 표현 불가 키 감사.** 두 재사용 워크플로에 대해 ⑴ `env`·`defaults`·`continue-on-error`·`container`·`services`·`runs-on` 각각이 이 워크플로들에 실제로 필요한지 근거를 갖고 판정 ⑵ 필요한 것이 있으면 선언 ⑶ 소비자가 바꾸고 싶어 할 법한데 caller 로는 불가능한 것(특히 `runs-on`)을 README 계약에 명시. 근거 없이 선제 추가하지 않는다 — 없으면 "없다"가 결과이고 그 판정을 기록한다.
