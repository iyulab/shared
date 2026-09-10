# Cycle 05: P6 cleanup-expired-artifacts.yml 실효성 조사
Date: 2026-09-10
Root: `claudedocs/`
Budget: 10
Start: 1
Status: complete

## Re-plan

트리거 ⚪ NONE. cycle-04 의 Next-Cycle Scope(P6) 그대로. Blocked 원장 비어 있음, `D-01`~`D-07` 전부 `provisional` 유지.

## Scope & Implementation

**STEP 1 — 조사 중심 사이클.** "추정으로 고치지 않는다"가 이 사이클의 전제였으므로 근거부터 세 갈래로 확보했다.

**문서 근거** — GitHub 문서와 커뮤니티 답변이 일치한다: 보존기간이 지나면 아티팩트는 **자동으로 삭제되고 용량은 그 시점에 회수된다**. UI 에 남는 "Expired" 표시는 그 run 이 아티팩트를 만들었다는 사실을 보여주기 위한 레코드일 뿐이다.

**실측 근거 ⑴ — 레코드 분포.** 접근 가능한 iyulab 리포 40곳을 훑어 만료 레코드를 가진 곳 18개를 확인했다. 만료 레코드의 `size_in_bytes` 합계가 리포에 따라 수 MB~수 GB 규모로 **0 이 아니다**(가장 큰 곳은 약 10.5 GB).

**실측 근거 ⑵ — 결정적.** 만료/미만료 아티팩트의 다운로드 엔드포인트를 읽기 전용으로 각각 호출했다.

```
만료 아티팩트  (size_in_bytes = 12,406,336) -> HTTP 410  {"message":"Artifact has expired"}
미만료 아티팩트(size_in_bytes = 12,517,984) -> HTTP 200  OK
```

⇒ **만료 아티팩트의 콘텐츠는 이미 없다. 그런데 API 는 만료 후에도 `size_in_bytes` 에 원래 크기를 계속 실어 준다.**

(삭제 API 를 실제로 호출해 보는 것이 더 직접적이지만, 대상이 이 세션 워크스페이스 밖 리포이고 되돌릴 수 없는 파괴적 행위라 하지 않았다. 위 두 근거로 판정에 충분하다.)

**결론** — 이 워크플로는 **저장 용량을 전혀 회수하지 않는다.** 이미 삭제된 것들의 레코드를 지우면서, 그 레코드에 남아 있는 원래 크기를 합산해 `Freed N MB` 로 보고하고 있었다. 한 리포 기준으로는 0바이트를 회수하고도 요약에 수 GB 가 찍힐 수 있는 구조다.

**변경 — 거짓 보고만 고쳤다.**
- `totalFreedBytes` 합산과 `Freed` 행 제거. 요약은 `Expired records removed` / `Failed` 로 바꾸고, "이것으로 회수되는 용량은 없으며 실제 손잡이는 업로드 쪽 `retention-days` 다"를 요약 본문에 명시.
- 스텝 이름을 `Delete expired artifacts` → `Remove expired artifact records` 로. 이름이 하는 일과 어긋나 있었다.
- 위 조사 결과와 410 증거를 스텝 주석으로 남겨, 다음 사람이 `size_in_bytes` 합산을 "빠진 기능"으로 오해해 되살리지 않게 했다.

**동작 자체는 바꾸지 않았다.** "이 워크플로가 존재할 이유가 있는가"는 소비 리포 3곳이 주간 cron 으로 참조 중인 공유 워크플로를 없애는 결정이라 소비자 대면 파괴적 변경이고, 도출 게이트상 **discussion** 이다 — 자율로 처리하지 않고 근거와 함께 사람에게 넘긴다.

## Verification & Defect Resolution

수용 기준을 검사 전에 고정: ① YAML 파싱·`timeout-minutes`·`permissions` 불변 ② 임베드된 JS 문법 유효(github-script 가 async 함수로 감싸므로 그 형태로 검사) ③ `Freed`·`size_in_bytes` 합산 흔적 0 ④ 전체 검사 스위트 그린.

```
timeout-minutes: 20 · permissions: {'actions': 'write'} · steps: ['Remove expired artifact records']
node --check (async 래핑 후): OK
'Freed' 문자열 잔존: False · size_in_bytes 합산 잔존: False
계약 검사기: contract OK (exit=0) · 자가 테스트 16/16 · 스크립트 테스트 20/20
```

**결함 1건 발견·수정**: 거짓 요약 보고(위 참조). 이건 이 리포가 소비자에게 내보내는 워크플로가 운영자에게 사실이 아닌 수치를 보고하고 있던 것이라 🟠 급으로 본다 — 용량 문제를 조사하는 사람이 이 요약을 근거로 삼으면 정확히 반대 방향으로 간다.

조사 과정에서 막다른 길 하나: 소비 리포 3곳(cycle-03 기록에 이름이 남아 있던 곳들)을 API 로 조회했으나 전부 404 였다 — 이 토큰으로 접근 불가이거나 다른 경로에 있다. 그 3곳의 실제 데이터는 확인하지 못했고, 대신 접근 가능한 18개 리포에서 같은 패턴을 확인했다. 판정 근거가 특정 리포에 의존하지 않으므로 결론은 그대로 선다.

## Reflection

**1. 스코프 적합** — P6 충족. 조사 → 근거 → 최소 수정 + 나머지는 제안, 순서를 지켰다.

**2. 잠재 결함** — 신규 없음. 이 워크플로는 이제 자기가 하는 일을 정확히 말한다.

