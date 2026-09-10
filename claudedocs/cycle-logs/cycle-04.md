# Cycle 04: P3 공유 스크립트 스모크 테스트
Date: 2026-09-10
Root: `claudedocs/`
Budget: 10
Start: 1
Status: complete

## Re-plan

트리거 ⚪ NONE. cycle-03 의 Next-Cycle Scope 그대로. Blocked 원장 비어 있음, `D-01`~`D-07` 전부 `provisional` 유지(사람 정정 없음).

## Scope & Implementation

**STEP 1 — 설계 생략(패턴 추종).** cycle-03 이 만든 `scripts/ci/` 하니스 패턴(임시 트리 구성 → 실제 산출물 구동 → 종료코드와 관찰 가능한 효과 단언)을 그대로 따른다. 신규 의존성 없음, 구조 결정 없음.

`scripts/ci/test-shared-scripts.py` 신설 — 세 스크립트를 **워크플로가 부르는 방식 그대로** 구동한다(같은 환경변수, 같은 작업 디렉터리). 상속된 `TAG_VERSION`·`GITHUB_REF_NAME`·`GITHUB_ENV` 는 케이스마다 지워서, "미설정" 케이스가 실행 환경 때문에 조용히 통과하지 않게 했다.

- `validate-tag.sh` 10케이스 — 수락(`v1.2.3`, 다자리 `v10.20.30`), 거절(`1.2.3`·`v1.2`·`v1.2.3.4`·`vnot-a-version`·빈 값), 프리릴리스 거절, `GITHUB_REF_NAME` 미설정, `GITHUB_ENV` 미설정. 수락 케이스는 종료코드뿐 아니라 `GITHUB_ENV` 에 실제로 `TAG_VERSION=1.2.3` 이 적혔는지까지 본다.
- `verify-package-version.mjs` 4케이스 — 일치/불일치/`TAG_VERSION` 부재/`version` 필드 부재.
- `rewrite-exports-src-to-dist.mjs` 6케이스 — `./src/` 접두, 접두 없는 `src/` 정규화, 중첩 객체·배열 재귀 재작성, `src/` 밖 경로 불변, `exports` 부재 시 무동작, `main` 불변.

**의도적으로 못박은 두 가지.** 둘 다 "지금 이게 맞다"가 아니라 "지금 이렇게 동작한다"를 고정한 것이고, 이유를 테스트 주석에 남겼다.
- **프리릴리스 태그 거절** — publish 스텝이 `--tag` 없이 게시하므로 프리릴리스가 통과하면 `latest` dist-tag 로 나간다. 지금 거절이 정합적이다.
- **`main` 은 재작성 대상 아님** — 스크립트 이름대로 `exports` 만 다룬다. 나중에 `main`·`types` 도 필요해지면 그 변경이 **의도된 것**이 되도록(조용한 구멍이 아니라) 고정했다.

`.github/workflows/ci.yml` 에 스텝 추가.

## Verification & Defect Resolution

수용 기준을 검사 전에 고정: ① 20케이스 전부 통과 ② **변이 테스트** — 스크립트를 고의로 망가뜨리면 해당 테스트가 실제로 실패하는가 ③ CI 연결 후 전체 재검증.

```
기준선            : 20 case(s), 0 failure(s)   exit=0
변이 테스트 (실패가 나와야 정상):
  validate-tag 정규식을 무엇이든 통과하게    -> 5 failure(s)
  verify-version 불일치 검사 제거            -> 1 failure(s)
  rewrite-exports 의 dist -> build           -> 4 failure(s)
  validate-tag 의 TAG_VERSION 내보내기 제거  -> 2 failure(s)
전체 재검증: 계약 검사기 자가 테스트 16/16 · 스크립트 20/20 · 실제 리포 contract OK (exit=0)
```

**변이 테스트를 넣은 이유**: 20케이스가 첫 시도에 전부 통과했다. 검증이 없던 코드에 대해 테스트가 한 번에 초록이면 그건 안심할 근거가 아니라 의심할 근거다 — 테스트가 대상을 실제로 구동하지 않아도 같은 그림이 나온다. 네 변이가 모두 잡히는 것을 확인하고서야 이 초록을 증거로 취급한다.

결함 발견 0건. 세 스크립트 모두 문서화된 의도대로 동작한다.

## Reflection

**1. 스코프 적합** — P3 의 스크립트 부분 충족. `assets/brand/` 는 미조사로 남는다.

