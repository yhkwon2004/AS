import asyncio
import os
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, UnidentifiedImageError

app = FastAPI(title="ASCII 비디오 플레이어")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

BASE_TMP = Path(os.getenv("TMPDIR", "/tmp"))
UPLOAD_DIR = BASE_TMP / "ascii_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

STOP_FLAGS: dict[str, asyncio.Event] = {}
ASCII_TABLE = " .,:;irsXA253hMHGS#9B&@"
FPS = 12
ASCII_WIDTH = 96
MAX_FILE_SIZE = 50 * 1024 * 1024


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
    return {"ok": True, "tmp": str(UPLOAD_DIR)}


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
                save_path.unlink(missing_ok=True)
                return JSONResponse({"message": "파일이 너무 큽니다. (최대 50MB)"}, status_code=413)
            f.write(chunk)

    return JSONResponse({"file_id": file_id, "filename": file.filename})


@app.get("/stream/{file_id}")
async def stream_ascii_video(file_id: str):
    video_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not video_files:
        return JSONResponse({"message": "파일을 찾을 수 없습니다."}, status_code=404)

    stop_event = asyncio.Event()
    STOP_FLAGS[file_id] = stop_event
    video_path = video_files[0]
    temp_dir = Path(tempfile.mkdtemp(prefix="ascii_frames_", dir=str(BASE_TMP)))

    async def event_gen():
        try:
            cmd = (
                f'ffmpeg -hide_banner -loglevel error -i "{video_path}" '
                f'-vf fps={FPS},scale={ASCII_WIDTH}:-1 "{temp_dir}/frame_%06d.jpg"'
            )
            proc = await asyncio.create_subprocess_shell(cmd)
            rc = await proc.wait()
            if rc != 0:
                yield "event: error\ndata: ffmpeg 실행 실패\n\n"
                return

            frames = sorted(temp_dir.glob("frame_*.jpg"))
            yield "event: status\ndata: 재생 시작\n\n"
            for frame in frames:
                if stop_event.is_set():
                    yield "event: status\ndata: 재생 중지\n\n"
                    break
                art = frame_to_ascii(frame)
                if art:
                    payload = art.replace("\n", "\\n")
                    yield f"event: frame\ndata: {payload}\n\n"
                await asyncio.sleep(1 / FPS)
            yield "event: done\ndata: 재생 완료\n\n"
        finally:
            STOP_FLAGS.pop(file_id, None)
            shutil.rmtree(temp_dir, ignore_errors=True)

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.post("/stop/{file_id}")
async def stop(file_id: str):
    event = STOP_FLAGS.get(file_id)
    if not event:
        return JSONResponse({"ok": False, "message": "실행 중인 재생이 없습니다."}, status_code=404)
    event.set()
    return JSONResponse({"ok": True})
