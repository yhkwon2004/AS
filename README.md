# 한국어 친화형 ASCII 비디오 웹 플레이어

`asciiplayer` 아이디어를 참고해, 웹에서 영상을 업로드하면 내장된 터미널 UI에서 ASCII 애니메이션으로 재생하는 서비스입니다.

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000` 접속.

## 기능

- 한국어 중심 UI (업로드/재생/중지/상태 안내)
- 업로드 영상 프레임을 ASCII로 변환
- 웹페이지 내 터미널(`xterm.js`)에 애니메이션 출력
- 재생 중단 기능
- 헬스체크 엔드포인트 `/health`

## 웹 배포 (Render)

이 저장소는 `render.yaml`과 `Dockerfile`을 포함해 바로 배포할 수 있습니다.

1. GitHub에 이 레포지토리 푸시
2. [Render](https://render.com)에서 **New +** → **Blueprint** 선택
3. 해당 GitHub repo 연결 후 생성
4. 배포 완료 후 발급된 URL로 접속

Render는 Docker 빌드 시 `ffmpeg`를 함께 설치하므로 별도 서버 세팅이 필요 없습니다.

## Docker로 직접 실행

```bash
docker build -t ascii-web .
docker run --rm -p 8000:8000 ascii-web
```

## 요구사항

- Python 3.10+
- 로컬 실행 시 시스템 `ffmpeg` 설치 필요
