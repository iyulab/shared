# Cycle 03: P5 자기 검증 — .gitattributes + CI
Date: 2026-09-10
Root: `claudedocs/`
Budget: 10
Start: 1
Status: complete

## Re-plan

트리거 ⚪ NONE. cycle-02 의 Next-Cycle Scope(P5) 그대로. Blocked 원장 비어 있음, `D-01`~`D-05` 전부 `provisional` 유지(사람 정정 없음).

## Scope & Implementation

**STEP 1 설계 — 도구 선택(`D-06`).** 외부 린터 액션(actionlint 류) 도입 vs 러너 기본 도구로 자립.

조사: PyYAML·yq·jq 는 GitHub 호스티드 ubuntu 러너에 선설치돼 있다(runner-images). 즉 python3 경로는 설치 스텝 없이 성립한다.

판단 근거 — actionlint 는 표현식 문법·액션 참조 유효성처럼 우리가 직접 하기 어려운 것을 잘 하지만, **이 리포에서 실제로 새어나간 것 두 가지를 하나도 잡지 못한다**: ⑴ "모든 job 이 상한을 갖는다"는 이 리포 고유 계약(#240 이 존재한 이유) ⑵ 공개 산출물의 내부 맥락 노출(cycle-02 에서 실제 발생). 또 이 환경에서 actionlint 를 구동할 수 없어 **통과를 확인하지 못한 CI 를 커밋하게 된다** — 증거 없이 초록을 주장하지 않는다는 원칙에 정면으로 걸린다. ⇒ 자립 검사기 채택, actionlint 는 제안으로 남긴다.

**변경**:
- `.gitattributes` 신설 — `* text=auto eol=lf` + `*.sh`/`*.mjs`/`*.yml`/`*.md` 명시, `*.png`·`*.ico` binary. `scripts/` 가 Linux 러너에서 실행되므로 이건 스타일이 아니라 정확성 설정이다.
- `.github/workflows/ci.yml` 신설 — push/PR 트리거, `permissions: contents: read`, ref 단위 `concurrency`(구버전 검증은 취소), `timeout-minutes: 10`(자기 규칙을 자기가 지킨다). 전역 지침대로 artifact 업로드 없음.
- `scripts/ci/check-workflows.py` 신설 — CONTRIBUTING 이 적은 계약을 기계가 검사한다: ⑴ 워크플로·템플릿 YAML 유효성 ⑵ `.github/workflows/` 의 모든 non-caller job 이 `timeout-minutes` 를 int 로 1..60 범위에 선언 ⑶ 템플릿 job 은 caller 로 남고 표현 불가 키를 갖지 않음 ⑷ 절대경로·IP·리터럴 토큰 미포함. `check(root)` 로 분리해 테스트 가능하게 했다.
- `scripts/ci/test-check-workflows.py` 신설 — 검사기 자가 테스트 16케이스.

## Verification & Defect Resolution

수용 기준을 검사 전에 고정: ① 검사기가 실제 리포에서 통과 ② **음성 테스트** — 잡아야 할 회귀마다 실제로 잡는가 ③ `.gitattributes` 가 기존 파일에 재정규화 churn 을 만들지 않는가.

```
자가 테스트: 16 case(s), 0 failure(s)   exit=0
실제 리포 : checked 3 workflow file(s), 3 job(s), 2 template(s) / workflow contract OK   exit=0
git add --renormalize . 후 git diff --cached --numstat:
  7개 파일 전부 삭제 0 (추가 전용) · scripts/·assets/ 원본 변경 없음
```

**🔴 이 사이클에서 발견·수정한 결함 4건 — 전부 내가 만든 것이고, 음성 테스트가 아니었으면 셋은 초록으로 커밋됐다.**

1. **유출 정규식이 죽어 있었다.** 인라인 패치가 백슬래시를 과도하게 줄여 `[A-Za-z]:\\|...` 가 `[A-Za-z]:\|...` 가 됐고, 정규식에서 `\|` 는 리터럴 파이프라 두 분기가 모두 무의미해졌다. 검사기는 계속 "OK" 를 냈다. → 문자 클래스 `[\\/]` + URL 스킴 배제 lookbehind/lookahead 로 재작성.
2. **검사기가 자기 주석에 스스로 걸렸다.** docstring 의 예시 경로가 자기 패턴과 매치. → 예시를 문자 그대로 적지 않고 서술로 대체.
3. **검사기가 자기 자가 테스트에 걸렸다.** 테스트 파일은 잡아야 할 패턴을 의도적으로 담으므로 필연이다(소스의 `a:\n` 문자열까지 매치됐다). → `LEAK_SCAN_EXCLUDED` 로 그 파일만 명시 제외, 왜 안전한지(전부 문서화용 placeholder, 실제 설정 없음)를 주석에 남김. 설계상 사각지대이므로 이름 지정 제외로 좁혔다.
4. **스캔 범위 구멍** — `skills/` 가 공개 텍스트인데 유출 스캔 대상에서 빠져 있었다. → 범위 추가 + 그것을 덮는 자가 테스트 케이스 추가(16번째).

**방법론 결함(리포 변경 아님, 기록).** 이 사이클에서 셸 heredoc 을 경유한 인라인 패치가 백슬래시·`\n` 을 반복해서 훼손했다(따옴표 heredoc 에서도 발생). 더 나쁜 것은 **첫 패치 스크립트가 치환 성공 여부를 확인하지 않고 "patched" 를 출력한 것**이다 — 결함 1이 살아남은 경로가 정확히 이것이다. 이후 모든 인라인 치환에 앵커 미발견 시 즉시 실패를 넣었고, 백슬래시를 포함하는 파일은 셸을 경유하지 않는 방식으로 썼다.

## Reflection

**1. 스코프 적합** — P5 충족. 예방(`.gitattributes`)과 탐지(CI)를 짝으로 넣었고, 탐지기 자신이 검증된다.

**2. 잠재 결함** — 위 4건 수정 완료. 남은 것: `LEAK_SCAN_EXCLUDED` 는 의도된 사각지대다. 파일 하나에 한정되고 그 파일의 성격이 명확해 감수한다.

**3. 구조 개선 기회** — cycle-02 의 CONTRIBUTING↔SKILL 중복 제안은 그대로 미결. 신규: actionlint 도입(위 `D-06` 의 미채택 대안) — 이 검사기와 상보적이지, 대체재가 아니다. 이 환경에서 통과를 확인할 수 없어 제안으로만 남긴다.

**4. 철학 드리프트** — 없음. 검사 로직을 `scripts/` 로 뺀 것은 CONTRIBUTING 자신의 규칙("Move non-trivial workflow logic into scripts/")을 따른 것이다.

**5. 로드맵 영향 · 창발 스코프**
- (a) P5 완료 → `HISTORY.md` 이관.
- (b) 세 렌즈:
  - **소비자 렌즈** — 새 요구 없음. CI 는 소비자 계약을 바꾸지 않는다.
  - **개발자 렌즈** — 🔴 **공유 스크립트 3개에 테스트가 하나도 없다.** `validate-tag.sh`·`verify-package-version.mjs`·`rewrite-exports-src-to-dist.mjs` 는 소비 리포의 모든 게시에서 실행되는데 검증이 없다. 이번 사이클이 자가 테스트 하니스 패턴을 이미 만들어 뒀으므로 이제 패턴 추종 작업이다.
  - **운영자 렌즈** — CI 가 생겼다. 추가 요구 현재 없음.

**6. 사용자 대면 품질** — 소비자 대면 변화 없음. 검사기 실패 메시지는 "무엇이 왜 문제이고 어디를 보라"까지 적어, 처음 걸리는 기여자가 CONTRIBUTING 으로 갈 수 있게 했다.

고아 발견 0건.

## Carry-Forward

- **Actionable**: docket #240 에 커밋 해시와 함께 코멘트(런 종료 커밋 이후, 1회) — cycle-01 부터 이월.
- **Decisions Ledger (L1 self-decisions)**:
  - `D-01`~`D-05` · 전부 **provisional** 유지, 이번 사이클에서 변동 없음 (상세는 cycle-01·cycle-02)
  - `D-06` · **외부 린터 액션 미도입, 러너 기본 도구(python3+PyYAML)로 자립** · 대안: actionlint 액션 도입, 또는 병행 · trade-off: 표현식 문법·액션 참조 유효성 같은 GitHub 고유 검사를 놓친다 · 근거: actionlint 는 이 리포에서 실제로 샌 두 가지(고유 계약 위반, 공개 산출물 내부 맥락 노출)를 잡지 못하고, 이 환경에서 구동 불가라 통과를 확인 못 한 CI 를 커밋하게 된다; 자립 검사기는 로컬에서 그대로 돌려 증거를 낼 수 있다 · 되돌리기 비용: 낮음(스텝 추가, 상보적이라 제거도 불필요) · status **provisional**
  - `D-07` · 유출 스캔에서 **자가 테스트 파일만 이름 지정 제외** · 대안: 테스트에서 패턴을 런타임 조립해 리터럴을 숨김 · trade-off: 그 파일의 실제 유출은 못 잡는 사각지대가 생긴다 · 근거: 런타임 조립은 난독화라 테스트 가독성을 해치고, 테스트가 잡아야 할 것을 보여주지 못하게 된다; 값이 전부 문서화용 placeholder 이고 실제 설정을 담지 않아 손실이 없다 · 되돌리기 비용: 한 줄 · status **provisional**
- **Blocked-on-Human (ledger)**: None
- **Structural Improvement Proposals**:
  - *(이월)* `CONTRIBUTING.md` ↔ `skills/repo-conventions/SKILL.md` 구조 규칙 4개 중복 해소.
  - **actionlint 도입** — 이 검사기와 상보적(그쪽은 GitHub 고유 문법, 이쪽은 리포 고유 계약). 도입 시 구동 확인이 가능한 환경에서 통과를 먼저 보고 커밋해야 한다.
- **Pending Human Decisions**: *(전부 이월)* push 시점 · 소비자 SHA 핀 전진(P4) · `CHANGELOG.md` 도입 여부
- **Emergent Next Capability**: `FRONTIER-OPEN: 공유 스크립트 3개 스모크 테스트 — validate-tag.sh·verify-package-version.mjs·rewrite-exports-src-to-dist.mjs 는 모든 소비 리포 게시 경로에서 실행되는데 검증이 없다; 자가 테스트 하니스 패턴이 이미 있어 패턴 추종 작업이다 [autonomous]`
- **Roadmap Revisions**: P5 완료 → `HISTORY.md` 이관. P3(나머지 공유 자산 점검)이 "미조사"에서 구체 항목으로 전환 — 스크립트 3개의 무테스트 상태가 이번 사이클에서 확인됐으므로, P3 를 "공유 스크립트 검증"으로 좁혀 다시 적는다.
- **Next-Cycle Scope**: **공유 스크립트 스모크 테스트.** `scripts/ci/` 하니스 패턴을 따라 세 스크립트의 계약을 고정한다 — `validate-tag.sh`(태그 형태 수락/거절, `TAG_VERSION` 내보내기, `GITHUB_ENV` 미설정 시 실패), `verify-package-version.mjs`(일치/불일치/`TAG_VERSION` 부재/`version` 필드 부재), `rewrite-exports-src-to-dist.mjs`(중첩 exports 재작성, `./src/`·`src/` 양쪽 접두, exports 부재 시 무동작). CI 에 스텝 추가. cycle-02 에서 관찰한 프리릴리스 태그 거절 동작도 테스트로 못박아, 나중에 dist-tag 를 다룰 때 의도된 동작이었음이 남게 한다.
