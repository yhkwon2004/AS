# 한국어 친화형 ASCII 비디오 웹 플레이어

`asciiplayer` 아이디어를 참고해, 웹에서 영상을 업로드하면 내장된 터미널 UI에서 ASCII 애니메이션으로 재생하는 서비스입니다.

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Vercel 배포

이 프로젝트는 Vercel Python 서버리스에 맞춰 `vercel.json` + `api/index.py`를 포함합니다.

```bash
npm i -g vercel
vercel
```

### Vercel에서 500(FUNCTION_INVOCATION_FAILED) 날 때 체크

- 업로드/임시파일은 `/tmp`만 사용 가능 → 코드에서 `/tmp/ascii_uploads` 사용하도록 수정됨.
- Vercel 함수 실행 시간 제한이 짧아서 긴 영상은 실패할 수 있음.
- 이 프로젝트는 WebSocket 대신 SSE(`/stream/{file_id}`)를 사용해 서버리스 환경 충돌을 줄였습니다.

## Render/Docker 배포 (권장)

긴 영상/안정적인 재생은 Render 같은 컨테이너 환경을 권장합니다.

```bash
docker build -t ascii-web .
docker run --rm -p 8000:8000 ascii-web
```
