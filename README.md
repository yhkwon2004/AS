# 한국어 친화형 ASCII 비디오 웹 플레이어

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Vercel 배포 (완료 절차)

### 1) Vercel 프로젝트 연결

```bash
npx vercel link
```

### 2) 로컬에서 프로덕션 배포

아래 환경변수 3개를 준비한 뒤:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

```bash
./scripts/deploy_vercel.sh
```

### 3) GitHub Actions 자동 배포

`.github/workflows/vercel-deploy.yml` 포함되어 있습니다.
GitHub 저장소 Secret에 `VERCEL_TOKEN` 추가하면 `work` 브랜치 push 시 프로덕션 배포됩니다.

## Vercel 500 (FUNCTION_INVOCATION_FAILED) 대응

- 서버 임시 저장 경로를 `/tmp`로 고정 (`/tmp/ascii_uploads`)
- 스트리밍 방식을 WebSocket 대신 SSE로 전환
- 긴 영상은 함수 실행 제한으로 실패할 수 있어 영상 길이를 짧게 유지 권장
