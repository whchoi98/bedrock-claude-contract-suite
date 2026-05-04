# Security Rules

## Secrets Management

- `AWS_BEARER_TOKEN_BEDROCK`는 환경변수로만 전달. 코드/로그/커밋에 절대 포함 금지
- `.env` 파일은 `.gitignore`에 포함되어 있음. `.env.example`에는 placeholder만 사용
- 토큰 값을 echo/print/log하지 않을 것. 존재 여부만 확인 (`<set>` / `NOT SET`)

## Secret Patterns (탐지 대상)

- `ABSK[A-Za-z0-9+/]{60,}={0,2}` — Bedrock API Key
- `AKIA[0-9A-Z]{16}` — AWS Access Key ID
- `sk-ant-[A-Za-z0-9-]{90,}` — Anthropic API Key
- `ghp_[A-Za-z0-9]{36}` — GitHub PAT
- `password/secret/api_key` 할당문

## Known Synthetic Patterns (False-Positive Whitelist)

본 repo는 secret-scan 인프라(스캐너 + fixture + ADR + template) 자체를
정식 컴포넌트로 보유하기 때문에, 아래 경로들은 **의도적으로** secret
패턴 매칭 문자열을 포함한다. 이는 누출이 아니며 review gate에서 high
severity로 flag하지 말 것.

| 경로 | 종류 | 식별 |
|---|---|---|
| `tests/_meta/fixtures/secret-samples.txt` | true-positive 회귀 fixture | line 2: "FAKE values formed to match the regexes" |
| `tests/_meta/fixtures/false-positives.txt` | false-positive 회귀 fixture | placeholder 형식 (`ABSK...replace-me` 등) |
| `.env.example` | 환경변수 템플릿 | `AWS_BEARER_TOKEN_BEDROCK=ABSK...replace-me` |
| `.claude/hooks/secret-scan.sh` | 스캐너 정규식 정의 | `'ABSK[A-Za-z0-9+/]{60,}={0,2}'` (literal token 아님) |
| `tests/_meta/hooks/test-secret-patterns.sh` | 위 정규식의 회귀 러너 | 동일 정규식 |
| `.claude/agents/security-auditor.yml` | agent 설명 문구 | "Bedrock API keys (ABSK...)" 류 자연어 |
| `docs/decisions/ADR-002-runtime-secret-scanning.md` | secret-scan 도입 ADR | 패턴 디스크립터 |

**진짜 누출 판단 기준**: 위 표에 없는 새로운 경로에서 ABSK/AKIA/sk-ant
literal이 등장한 경우만 high. 기존 화이트리스트 경로 내 변경은 medium
이하로 처리하거나 무시.

검증 명령:

```bash
# .env가 한 번도 추적된 적 없는지 확인 — 빈 결과여야 함
git log --all --diff-filter=A --name-only --pretty=format: -- .env

# ABSK literal을 도입한 모든 커밋 — 5c2b222(initial commit)만 정상
git log --all -S "ABSK" --oneline
```

`5c2b222` 외의 커밋이 ABSK literal을 도입했다면 그때만 실제 leak 의심
플로우(즉시 회전, history 정화)로 진입.

## Forbidden Actions

- `rm -rf`, `rm -r` — 재귀 삭제 금지
- `git push --force`, `git reset --hard`, `git clean -f` — 파괴적 git 명령 금지
- `curl * | bash`, `wget * | bash`, `eval` — 원격 코드 실행 금지
- `chmod 777` — 과도한 권한 부여 금지

## Allowed Execution

- `python3 run_all.py` (모든 인자)
- `python3 scripts/probe_*.py`
- `./verify.sh` (모든 인자)
- `bash scripts/*.sh`

## Commit Hygiene

- `.env`, `logs/`, `__pycache__/` 는 커밋하지 않을 것
- `settings.local.json`은 개인 설정이므로 커밋 제외
- 커밋 전 staged 파일에 secret pattern이 없는지 확인

## Intercept Proxy

`scripts/intercept_proxy.py`는 Authorization 헤더를 redact하지만,
`logs/intercept.jsonl`에 민감 데이터가 남을 수 있으므로 `.gitignore`에 포함.
