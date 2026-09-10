# Cycle 10: 사다리 ③ — 최소 권한
Date: 2026-09-10
Root: `claudedocs/`
Budget: 10
Start: 1
Status: complete

## Re-plan

트리거 ⚪ NONE. cycle-09 의 Next-Cycle Scope 그대로. Blocked 원장 비어 있음, `D-01`~`D-10` 전부 `provisional` 유지. 이 런의 마지막 사이클(budget 10/10).

## Scope & Implementation

**STEP 1 — 필요한 최소가 무엇인지부터.** 권한은 넓히기 쉽고 좁히기 어려우므로 스텝별로 따졌다.

`publish-npm.yml` 의 10개 스텝 중 `GITHUB_TOKEN` 을 쓰는 것은 **체크아웃 둘뿐**이다. 레지스트리 인증은 `NPM_TOKEN` 이 하고(`NODE_AUTH_TOKEN` 으로 주입), 어떤 스텝도 리포에 쓰지 않는다(태그를 읽기만 하고, `package.json` 수정은 러너 로컬에서 끝난다). 두 번째 체크아웃 대상인 `iyulab/shared` 는 공개 리포라 별도 권한이 필요 없다. ⇒ **`contents: read`.**

`cleanup-expired-artifacts.yml` 은 이미 `actions: write` 만 갖는데, 이것도 맞다 — 체크아웃 스텝이 없고 아티팩트 API 만 호출한다. `permissions` 를 선언하면 명시하지 않은 스코프는 `none` 이 되므로 `contents` 부재가 정상이다.

**변경**:
- `publish-npm.yml` — `permissions: contents: read` 선언. 주석에 왜 이것이 최소인지와, **재사용 워크플로의 `permissions` 는 caller 가 가진 것을 넘어설 수 없고 좁히기만 하므로 소비자의 다른 워크플로에 영향이 없다**는 점을 남겼다(이 선언이 소비자에게 파괴적일까 걱정할 사람을 위해).
- `scripts/ci/check-workflows.py` — "모든 워크플로가 `permissions` 를 선언한다"를 검사로 추가. 최상위 또는 모든 job 중 어느 쪽이든 허용한다.
- `scripts/ci/test-check-workflows.py` — 그 검사를 덮는 케이스 추가(20케이스).
- `CONTRIBUTING.md` — 규칙 명문화. `permissions` 는 caller 가 **쓸 수 있는** 키라 표현 불가 목록과는 성격이 다르다는 점을 명시했다 — 그럼에도 여기서 선언해야 하는 이유는 "다른 리포가 돌리는 워크플로에 기본값은 잘못된 기본값"이기 때문이다.

## Verification & Defect Resolution

수용 기준을 검사 전에 고정: ① 세 워크플로 모두 `permissions` 보유 ② 신규 검사가 미선언을 실제로 잡음 ③ `publish-npm.yml` 이 `permissions` 외에는 변하지 않음 ④ 전체 검사 그린.

```
ci.yml                        {'contents': 'read'}
cleanup-expired-artifacts.yml {'actions': 'write'}
publish-npm.yml               {'contents': 'read'}      <- 신규

자가 테스트: ok  workflow without a permissions block is caught   / 20 case(s), 0 failure(s)
publish-npm 구조: 상위 키 추가 {'permissions'} · 제거 없음 · steps 10 -> 10 · concurrency 불변
전체: all 3 check(s) passed
```

결함 1건 발견·수정(권한 미선언). 이번에도 인라인 패치가 `\n` 을 실제 개행으로 풀어 테스트 파일을 깨뜨렸고, `check-all.py` 가 `FAILED: test-check-workflows.py` 로 즉시 잡아냈다 — cycle-08 이 만든 진입점이 같은 런 안에서 실제로 값을 했다.

## Reflection

**1. 스코프 적합** — 충족. 권한을 근거 없이 넓히지 않았고, 이미 맞던 것(`cleanup` 의 `actions: write`)은 건드리지 않았다.

**2. 잠재 결함** — 신규 없음.

**3. 구조 개선 기회** — 기존 3건 이월, 신규 없음.

**4. 철학 드리프트** — 없음.

