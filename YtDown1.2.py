import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
import subprocess
import urllib.request

APPDATA_DIR = os.path.join(os.getenv('APPDATA'), 'ElAlehYt_Down')
os.makedirs(APPDATA_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(APPDATA_DIR, 'config.json')
YTDLP_PATH = os.path.join(APPDATA_DIR, "yt-dlp.exe")


# =========================
# yt-dlp SETUP
# =========================
def ensure_ytdlp():
    if not os.path.exists(YTDLP_PATH):
        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
        urllib.request.urlretrieve(url, YTDLP_PATH)


def update_ytdlp():
    try:
        subprocess.run([YTDLP_PATH, "-U"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass


# =========================
# Traducciones
# =========================
translations = {
    "es": {
        "title": "Descargador de Vídeos",
        "url": "URL del vídeo",
        "path": "Ruta de descarga",
        "browse": "Examinar",
        "save": "Guardar ruta",
        "fetch": "Obtener calidades",
        "format": "Formato",
        "video": "Vídeo + audio",
        "audio": "Solo audio",
        "quality": "Calidad",
        "download": "Descargar",
        "downloading": "Descargando…",
        "status_wait": "Esperando",
        "status_fetching": "Obteniendo calidades…",
        "status_down": "Descargando…",
        "status_processing": "Procesando…",
        "status_done": "Descarga completada",
        "confirm": "¿Deseas continuar?",
        "error": "Error",
        "lang": "Change To English",
        "path_saved": "Ruta guardada correctamente",
        "res_fetched": "Calidades obtenidas correctamente",
        "setup": "Iniciando yt-dlp…"
    },
    "en": {
        "title": "Video Downloader",
        "url": "Video URL",
        "path": "Download path",
        "browse": "Browse",
        "save": "Save path",
        "fetch": "Fetch qualities",
        "format": "Format",
        "video": "Video + audio",
        "audio": "Audio only",
        "quality": "Quality",
        "download": "Download",
        "downloading": "Downloading…",
        "status_wait": "Waiting",
        "status_fetching": "Fetching qualities…",
        "status_down": "Downloading…",
        "status_processing": "Processing…",
        "status_done": "Download completed",
        "confirm": "Do you want to continue?",
        "error": "Error",
        "lang": "Cambiar a Español",
        "path_saved": "Path saved successfully",
        "res_fetched": "Available qualities fetched successfully",
        "setup": "Setting up yt-dlp…"
    }
}


class App:
    def __init__(self, root):
        self.root = root
        self.is_downloading = False
        self.last_progress = -1
        self.load_config()
        self.build_ui()
        self.update_texts()
        # ✅ Abre la ventana al instante, yt-dlp se descarga/actualiza en segundo plano
        self.root.after(100, lambda: threading.Thread(target=self._setup_ytdlp, daemon=True).start())

    def t(self, k): return translations[self.lang][k]
    def ui(self, f): self.root.after(0, f)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            self.config = json.load(open(CONFIG_FILE, 'r', encoding='utf-8'))
        else:
            self.config = {}
        self.lang = self.config.get('lang', 'es')

    def save_config(self):
        json.dump(self.config, open(CONFIG_FILE, 'w', encoding='utf-8'), indent=2)

    def _setup_ytdlp(self):
        self.ui(lambda: self.status.config(text=self.t('setup')))
        ensure_ytdlp()
        update_ytdlp()
        self.ui(lambda: self.status.config(text=self.t('status_wait')))

    def build_ui(self):
        self.root.title(self.t('title'))
        self.root.geometry("600x470")
        self.root.resizable(False, False)

        main = ttk.Frame(self.root, padding=15)
        main.grid(sticky="nsew")

        self.url_label = ttk.Label(main)
        self.url_label.grid(row=0, column=0, sticky="w")
        self.url = ttk.Entry(main, width=60)
        self.url.grid(row=1, column=0, columnspan=3, pady=5)

        self.path_label = ttk.Label(main)
        self.path_label.grid(row=2, column=0, sticky="w")
        self.path = ttk.Entry(main, width=45)
        self.path.grid(row=3, column=0, columnspan=2, sticky="w")
        self.path.insert(0, self.config.get('path', ''))

        self.browse_btn = ttk.Button(main, command=self.browse)
        self.browse_btn.grid(row=3, column=2)

        self.save_btn = ttk.Button(main, command=self.save_path)
        self.save_btn.grid(row=4, column=2, pady=5)

        self.fetch_btn = ttk.Button(main, command=self.fetch)
        self.fetch_btn.grid(row=5, column=0, pady=5)

        self.format_label = ttk.Label(main)
        self.format_label.grid(row=6, column=0, sticky="w")

        self.format = tk.StringVar(value="video")
        self.radio_video = ttk.Radiobutton(main, variable=self.format, value="video")
        self.radio_audio = ttk.Radiobutton(main, variable=self.format, value="audio")
        self.radio_video.grid(row=7, column=0, sticky="w")
        self.radio_audio.grid(row=7, column=1, sticky="w")

        self.quality_label = ttk.Label(main)
        self.quality_label.grid(row=8, column=0, sticky="w")

        self.quality = ttk.Combobox(main, state="readonly")
        self.quality.grid(row=9, column=0, columnspan=2, sticky="w")

        self.progress = ttk.Progressbar(main, length=500, mode='determinate')
        self.progress.grid(row=10, column=0, columnspan=3, pady=10)

        self.status = ttk.Label(main)
        self.status.grid(row=11, column=0, sticky="w")

        self.download_btn = ttk.Button(main, command=self.confirm)
        self.download_btn.grid(row=12, column=0, pady=10)

        self.lang_btn = ttk.Button(main, command=self.toggle_lang)
        self.lang_btn.grid(row=12, column=2)

    def update_texts(self):
        self.root.title(self.t('title'))
        self.url_label.config(text=self.t('url'))
        self.path_label.config(text=self.t('path'))
        self.format_label.config(text=self.t('format'))
        self.radio_video.config(text=self.t('video'))
        self.radio_audio.config(text=self.t('audio'))
        self.quality_label.config(text=self.t('quality'))
        self.download_btn.config(text=self.t('download'))
        self.browse_btn.config(text=self.t('browse'))
        self.save_btn.config(text=self.t('save'))
        self.fetch_btn.config(text=self.t('fetch'))
        self.lang_btn.config(text=self.t('lang'))
        if not self.is_downloading:
            self.status.config(text=self.t('status_wait'))

    def toggle_lang(self):
        self.lang = 'en' if self.lang == 'es' else 'es'
        self.config['lang'] = self.lang
        self.save_config()
        self.update_texts()

    def browse(self):
        p = filedialog.askdirectory()
        if p:
            self.path.delete(0, tk.END)
            self.path.insert(0, p)

    def save_path(self):
        self.config['path'] = self.path.get()
        self.save_config()
        messagebox.showinfo(self.t('path_saved'), self.t('path_saved'))

    # ✅ fetch en hilo secundario para no congelar la UI
    def fetch(self):
        self.fetch_btn.config(state='disabled')
        self.status.config(text=self.t('status_fetching'))
        threading.Thread(target=self._fetch_thread, daemon=True).start()

    def _fetch_thread(self):
        try:
            result = subprocess.run(
                [YTDLP_PATH, "-F", self.url.get()],
                capture_output=True, text=True
            )
            qualities = []
            for line in result.stdout.splitlines():
                parts = line.split()
                for p in parts:
                    if p.endswith("p") and p[:-1].isdigit():
                        qualities.append(p)
            qualities = sorted(set(qualities), key=lambda x: int(x[:-1]), reverse=True)

            def on_done():
                self.quality['values'] = ['Best'] + qualities
                self.quality.current(0)
                self.fetch_btn.config(state='normal')
                self.status.config(text=self.t('status_wait'))
                messagebox.showinfo(self.t('res_fetched'), self.t('res_fetched'))
            self.ui(on_done)
        except Exception as e:
            err = str(e)
            self.ui(lambda: (
                messagebox.showerror(self.t('error'), err),
                self.fetch_btn.config(state='normal'),
                self.status.config(text=self.t('status_wait'))
            ))

    def confirm(self):
        if self.is_downloading:
            return
        if messagebox.askyesno(self.t('download'), self.t('confirm')):
            self.lock()
            threading.Thread(target=self.download, daemon=True).start()

    def lock(self):
        self.is_downloading = True
        self.last_progress = -1
        self.progress['value'] = 0
        self.progress['mode'] = 'indeterminate'
        self.progress.start(10)
        self.download_btn.config(state='disabled', text=self.t('downloading'))

    def unlock(self):
        self.is_downloading = False
        self.download_btn.config(state='normal', text=self.t('download'))
        self.progress.stop()
        self.progress['mode'] = 'determinate'
        self.progress['value'] = 100
        self.status.config(text=self.t('status_done'))

    def download(self):
        try:
            cmd = [
                YTDLP_PATH,
                self.url.get(),
                "-o", os.path.join(self.path.get(), "%(title)s.%(ext)s"),
                "--newline"  # ✅ output línea a línea para leer progreso
            ]

            if self.format.get() == "audio":
                cmd += ["-x", "--audio-format", "mp3"]
            else:
                q = self.quality.get()
                if q not in ("", "Best"):
                    cmd += ["-f", f"bestvideo[height<={q[:-1]}]+bestaudio/best"]
                else:
                    cmd += ["-f", "bestvideo+bestaudio/best"]

            self.ui(lambda: self.status.config(text=self.t('status_down')))

            # ✅ Lee el output en tiempo real para actualizar la barra de progreso
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                line = line.strip()
                if '[download]' in line and '%' in line:
                    try:
                        percent_str = line.split('%')[0].split()[-1]
                        percent = float(percent_str)
                        if percent != self.last_progress:
                            self.last_progress = percent
                            self.ui(lambda p=percent: (
                                self.progress.stop(),
                                self.progress.config(mode='determinate', value=p)
                            ))
                        # ETA
                        if 'ETA' in line:
                            eta = line.split('ETA')[-1].strip()
                            self.ui(lambda e=eta: self.status.config(
                                text=f"{self.t('status_down')} - ETA {e}"
                            ))
                    except:
                        pass
                elif 'Merging' in line or 'ffmpeg' in line.lower():
                    self.ui(lambda: self.status.config(text=self.t('status_processing')))

            process.wait()
            self.ui(self.unlock)

        except Exception as e:
            err = str(e)
            self.ui(lambda: (messagebox.showerror(self.t('error'), err), self.unlock()))


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()