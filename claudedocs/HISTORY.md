# HISTORY — iyulab/shared

완료된 작업의 색인. 상세는 `cycle-logs/` 와 git 이력이 갖는다.

- **2026-09-10** 사다리③ 최소 권한 — publish-npm.yml 에 contents: read 선언, 모든 워크플로의 permissions 선언을 검사 불변식으로 (cycle-10)
- **2026-09-10** 사다리② 문서 정합성 실측 — 구조 목록·상호 참조는 이상 없음, 미설명이던 claudedocs/ 를 README 에 명시 (cycle-09)
- **2026-09-10** 로컬 검증 진입점 — scripts/ci/check-all.py 로 검사 목록을 단일화(발견 기반), CI 스텝 3→1, CONTRIBUTING 에 push 전 실행 안내 (cycle-08)
- **2026-09-10** P1 재사용 워크플로 실행 가드 완료 — caller 허용 키 목록이 낡아(cache-mode 누락) 정당한 템플릿을 CI 가 막던 결함 수정, 문서/코드 목록 대조를 불변식으로 추가, 나머지 키는 불필요 판정 (cycle-07)
- **2026-09-10** P3 나머지 공유 자산 — assets/brand 점검(무결함), cleanup 워크플로의 실제 효과를 README·템플릿에 반영, assets raw URL 예시 추가 (cycle-06)
- **2026-09-10** P6 cleanup 워크플로 실효성 조사 — 만료 아티팩트는 콘텐츠가 이미 삭제(410)돼 용량 회수가 0임을 실측 확인, 거짓 "Freed" 보고 제거 (cycle-05)
- **2026-09-10** P3 공유 스크립트 검증 — validate-tag.sh·verify-package-version.mjs·rewrite-exports-src-to-dist.mjs 계약 테스트 20케이스, 변이 테스트로 유효성 확인 (cycle-04)
- **2026-09-10** P5 자기 검증 — .gitattributes 로 줄바꿈 고정, CI 워크플로 + 워크플로 계약 검사기(자가 테스트 16케이스) 신설; 검사기 결함 4건 발견·수정 (cycle-03)
- **2026-09-10** P2 소비자 계약 문서화 — CONTRIBUTING 에 재사용 워크플로 클래스 규칙, README 에 소유 항목 표, templates 에 caller 한계 주석; 공개 산출물 내부 맥락 노출 1건 수정 (cycle-02)
- **2026-09-10** P1 재사용 워크플로 실행 가드 — `publish-npm.yml`·`cleanup-expired-artifacts.yml` 두 job 에 `timeout-minutes: 20` 선언, 6시간 기본 상한 제거 (docket #240) (cycle-01)