**5. 로드맵 영향 · 창발 스코프**
- (a) 로드맵 변경 없음. `ROADMAP.md` 에는 P4(이 리포 밖에서만 실행 가능)만 남는다.
- (b) 세 렌즈 — 자율 가능한 후속이 남지 않았다:
  - **소비자 렌즈** — 계약 문서가 받는 것·못 바꾸는 것·하지 않는 것을 모두 말한다. 더 나아가는 것(입력 추가, 다른 레지스트리)은 전부 **수요 증거가 필요한 선제 확장**이다.
  - **개발자 렌즈** — 검사·테스트·진입점·기여 규칙이 서로를 가리키고, 문서와 코드의 목록은 기계가 대조한다. 남은 3건은 전부 사람 판단이 필요한 제안이다.
  - **운영자 렌즈** — bound·최소 권한·동시성·정직한 요약이 세 워크플로 모두에 자리 잡았다. 사다리 ③ 에서 더 집을 신호가 없다.
  - **사다리 ④(가속기)** — 검사 3종의 로컬 실행이 수 초 수준이고 CI job 상한이 10분이다. 최적화할 대상이 없다.

**6. 사용자 대면 품질** — 소비자 대면 동작 변화 없음(권한은 좁히기만 한다). 다만 주석에 "이것이 당신의 다른 워크플로를 건드리지 않는다"를 적은 것이 실질적 사용자 대면 배려다.

고아 발견 0건.

## Carry-Forward

- **Actionable**: docket #240 에 커밋 해시와 함께 코멘트(런 종료 커밋 직후) — 이 런의 마지막 남은 실행 항목.
- **Decisions Ledger (L1 self-decisions)**:
  - `D-01`~`D-10` 전부 **provisional** 유지
  - `D-11` · `publish-npm.yml` 의 권한을 **`contents: read`** 로 · 대안: 선언하지 않고 caller 기본값에 맡김, 또는 `contents: write` 로 여유 · trade-off: 나중에 이 워크플로가 리포에 쓰는 일(태그 생성, 릴리스 노트)을 하게 되면 권한을 넓혀야 한다 · 근거: 현재 10개 스텝 중 `GITHUB_TOKEN` 을 쓰는 것은 체크아웃뿐이고 어떤 스텝도 쓰기를 하지 않는다; 다른 리포가 돌리는 워크플로에 기본값을 상속시키는 것은 최소 권한의 반대다 · 되돌리기 비용: 한 줄 · status **provisional**
- **Blocked-on-Human (ledger)**: None
- **Structural Improvement Proposals**: *(이월 3건)* CONTRIBUTING↔SKILL 중복 · actionlint 도입 · `rewrite-exports` 의 `main`/`types` 처리 여부
- **Pending Human Decisions**: *(전부 이월)* push 시점 · 소비자 SHA 핀 전진(P4) · `CHANGELOG.md` 도입 여부 · `cleanup-expired-artifacts.yml` 존폐
- **Emergent Next Capability**: `FRONTIER-EXHAUSTED: 세 렌즈 모두에서 자율 가능한 후속이 없다 — 소비자 렌즈의 남은 후보는 전부 수요 증거가 필요한 선제 확장이고(입력 추가·다른 레지스트리 지원), 개발자 렌즈는 검사·테스트·진입점·기여 규칙이 갖춰지고 문서/코드 목록을 기계가 대조하며 남은 3건이 전부 사람 판단이고, 운영자 렌즈는 bound·최소 권한·동시성·정직한 보고가 세 워크플로에 모두 자리 잡았다 | ladder: ③(방어선) 을 이번 사이클에서 실행 — ②(문서)는 cycle-09 에서 완료, ④(가속기)는 검사가 수 초·job 상한 10분이라 대상 없음`
- **Roadmap Revisions**: 없음. budget 10/10 소진으로 런 종료.
- **Next-Cycle Scope**: **없음 — 자율 프론티어 소진.** 다음 런이 열리면 시작점은 사람 결정 4건 중 하나다(가장 앞선 것은 push, 그다음이 소비자 SHA 핀 전진). 그 결정들이 내려지기 전까지 이 리포에서 자율로 진행할 작업이 남아 있지 않다.

## Release Readiness
- Version: n/a — 이 리포에는 버전을 담는 파일이 없다(`package.json`·`plugin.json` 등 부재).
- Changelog: n/a — `CHANGELOG.md` 가 없고, 도입 여부 자체가 사람 결정 대기 항목이다.
- Docs: doc-sync 는 cycle-09 에서 실측해 정합 확인(구조 목록·상호 참조·최상위 항목 설명). 연속성 문서 lean — `ROADMAP.md` 에 완료 항목 0(남은 것은 P4 하나, 이 리포에서 실행 불가), 완료분 10건 전부 `HISTORY.md` 색인.
- Evidence: `python3 scripts/ci/check-all.py` → `all 3 check(s) passed` (계약 검사 `workflow contract OK`, 워크플로 3개·job 3개·템플릿 2개 · 검사기 자가 테스트 20/20 · 공유 스크립트 계약 테스트 20/20).
- Tag/publish: 수행하지 않음 — push 는 사람 게이트이고, 소비자 도달은 SHA 핀 전진이 별도로 필요하다.
