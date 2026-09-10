# Cycle 09: 사다리 ② — 문서 정합성 실측
Date: 2026-09-10
Root: `claudedocs/`
Budget: 10
Start: 1
Status: complete

## Re-plan

트리거 ⚪ NONE. cycle-08 이 `FRONTIER-EXHAUSTED` 로 닫히며 가치 사다리 ②(내공/문서)로 진입한 그 스코프 그대로. Blocked 원장 비어 있음, `D-01`~`D-10` 전부 `provisional` 유지.

로드맵에는 P4(이 리포 밖)만 남아 있어 주 루프에서 가져올 스코프가 없다 — 사다리 진입이 맞는 상태다.

## Scope & Implementation

**STEP 1 — 설계 생략.** 실측이 먼저이고, 고칠 것이 나오면 그때 판단한다. 작업을 만들어내지 않는 것이 이 사이클의 전제다.

이 런에서 `README.md`·`CONTRIBUTING.md`·`SKILL.md`·템플릿·워크플로가 여러 번 수정됐다. 서로, 그리고 실제 파일 트리와 어긋난 곳이 있는지 세 갈래로 쟀다.

**실측 1 — README 구조 목록 vs 실재 디렉터리**: 나열된 5개 전부 실재하고, 실재 디렉터리 중 목록에 빠진 것 없음. **일치.**

**실측 2 — 문서·코드의 상호 참조**: 파일 경로 참조와 절 이름 인용을 전부 해소해 봤다.
- 절 이름: 다른 파일이 인용하는 README 절(`What the reusable workflows own`)이 실재. **죽은 참조 0.**
- 파일 경로: 미존재 4건이 보고됐으나 **전부 오탐** — `scripts/ci/test-check-workflows.py` 가 임시 트리에 만드는 가상 픽스처 경로(`.github/workflows/broken.yml`·`scripts/leak.sh`·`scripts/ok.sh`·`skills/x/SKILL.md`)다. 실재하면 안 되는 것들이라 결함이 아니다.

**실측 3 — 커밋되는 최상위 항목이 README 에 설명돼 있는가**: 🔴 **`claudedocs/` 가 설명되지 않는다.** 이 런이 만들어 커밋할 디렉터리인데, 공개 리포를 방문한 사람에게는 정체불명의 디렉터리로 보인다.

**변경** — `README.md` 구조 블록에 `claudedocs/` 한 줄 추가(`development notes for this repository - not a shared asset`). "공유 자산이 아니다"를 명시한 것이 요점이다 — 이 리포의 나머지는 전부 다른 리포가 가져다 쓰라고 있는 것이므로, 그렇지 않은 것은 그렇다고 말해야 한다. 겸해서 `scripts/` 설명을 `helper scripts, plus the checks CI runs` 로 갱신했다(cycle-03 이후 `scripts/ci/` 가 생겼는데 설명이 따라가지 않았다).

## Verification & Defect Resolution

수용 기준: ① 재실측에서 미설명 최상위 항목 0 ② README 표 열 수 정합 유지 ③ 전체 검사 그린.

```
재실측 3: CONTRIBUTING.md·assets·claudedocs·scripts·skills·templates 전부 설명됨
          (README.md 자신이 미설명으로 뜨는 것은 실측 스크립트의 오탐 — 구조 블록은 자기 자신을 나열하지 않는다)
README 표: [(6행, 열{3}), (5행, 열{3})]
전체 검사: all 3 check(s) passed
```

결함 1건 발견·수정(`claudedocs/` 미설명). 나머지 두 실측은 **어긋난 곳 없음이 결과**다.

## Reflection

**1. 스코프 적합** — 충족. 실측 셋 중 둘은 "이상 없음"으로 끝났고, 그것을 작업으로 부풀리지 않았다.

**2. 잠재 결함** — 신규 없음.

**3. 구조 개선 기회** — 기존 3건 이월. 신규 없음.

**4. 철학 드리프트** — 없음. 이 사이클이 발견한 것은 오히려 이 런 자신이 만든 부작용이다(`claudedocs/` 를 만들어 놓고 설명하지 않음). 사다리 ② 가 잡으라고 있는 종류의 것이 정확히 이것이다.

**5. 로드맵 영향 · 창발 스코프**
- (a) 로드맵 변경 없음.
- (b) 세 렌즈 — 사다리 ③(방어선)에서 하나가 나왔다:
  - **운영자 렌즈** — 🔴 **`publish-npm.yml` 에 `permissions` 선언이 없다.** `ci.yml`(`contents: read`)과 `cleanup-expired-artifacts.yml`(`actions: write`)은 선언하는데 이 워크플로만 없어서, 호출한 리포의 기본 권한을 그대로 받는다. 이 워크플로가 실제로 필요로 하는 것은 체크아웃을 위한 읽기뿐이고(게시 인증은 `GITHUB_TOKEN` 이 아니라 `NPM_TOKEN` 이 한다), 이건 12곳의 게시 파이프라인이 지나는 경로다. 최소 권한 선언은 표준이고 추가적이며 위험이 낮다.
  - **소비자 렌즈 / 개발자 렌즈** — cycle-08 의 판정에서 변화 없음.

**6. 사용자 대면 품질** — 구조 블록은 리포에 처음 온 사람이 가장 먼저 읽는 곳이다. 거기서 설명되지 않은 디렉터리를 보면 "이게 나한테 필요한 건가?"를 스스로 판단해야 한다 — 그 판단을 대신 해 주는 한 줄이다.

고아 발견 0건.

## Carry-Forward

- **Actionable**: docket #240 에 커밋 해시와 함께 코멘트(런 종료 커밋 이후, 1회) — cycle-01 부터 이월.
- **Decisions Ledger (L1 self-decisions)**: `D-01`~`D-10` 전부 **provisional** 유지, 이번 사이클 변동 없음. 신규 없음.
- **Blocked-on-Human (ledger)**: None
- **Structural Improvement Proposals**: *(이월 3건)* CONTRIBUTING↔SKILL 중복 · actionlint 도입 · `rewrite-exports` 의 `main`/`types` 처리 여부
- **Pending Human Decisions**: *(전부 이월)* push 시점 · 소비자 SHA 핀 전진(P4) · `CHANGELOG.md` 도입 여부 · `cleanup-expired-artifacts.yml` 존폐
- **Emergent Next Capability**: `FRONTIER-OPEN: publish-npm.yml 의 permissions 미선언 — 12곳의 게시 경로가 호출 리포의 기본 권한을 그대로 받는다; 최소 권한을 선언하고, 세 워크플로 모두 permissions 를 갖는다는 것을 계약 검사기의 불변식으로 고정한다 [autonomous]`
- **Roadmap Revisions**: 없음.
- **Next-Cycle Scope**: **사다리 ③ 방어선 — 최소 권한.** ⑴ `publish-npm.yml` 이 실제로 필요로 하는 권한을 근거를 갖고 판정하고 선언 ⑵ `scripts/ci/check-workflows.py` 에 "모든 재사용 워크플로가 `permissions` 를 선언한다"를 검사로 추가 + 자가 테스트 ⑶ 이 규칙을 `CONTRIBUTING.md` 의 재사용 워크플로 절에 명문화. 근거 없이 권한을 넓히지 않는다 — 필요한 최소가 무엇인지부터 스텝별로 따진다.