**2. 잠재 결함** — 신규 없음. 다만 테스트가 **설계상 날카로운 모서리 하나**를 드러냈다: `rewrite-exports` 는 `exports` 만 재작성하므로, `main`·`types` 가 `./src/` 를 가리키는 소비 패키지는 게시 후에도 src 를 가리킨다. 이 리포에서는 소비 패키지의 실제 형태를 볼 수 없어 영향 여부를 판정할 수 없다 — 추정으로 결함이라 부르지 않고 관찰로 남긴다(제안 항목).

**3. 구조 개선 기회** — 기존 제안 2건 이월. 신규: `scripts/ci/` 에 검사 스크립트가 셋이 됐는데 로컬에서 무엇을 돌려야 하는지 어디에도 없다. 작지만 실재하는 간극.

**4. 철학 드리프트** — 없음. 신규 의존성 0, 러너 기본 도구만 사용.

**5. 로드맵 영향 · 창발 스코프**
- (a) P3 의 스크립트 항목 해소 → `HISTORY.md` 이관. P3 에는 `assets/brand/` 미조사만 남는다.
- (b) 세 렌즈:
  - **소비자 렌즈** — 🔴 **`cleanup-expired-artifacts.yml` 이 실제로 무언가를 하는지 확인된 적이 없다.** 이 워크플로는 `artifact.expired` 가 참인 것만 골라 삭제하는데, GitHub 은 보존기간이 지난 아티팩트를 스스로 만료 처리한다. 만료된 아티팩트 삭제가 실제로 용량을 회수하는지, 아니면 이미 회수된 것의 레코드만 지우는지 확인된 바 없다. 소비 리포 3곳이 이걸 주간 cron 으로 돌리고 있으므로, 무동작이라면 3곳이 매주 아무것도 아닌 일을 하고 있는 것이다.
  - **개발자 렌즈** — 로컬 검증 진입점 부재(위 3번).
  - **운영자 렌즈** — 추가 요구 없음.

**6. 사용자 대면 품질** — 소비자 대면 변화 없음. 테스트 이름이 계약 문장으로 읽히게 썼다(`rejects a prerelease tag (no dist-tag handling downstream)`) — 실패했을 때 무엇이 깨졌는지가 이름만으로 드러난다.

고아 발견 0건.

## Carry-Forward

- **Actionable**: docket #240 에 커밋 해시와 함께 코멘트(런 종료 커밋 이후, 1회) — cycle-01 부터 이월.
- **Decisions Ledger (L1 self-decisions)**: `D-01`~`D-07` 전부 **provisional** 유지, 이번 사이클 변동 없음. 신규 없음(이 사이클은 패턴 추종이라 실질 trade-off 를 낳은 선택이 없었다).
- **Blocked-on-Human (ledger)**: None
- **Structural Improvement Proposals**:
  - *(이월)* `CONTRIBUTING.md` ↔ `skills/repo-conventions/SKILL.md` 구조 규칙 4개 중복 해소
  - *(이월)* actionlint 도입 — 이 리포 고유 계약 검사와 상보적
  - **신규**: `rewrite-exports-src-to-dist.mjs` 가 `main`·`types` 도 다뤄야 하는지. 소비 패키지의 실제 형태를 아는 쪽에서만 판단 가능하므로 여기서 결정하지 않는다.
- **Pending Human Decisions**: *(전부 이월)* push 시점 · 소비자 SHA 핀 전진(P4) · `CHANGELOG.md` 도입 여부
- **Emergent Next Capability**: `FRONTIER-OPEN: cleanup-expired-artifacts.yml 이 실제로 용량을 회수하는지 조사 — 만료 아티팩트 삭제의 실제 효과를 문서·API 근거로 확인하고, 무동작이면 필터를 고치거나 워크플로 자체를 재검토한다; 소비 리포 3곳이 주간 cron 으로 돌리고 있다 [autonomous]`
- **Roadmap Revisions**: P3 의 스크립트 항목 완료 → `HISTORY.md` 이관, P3 는 `assets/brand/` 미조사만 남김. **P6 신설** — `cleanup-expired-artifacts.yml` 실효성 조사.
- **Next-Cycle Scope**: **P6 — `cleanup-expired-artifacts.yml` 이 실제로 하는 일 확인.** GitHub 이 아티팩트 만료를 어떻게 처리하는지(만료 시 콘텐츠가 이미 삭제되는지, `expired: true` 레코드 삭제가 용량에 영향을 주는지)를 공식 문서·REST API 레퍼런스로 확인하고, 결과에 따라 ⑴ 그대로 유효 → 근거를 주석으로 남김 ⑵ 필터가 잘못됨 → 수정 ⑶ 무동작 → 워크플로 재검토를 제안으로. 추정으로 코드를 고치지 않는다 — 근거를 먼저 확보한다.