**3. 구조 개선 기회** — 기존 3건 이월. 신규: **이 워크플로가 존재할 이유** 자체(아래 Pending 참조).

**4. 철학 드리프트** — 없음. 오히려 "표면적 증상이 아니라 근본"에 해당하는 사이클이었다 — 요약 숫자를 고치는 데서 멈추지 않고 왜 그 숫자가 나왔는지까지 갔고, 판정을 바꿀 수 없는 부분(워크플로 존폐)은 선을 넘지 않았다.

**5. 로드맵 영향 · 창발 스코프**
- (a) P6 조사 완료 → `HISTORY.md` 이관. 남는 것은 존폐 결정이고 그것은 사람 몫이라 로드맵이 아니라 Pending 으로 간다.
- (b) 세 렌즈:
  - **소비자 렌즈** — 🔴 이 발견이 **소비자에게 도달하지 않는다.** `README.md` 의 소유 항목 표는 `publish-npm.yml` 만 다루고, `templates/cleanup-expired-artifacts.yml` 은 이 워크플로가 무엇을 하고 무엇을 하지 «않는지» 말하지 않는다. 이 템플릿을 복사해 가는 다음 소비자는 "아티팩트 정리 = 용량 관리"라고 믿게 되고, 실제 손잡이(`retention-days`)를 놓친다. 템플릿의 존재 자체가 잘못된 것을 가르치고 있다.
  - **개발자 렌즈** — `scripts/ci/` 검사 셋을 로컬에서 어떻게 돌리는지가 어디에도 없다(cycle-04 이월).
  - **운영자 렌즈** — 이제 요약이 정직하다. 추가 요구 없음.

**6. 사용자 대면 품질** — Actions 요약은 운영자가 보는 UI 표면이다. 이번 변경으로 그 표면이 사실을 말하게 됐고, "그럼 무엇을 해야 하는가"(`retention-days`)까지 같은 자리에 적었다 — 진단만 주고 처방을 빼면 다시 잘못된 결론으로 간다.

고아 발견 0건.

## Carry-Forward

- **Actionable**: docket #240 에 커밋 해시와 함께 코멘트(런 종료 커밋 이후, 1회) — cycle-01 부터 이월.
- **Decisions Ledger (L1 self-decisions)**:
  - `D-01`~`D-07` 전부 **provisional** 유지, 이번 사이클 변동 없음
  - `D-08` · cleanup 워크플로의 **동작은 유지하고 보고만 정정** · 대안: 워크플로 삭제, 또는 미만료 아티팩트를 지우도록 필터 반전 · trade-off: 아무 용량도 회수하지 않는 주간 cron 이 3곳에서 계속 돈다 · 근거: 삭제는 소비 리포 3곳이 참조 중인 공유 워크플로를 없애는 소비자 대면 파괴적 변경이고, 필터 반전은 이름과 어긋나는 데다 살아 있는 아티팩트를 지우는 실질적 위험이 있다; 거짓 보고는 그와 무관하게 결함이므로 그것만 자율로 고친다 · 되돌리기 비용: 낮음 · status **provisional**
- **Blocked-on-Human (ledger)**: None
- **Structural Improvement Proposals**: *(이월 3건)* CONTRIBUTING↔SKILL 중복 · actionlint 도입 · `rewrite-exports` 의 `main`/`types` 처리 여부
- **Pending Human Decisions**:
  - *(이월)* push 시점 · 소비자 SHA 핀 전진(P4) · `CHANGELOG.md` 도입 여부
  - **신규 — `cleanup-expired-artifacts.yml` 을 계속 제공할 것인가.** 근거는 위에 전부 있다: 용량을 회수하지 않고, 남는 효과는 아티팩트 목록의 레코드 정리뿐이다. 선택지 ⑴ 그대로 유지(정직해진 보고와 함께) ⑵ 제거 — 소비 리포 3곳이 참조 중이라 핀 전진 시 워크플로 오류가 되므로 그 3곳과 함께 조율 필요 ⑶ 용량을 실제로 다루는 것으로 대체(업로드 쪽 `retention-days` 규약을 강제하는 검사 등). 소비자 대면 결정이라 자율로 하지 않는다.
- **Emergent Next Capability**: `FRONTIER-OPEN: cleanup 워크플로의 실제 효과를 소비자 계약에 반영 — README 소유 항목 표에 이 워크플로 항목 추가(무엇을 하고 무엇을 하지 않는지, 실제 손잡이는 retention-days), templates/cleanup-expired-artifacts.yml 에 같은 사실 주석; 겸해서 P3 잔여인 assets/brand/ 점검 [autonomous]`
- **Roadmap Revisions**: P6 조사 완료 → `HISTORY.md` 이관, 존폐 결정은 Pending Human Decisions 로 이동(로드맵에 남기지 않는다 — 우리가 실행할 작업이 아니다).
- **Next-Cycle Scope**: **발견을 소비자 계약에 반영 + P3 잔여.** ⑴ `README.md` 의 "What the reusable workflows own" 표에 `cleanup-expired-artifacts.yml` 항목 추가 — 만료 레코드를 정리할 뿐 용량을 회수하지 않으며 실제 손잡이는 업로드 쪽 `retention-days` 라는 것을, 발견 정황 없이 관찰 가능한 서술로. ⑵ `templates/cleanup-expired-artifacts.yml` 에 같은 사실 한 줄. ⑶ `assets/brand/` 점검(P3 잔여) — 파일이 README 가 말하는 대로 존재하고 참조 가능한지.
