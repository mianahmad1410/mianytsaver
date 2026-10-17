from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp, os, uuid, threading

app = Flask(__name__)
OUT = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(OUT, exist_ok=True)

@app.get('/')
def home():
    return render_template('index.html')

@app.post('/download')
def download():
    data = request.get_json(force=True)
    url = (data.get('url') or '').strip()
    mode = data.get('mode', 'video')
    quality = data.get('quality', 'best')
    if not url.startswith(('https://', 'http://')):
        return jsonify(error='Please enter a valid video URL.'), 400
    stem = uuid.uuid4().hex
    if mode == 'audio':
        fmt = 'bestaudio/best'
        opts = {'format': fmt, 'outtmpl': os.path.join(OUT, stem + '.%(ext)s'),
                'noplaylist': True, 'quiet': True, 'no_warnings': True,
                'postprocessors': [{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}]}
    else:
        if quality == 'best': fmt = 'bestvideo+bestaudio/best'
        else: fmt = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best[height<={quality}]'
        opts = {'format': fmt, 'outtmpl': os.path.join(OUT, stem + '.%(ext)s'),
                'merge_output_format':'mp4', 'noplaylist': True, 'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'download')
        candidates = [os.path.join(OUT, f) for f in os.listdir(OUT) if f.startswith(stem + '.')]
        if not candidates:
            return jsonify(error='Download finished but output file was not found. Check FFmpeg installation for MP3/merging.'), 500
        path = max(candidates, key=os.path.getmtime)
        return send_file(path, as_attachment=True, download_name=os.path.basename(title).replace('/', '_') + os.path.splitext(path)[1])
    except Exception as e:
        return jsonify(error=str(e)[:600]), 400

if __name__ == '__main__':
    print('Open http://127.0.0.1:5000 in your browser')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
