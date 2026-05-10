const term = new Terminal({
  cursorBlink: false,
  fontFamily: 'monospace',
  fontSize: 12,
  rows: 40,
  cols: 100,
  theme: { background: '#000000', foreground: '#cfcfcf' }
});
term.open(document.getElementById('terminal'));
term.writeln('ASCII 비디오 플레이어 준비 완료.');

const fileInput = document.getElementById('videoFile');
const uploadBtn = document.getElementById('uploadBtn');
const playBtn = document.getElementById('playBtn');
const stopBtn = document.getElementById('stopBtn');
const statusEl = document.getElementById('status');

let fileId = null;
let ws = null;

function setStatus(text) { statusEl.textContent = `상태: ${text}`; }

uploadBtn.onclick = async () => {
  const file = fileInput.files[0];
  if (!file) return setStatus('업로드할 파일을 선택하세요.');

  const formData = new FormData();
  formData.append('file', file);

  setStatus('업로드 중...');
  const res = await fetch('/upload', { method: 'POST', body: formData });
  if (!res.ok) return setStatus('업로드 실패');

  const data = await res.json();
  fileId = data.file_id;
  playBtn.disabled = false;
  stopBtn.disabled = false;
  setStatus(`업로드 완료 (${data.filename})`);
};

playBtn.onclick = () => {
  if (!fileId) return setStatus('먼저 파일을 업로드하세요.');
  term.clear();
  setStatus('재생 중...');

  ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/play/${fileId}`);
  ws.onmessage = (e) => {
    term.write(e.data);
  };
  ws.onclose = () => setStatus('재생 종료');
};

stopBtn.onclick = async () => {
  if (!fileId) return;
  await fetch(`/stop/${fileId}`, { method: 'POST' });
  setStatus('중지 요청 보냄');
};
