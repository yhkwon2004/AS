import asyncio
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, UnidentifiedImageError

app = FastAPI(title="ASCII 비디오 플레이어")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

STOP_FLAGS: dict[str, asyncio.Event] = {}
ASCII_TABLE = " .,:;irsXA253hMHGS#9B&@"
FPS = 12
ASCII_WIDTH = 96
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


def frame_to_ascii(frame_path: Path, width: int = ASCII_WIDTH) -> str:
    try:
        img = Image.open(frame_path).convert("L")
    except (UnidentifiedImageError, OSError):
        return ""

    aspect = img.height / max(1, img.width)
    height = max(1, int(width * aspect * 0.55))
    img = img.resize((width, height))

    pixels = img.getdata()
    chars = [ASCII_TABLE[p * (len(ASCII_TABLE) - 1) // 255] for p in pixels]
    rows = ["".join(chars[i : i + width]) for i in range(0, len(chars), width)]
    return "\n".join(rows)


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    ext = Path(file.filename or "video.mp4").suffix.lower() or ".mp4"
    file_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{file_id}{ext}"

    total = 0
    with save_path.open("wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_FILE_SIZE:
                f.close()
                save_path.unlink(missing_ok=True)
                return JSONResponse({"message": "파일이 너무 큽니다. (최대 100MB)"}, status_code=413)
            f.write(chunk)

    return JSONResponse({"file_id": file_id, "filename": file.filename})


@app.websocket("/ws/play/{file_id}")
async def play_ascii_video(ws: WebSocket, file_id: str):
    await ws.accept()
    video_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))

    if not video_files:
        await ws.send_text("[오류] 파일을 찾을 수 없습니다.")
        await ws.close()
        return

    stop_event = asyncio.Event()
    STOP_FLAGS[file_id] = stop_event
    temp_dir = Path(tempfile.mkdtemp(prefix="ascii_frames_"))
    video_path = video_files[0]

    try:
        ffmpeg_cmd = (
            f'ffmpeg -hide_banner -loglevel error -i "{video_path}" '
            f'-vf fps={FPS},scale={ASCII_WIDTH}:-1 "{temp_dir}/frame_%06d.jpg"'
        )
        proc = await asyncio.create_subprocess_shell(ffmpeg_cmd)
        rc = await proc.wait()
        if rc != 0:
            await ws.send_text("[오류] ffmpeg 프레임 추출에 실패했습니다.")
            await ws.close()
            return

        frames = sorted(temp_dir.glob("frame_*.jpg"))
        if not frames:
            await ws.send_text("[오류] 추출된 프레임이 없습니다.")
            await ws.close()
            return

        await ws.send_text("[안내] ASCII 재생을 시작합니다.\n")
        for frame in frames:
            if stop_event.is_set():
                await ws.send_text("\n[안내] 재생이 중지되었습니다.")
                break
            ascii_art = frame_to_ascii(frame)
            if ascii_art:
                await ws.send_text("\x1b[2J\x1b[H" + ascii_art)
                await asyncio.sleep(1 / FPS)

        await ws.send_text("\n[안내] 재생이 완료되었습니다.")

    except WebSocketDisconnect:
        pass
    finally:
        STOP_FLAGS.pop(file_id, None)
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/stop/{file_id}")
async def stop(file_id: str):
    event = STOP_FLAGS.get(file_id)
    if not event:
        return JSONResponse({"ok": False, "message": "실행 중인 재생이 없습니다."}, status_code=404)
    event.set()
    return JSONResponse({"ok": True, "message": "중지 요청을 보냈습니다."})
