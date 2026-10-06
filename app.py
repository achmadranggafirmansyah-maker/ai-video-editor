from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid, shutil, subprocess, json, os

BASE = Path(__file__).parent
UPLOADS = BASE / 'uploads'; OUTPUTS = BASE / 'outputs'
UPLOADS.mkdir(exist_ok=True); OUTPUTS.mkdir(exist_ok=True)

app = FastAPI(title='AI Video Editor')
app.mount('/static', StaticFiles(directory=BASE/'static'), name='static')
app.mount('/outputs', StaticFiles(directory=OUTPUTS), name='outputs')

MAX_BYTES = 1024 * 1024 * 1024
MAX_SECONDS = 300

@app.get('/')
def home():
    return FileResponse(BASE/'static/index.html')

def ffprobe_duration(path: Path):
    p = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],capture_output=True,text=True)
    if p.returncode != 0: raise HTTPException(400,'Video tidak valid atau tidak bisa dibaca.')
    return float(p.stdout.strip())

def run_ffmpeg(src, out, ratio, resolution, style):
    # Lightweight real processing MVP: normalize/crop, preserve audio, add subtle punch-in.
    sizes = {
        '1080p': {'9:16':'1080:1920','1:1':'1080:1080','16:9':'1920:1080'},
        '4K': {'9:16':'2160:3840','1:1':'2160:2160','16:9':'3840:2160'},
        '720p': {'9:16':'720:1280','1:1':'720:720','16:9':'1280:720'},
    }
    target = sizes.get(resolution, sizes['1080p']).get(ratio, '1080:1920')
    w,h = target.split(':')
    # Fit/crop to requested ratio then scale. Style preset controls a subtle zoom/punch-in.
    zoom = '1.00'
    if style == 'reference_storytelling': zoom = '1.025'
    elif style == 'clean_creator': zoom = '1.015'
    vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,scale=iw*{zoom}:ih*{zoom},crop={w}:{h}"
    cmd = ['ffmpeg','-y','-i',str(src),'-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','20','-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)]
    p = subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode != 0:
        raise HTTPException(500, 'Gagal memproses video: '+p.stderr[-800:])

@app.post('/api/edit')
async def edit(video: UploadFile = File(...), brief: str = Form(''), style: str = Form('reference_storytelling'), ratio: str = Form('9:16'), resolution: str = Form('1080p')):
    if not video.filename.lower().endswith(('.mp4','.mov','.m4v','.webm','.mkv')):
        raise HTTPException(400,'Format video belum didukung. Gunakan MP4/MOV/WebM/MKV.')
    job = uuid.uuid4().hex
    src = UPLOADS/f'{job}_{Path(video.filename).name}'
    out = OUTPUTS/f'{job}.mp4'
    with src.open('wb') as f:
        shutil.copyfileobj(video.file, f)
    if src.stat().st_size > MAX_BYTES:
        src.unlink(missing_ok=True); raise HTTPException(413,'Ukuran video terlalu besar.')
    duration = ffprobe_duration(src)
    if duration > MAX_SECONDS + 0.5:
        src.unlink(missing_ok=True); raise HTTPException(400,'Durasi video maksimal 5 menit.')
    run_ffmpeg(src,out,ratio,resolution,style)
    src.unlink(missing_ok=True)
    return JSONResponse({'ok':True,'job_id':job,'duration':duration,'preview':f'/outputs/{job}.mp4','download':f'/api/download/{job}'})

@app.get('/api/download/{job_id}')
def download(job_id: str):
    path = OUTPUTS/f'{job_id}.mp4'
    if not path.exists(): raise HTTPException(404,'Hasil video tidak ditemukan.')
    return FileResponse(path, media_type='video/mp4', filename=f'ai-edit-{job_id[:8]}.mp4')
