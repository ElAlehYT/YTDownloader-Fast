import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
import re
import shutil
import subprocess
import urllib.request
import logging

APPDATA_DIR = os.path.join(os.getenv('APPDATA'), 'ElAlehYt_Down')
os.makedirs(APPDATA_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(APPDATA_DIR, 'config.json')
YTDLP_PATH = os.path.join(APPDATA_DIR, "yt-dlp.exe")
LOG_FILE = os.path.join(APPDATA_DIR, "app.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# Flags para que subprocess no abra ventanas de consola en Windows
CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0


# =========================
# yt-dlp SETUP
# =========================
def ensure_ytdlp():
    if not os.path.exists(YTDLP_PATH):
        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
        tmp_path = YTDLP_PATH + ".tmp"
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status} al descargar yt-dlp")
                with open(tmp_path, 'wb') as f:
                    shutil.copyfileobj(resp, f)
            # Sanity check: el ejecutable debe pesar más de ~1MB
            if os.path.getsize(tmp_path) < 1_000_000:
                raise RuntimeError("Descarga de yt-dlp incompleta o corrupta")
            os.replace(tmp_path, YTDLP_PATH)
        except Exception as e:
            logging.error(f"Error descargando yt-dlp: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise


def update_ytdlp():
    try:
        subprocess.run(
            [YTDLP_PATH, "-U"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW
        )
    except Exception as e:
        logging.warning(f"No se pudo actualizar yt-dlp: {e}")


def ffmpeg_available():
    return shutil.which("ffmpeg") is not None


# =========================
# Paleta / tema visual
# =========================
COLORS = {
    "bg":        "#161a23",   # fondo ventana
    "card":      "#1f2430",   # tarjeta principal
    "card_alt":  "#262c3b",   # inputs / campos
    "border":    "#323a4d",
    "text":      "#e7e9f0",
    "muted":     "#8992a8",
    "accent":    "#7c6ff0",   # violeta principal
    "accent_hv": "#6a5cf0",
    "accent_dk": "#5b4de0",
    "success":   "#3ddc84",
    "warning":   "#f0b429",
    "danger":    "#f0576f",
}
FONT_FAMILY = "Segoe UI"



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
        "bitrate": "Bitrate audio",
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
        "setup": "Iniciando yt-dlp…",
        "err_no_url": "Introduce una URL",
        "err_no_path": "Selecciona una ruta de descarga válida",
        "err_no_ffmpeg": "No se encontró ffmpeg. Instálalo y añádelo al PATH para poder unir vídeo+audio o convertir a mp3.",
        "err_ytdlp_setup": "No se pudo preparar yt-dlp. Revisa tu conexión a internet."
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
        "bitrate": "Audio bitrate",
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
        "setup": "Setting up yt-dlp…",
        "err_no_url": "Enter a URL",
        "err_no_path": "Select a valid download path",
        "err_no_ffmpeg": "ffmpeg was not found. Install it and add it to PATH to merge video+audio or convert to mp3.",
        "err_ytdlp_setup": "Could not set up yt-dlp. Check your internet connection."
    }
}


class App:
    def __init__(self, root):
        self.root = root
        self.is_downloading = False
        self.is_fetching = False
        self.last_progress = -1
        self.current_process = None
        self.ytdlp_ready = False
        self.load_config()
        self.build_ui()
        self.update_texts()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # Abre la ventana al instante, yt-dlp se descarga/actualiza en segundo plano
        self.root.after(100, lambda: threading.Thread(target=self._setup_ytdlp, daemon=True).start())

    def t(self, k): return translations[self.lang][k]
    def ui(self, f): self.root.after(0, f)

    def load_config(self):
        self.config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                logging.warning(f"config.json corrupto, se ignora: {e}")
                self.config = {}
        self.lang = self.config.get('lang', 'es')

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"No se pudo guardar config.json: {e}")

    def _setup_ytdlp(self):
        self.ui(lambda: self.status.config(text=self.t('setup')))
        try:
            ensure_ytdlp()
            update_ytdlp()
            self.ytdlp_ready = True
        except Exception:
            self.ui(lambda: messagebox.showerror(self.t('error'), self.t('err_ytdlp_setup')))
        self.ui(lambda: self.status.config(text=self.t('status_wait')))
        if not ffmpeg_available():
            self.ui(lambda: messagebox.showwarning(self.t('error'), self.t('err_no_ffmpeg')))

    # =========================
    # Estilos visuales
    # =========================
    def setup_styles(self):
        c = COLORS
        self.root.configure(bg=c["bg"])

        # Listas desplegables (combobox) usan option database para el popup
        self.root.option_add("*TCombobox*Listbox.background", c["card_alt"])
        self.root.option_add("*TCombobox*Listbox.foreground", c["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", c["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", c["text"])
        self.root.option_add("*TCombobox*Listbox.font", (FONT_FAMILY, 10))

        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".", background=c["bg"], foreground=c["text"],
                         font=(FONT_FAMILY, 10))

        style.configure("Card.TFrame", background=c["card"])
        style.configure("Bg.TFrame", background=c["bg"])

        style.configure("Title.TLabel", background=c["card"], foreground=c["text"],
                         font=(FONT_FAMILY, 17, "bold"))
        style.configure("Subtitle.TLabel", background=c["card"], foreground=c["muted"],
                         font=(FONT_FAMILY, 9))
        style.configure("Section.TLabel", background=c["card"], foreground=c["accent"],
                         font=(FONT_FAMILY, 10, "bold"))
        style.configure("Field.TLabel", background=c["card"], foreground=c["muted"],
                         font=(FONT_FAMILY, 9))
        style.configure("Status.TLabel", background=c["card"], foreground=c["muted"],
                         font=(FONT_FAMILY, 9))
        style.configure("Percent.TLabel", background=c["card"], foreground=c["text"],
                         font=(FONT_FAMILY, 9, "bold"))

        style.configure("TEntry", fieldbackground=c["card_alt"], foreground=c["text"],
                         bordercolor=c["border"], lightcolor=c["card_alt"],
                         darkcolor=c["card_alt"], insertcolor=c["text"],
                         padding=8, borderwidth=1, relief="flat")
        style.map("TEntry", bordercolor=[("focus", c["accent"])])

        style.configure("TCombobox", fieldbackground=c["card_alt"], background=c["card_alt"],
                         foreground=c["text"], arrowcolor=c["muted"],
                         bordercolor=c["border"], lightcolor=c["card_alt"],
                         darkcolor=c["card_alt"], padding=6, borderwidth=1, relief="flat")
        style.map("TCombobox",
                  fieldbackground=[("readonly", c["card_alt"])],
                  foreground=[("readonly", c["text"])],
                  bordercolor=[("focus", c["accent"])])

        # Botón principal (acento)
        style.configure("Accent.TButton", background=c["accent"], foreground="#ffffff",
                         font=(FONT_FAMILY, 10, "bold"), padding=(14, 9), borderwidth=0,
                         relief="flat")
        style.map("Accent.TButton",
                  background=[("disabled", c["border"]), ("pressed", c["accent_dk"]),
                              ("active", c["accent_hv"])],
                  foreground=[("disabled", c["muted"])])

        # Botón secundario (contorno)
        style.configure("Ghost.TButton", background=c["card"], foreground=c["text"],
                         font=(FONT_FAMILY, 9), padding=(10, 7), borderwidth=1,
                         bordercolor=c["border"], relief="flat")
        style.map("Ghost.TButton",
                  background=[("active", c["card_alt"])],
                  bordercolor=[("active", c["accent"])],
                  foreground=[("active", c["text"])])

        # Botón pequeño de icono (browse)
        style.configure("Icon.TButton", background=c["card_alt"], foreground=c["text"],
                         font=(FONT_FAMILY, 10), padding=(10, 7), borderwidth=1,
                         bordercolor=c["border"], relief="flat")
        style.map("Icon.TButton",
                  background=[("active", c["accent"])],
                  foreground=[("active", "#ffffff")])

        style.configure("TRadiobutton", background=c["card"], foreground=c["text"],
                         font=(FONT_FAMILY, 10), indicatorcolor=c["card_alt"],
                         indicatorbackground=c["card_alt"], focuscolor=c["card"])
        style.map("TRadiobutton",
                  indicatorcolor=[("selected", c["accent"])],
                  foreground=[("selected", c["text"])])

        style.configure("TProgressbar", troughcolor=c["card_alt"], background=c["accent"],
                         bordercolor=c["card_alt"], lightcolor=c["accent"],
                         darkcolor=c["accent"], thickness=10)

        style.configure("Sep.TSeparator", background=c["border"])

    def build_ui(self):
        c = COLORS
        self.setup_styles()

        self.root.title(self.t('title'))
        self.root.resizable(False, False)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        outer = ttk.Frame(self.root, style="Bg.TFrame", padding=18)
        outer.grid(sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        card = ttk.Frame(outer, style="Card.TFrame", padding=24)
        card.grid(sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=0)

        row = 0

        # --- Cabecera ---
        header = ttk.Frame(card, style="Card.TFrame")
        header.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 18))
        header.grid_columnconfigure(0, weight=1)
        self.title_label = ttk.Label(header, style="Title.TLabel", text="🎬  " + self.t('title'))
        self.title_label.grid(row=0, column=0, sticky="w")
        self.lang_btn = ttk.Button(header, style="Ghost.TButton", command=self.toggle_lang)
        self.lang_btn.grid(row=0, column=1, sticky="e")
        row += 1

        ttk.Separator(card, style="Sep.TSeparator").grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 16))
        row += 1

        # --- URL ---
        self.url_label = ttk.Label(card, style="Section.TLabel")
        self.url_label.grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1
        self.url = ttk.Entry(card, font=(FONT_FAMILY, 10))
        self.url.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(4, 16), ipady=3)
        row += 1

        # --- Ruta de descarga ---
        self.path_label = ttk.Label(card, style="Section.TLabel")
        self.path_label.grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1
        self.path = ttk.Entry(card, font=(FONT_FAMILY, 10))
        self.path.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 0), ipady=3)
        self.path.insert(0, self.config.get('path', ''))
        self.browse_btn = ttk.Button(card, style="Icon.TButton", command=self.browse)
        self.browse_btn.grid(row=row, column=2, sticky="e", padx=(8, 0), pady=(4, 0))
        row += 1
        self.save_btn = ttk.Button(card, style="Ghost.TButton", command=self.save_path)
        self.save_btn.grid(row=row, column=2, sticky="e", pady=(8, 16))
        row += 1

        ttk.Separator(card, style="Sep.TSeparator").grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 16))
        row += 1

        # --- Formato ---
        self.format_label = ttk.Label(card, style="Section.TLabel")
        self.format_label.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 6))
        row += 1

        self.format = tk.StringVar(value="video")
        fmt_frame = ttk.Frame(card, style="Card.TFrame")
        fmt_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 12))
        self.radio_video = ttk.Radiobutton(fmt_frame, variable=self.format, value="video", command=self.on_format_change)
        self.radio_audio = ttk.Radiobutton(fmt_frame, variable=self.format, value="audio", command=self.on_format_change)
        self.radio_video.grid(row=0, column=0, sticky="w", padx=(0, 24))
        self.radio_audio.grid(row=0, column=1, sticky="w")
        row += 1

        # --- Calidad / Bitrate + botón fetch ---
        opts_frame = ttk.Frame(card, style="Card.TFrame")
        opts_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 16))
        opts_frame.grid_columnconfigure(0, weight=1)

        self.quality_label = ttk.Label(opts_frame, style="Field.TLabel")
        self.quality_label.grid(row=0, column=0, sticky="w")
        self.quality = ttk.Combobox(opts_frame, state="readonly", font=(FONT_FAMILY, 10))
        self.quality.grid(row=1, column=0, sticky="ew", pady=(4, 0), ipady=2)

        self.bitrate_label = ttk.Label(opts_frame, style="Field.TLabel")
        self.bitrate_label.grid(row=0, column=0, sticky="w")
        self.bitrate = ttk.Combobox(opts_frame, state="readonly", width=8, font=(FONT_FAMILY, 10),
                                     values=["128", "192", "256", "320"])
        self.bitrate.current(1)  # 192 por defecto
        self.bitrate.grid(row=1, column=0, sticky="w", pady=(4, 0), ipady=2)
        self.bitrate_label.grid_remove()
        self.bitrate.grid_remove()

        self.fetch_btn = ttk.Button(opts_frame, style="Ghost.TButton", command=self.fetch)
        self.fetch_btn.grid(row=1, column=1, sticky="e", padx=(10, 0))
        row += 1

        ttk.Separator(card, style="Sep.TSeparator").grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 16))
        row += 1

        # --- Progreso ---
        prog_header = ttk.Frame(card, style="Card.TFrame")
        prog_header.grid(row=row, column=0, columnspan=3, sticky="ew")
        prog_header.grid_columnconfigure(0, weight=1)
        self.status = ttk.Label(prog_header, style="Status.TLabel")
        self.status.grid(row=0, column=0, sticky="w")
        self.percent_label = ttk.Label(prog_header, style="Percent.TLabel", text="")
        self.percent_label.grid(row=0, column=1, sticky="e")
        row += 1

        self.progress = ttk.Progressbar(card, mode='determinate')
        self.progress.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(8, 20))
        row += 1

        # --- Botón de descarga ---
        self.download_btn = ttk.Button(card, style="Accent.TButton", command=self.confirm)
        self.download_btn.grid(row=row, column=0, columnspan=3, sticky="ew")

        # Ajusta la ventana al tamaño real que necesita el contenido (con margen)
        # en vez de un alto fijo que podía cortar el botón de descarga.
        self.root.update_idletasks()
        width = 660
        height = self.root.winfo_reqheight() + 20
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(width, height)

    def on_format_change(self):
        if self.format.get() == "audio":
            self.quality_label.grid_remove()
            self.quality.grid_remove()
            self.bitrate_label.grid()
            self.bitrate.grid()
        else:
            self.bitrate_label.grid_remove()
            self.bitrate.grid_remove()
            self.quality_label.grid()
            self.quality.grid()

    def update_texts(self):
        self.root.title(self.t('title'))
        self.title_label.config(text="🎬  " + self.t('title'))
        self.url_label.config(text="🔗  " + self.t('url'))
        self.path_label.config(text="📁  " + self.t('path'))
        self.format_label.config(text="⚙  " + self.t('format'))
        self.radio_video.config(text="🎥  " + self.t('video'))
        self.radio_audio.config(text="🎧  " + self.t('audio'))
        self.quality_label.config(text=self.t('quality'))
        self.bitrate_label.config(text=self.t('bitrate'))
        self.download_btn.config(text="⬇  " + self.t('download'))
        self.browse_btn.config(text="📂")
        self.save_btn.config(text="💾  " + self.t('save'))
        self.fetch_btn.config(text="🔍  " + self.t('fetch'))
        self.lang_btn.config(text="🌐  " + self.t('lang'))
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

    def _validate_inputs(self):
        if not self.url.get().strip():
            messagebox.showerror(self.t('error'), self.t('err_no_url'))
            return False
        path = self.path.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showerror(self.t('error'), self.t('err_no_path'))
            return False
        return True

    def _set_busy(self, busy):
        """Bloquea fetch/download simultáneos entre sí."""
        state = 'disabled' if busy else 'normal'
        self.fetch_btn.config(state=state)
        self.download_btn.config(state=state if not self.is_downloading else self.download_btn['state'])

    # ✅ fetch en hilo secundario para no congelar la UI
    def fetch(self):
        if self.is_downloading or self.is_fetching:
            return
        if not self.url.get().strip():
            messagebox.showerror(self.t('error'), self.t('err_no_url'))
            return
        self.is_fetching = True
        self.fetch_btn.config(state='disabled')
        self.download_btn.config(state='disabled')
        self.status.config(text=self.t('status_fetching'))
        threading.Thread(target=self._fetch_thread, daemon=True).start()

    def _fetch_thread(self):
        try:
            result = subprocess.run(
                [YTDLP_PATH, "-F", self.url.get()],
                capture_output=True, text=True, timeout=60,
                creationflags=CREATE_NO_WINDOW
            )
            qualities = set()
            # Formato típico de línea: "137  mp4  1920x1080  1080p ..."
            for line in result.stdout.splitlines():
                m = re.search(r'\b(\d{3,4})p\b', line)
                if m:
                    qualities.add(f"{m.group(1)}p")
            sorted_q = sorted(qualities, key=lambda x: int(x[:-1]), reverse=True)

            def on_done():
                self.quality['values'] = ['Best'] + sorted_q
                self.quality.current(0)
                self.is_fetching = False
                self.fetch_btn.config(state='normal')
                self.download_btn.config(state='normal')
                self.status.config(text=self.t('status_wait'))
                if sorted_q:
                    messagebox.showinfo(self.t('res_fetched'), self.t('res_fetched'))
                else:
                    messagebox.showwarning(self.t('error'), self.t('res_fetched'))
            self.ui(on_done)
        except Exception as e:
            logging.error(f"Error en fetch: {e}")
            err = str(e)

            def on_error():
                messagebox.showerror(self.t('error'), err)
                self.is_fetching = False
                self.fetch_btn.config(state='normal')
                self.download_btn.config(state='normal')
                self.status.config(text=self.t('status_wait'))
            self.ui(on_error)

    def confirm(self):
        if self.is_downloading or self.is_fetching:
            return
        if not self._validate_inputs():
            return
        if self.format.get() != "audio" and not ffmpeg_available():
            # Vídeo+audio necesita ffmpeg para el merge; avisamos pero dejamos continuar
            if not messagebox.askyesno(self.t('error'), self.t('err_no_ffmpeg') + "\n\n" + self.t('confirm')):
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
        self.percent_label.config(text="", foreground=COLORS["text"])
        self.download_btn.config(state='disabled', text="⬇  " + self.t('downloading'))
        self.fetch_btn.config(state='disabled')

    def unlock(self, success=True):
        self.is_downloading = False
        self.current_process = None
        self.download_btn.config(state='normal', text="⬇  " + self.t('download'))
        self.fetch_btn.config(state='normal')
        self.progress.stop()
        self.progress['mode'] = 'determinate'
        if success:
            self.progress['value'] = 100
            self.percent_label.config(text="100%", foreground=COLORS["success"])
            self.status.config(text="✅  " + self.t('status_done'))
        else:
            self.percent_label.config(text="", foreground=COLORS["danger"])
            self.status.config(text="⚠  " + self.t('error'))

    def download(self):
        process = None
        try:
            cmd = [
                YTDLP_PATH,
                self.url.get(),
                "-o", os.path.join(self.path.get(), "%(title)s.%(ext)s"),
                "--newline"  # output línea a línea para leer progreso
            ]

            if self.format.get() == "audio":
                cmd += ["-x", "--audio-format", "mp3", "--audio-quality", f"{self.bitrate.get()}K"]
            else:
                q = self.quality.get()
                if q not in ("", "Best"):
                    cmd += ["-f", f"bestvideo[height<={q[:-1]}]+bestaudio/best"]
                else:
                    cmd += ["-f", "bestvideo+bestaudio/best"]

            self.ui(lambda: self.status.config(text=self.t('status_down')))

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                creationflags=CREATE_NO_WINDOW
            )
            self.current_process = process

            percent_re = re.compile(r'(\d+(?:\.\d+)?)%')
            eta_re = re.compile(r'ETA\s+(\S+)')

            for line in process.stdout:
                line = line.strip()
                if '[download]' in line and '%' in line:
                    m = percent_re.search(line)
                    if m:
                        percent = float(m.group(1))
                        if percent != self.last_progress:
                            self.last_progress = percent
                            self.ui(lambda p=percent: (
                                self.progress.stop(),
                                self.progress.config(mode='determinate', value=p),
                                self.percent_label.config(text=f"{p:.0f}%")
                            ))
                        m_eta = eta_re.search(line)
                        if m_eta:
                            eta = m_eta.group(1)
                            self.ui(lambda e=eta: self.status.config(
                                text=f"{self.t('status_down')} - ETA {e}"
                            ))
                elif 'Merging' in line or 'ffmpeg' in line.lower() or 'Extracting audio' in line:
                    self.ui(lambda: self.status.config(text=self.t('status_processing')))

            process.wait()

            if process.returncode != 0:
                self.ui(lambda: (
                    messagebox.showerror(self.t('error'), f"yt-dlp exited with code {process.returncode}"),
                    self.unlock(success=False)
                ))
            else:
                self.ui(self.unlock)

        except Exception as e:
            logging.error(f"Error en download: {e}")
            err = str(e)
            self.ui(lambda: (messagebox.showerror(self.t('error'), err), self.unlock(success=False)))
        finally:
            if process is not None and process.poll() is None:
                try:
                    process.terminate()
                except Exception:
                    pass

    def on_close(self):
        if self.is_downloading and self.current_process is not None:
            if not messagebox.askyesno(self.t('error'), self.t('confirm')):
                return
            try:
                self.current_process.terminate()
            except Exception:
                pass
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
