import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import yt_dlp # type: ignore
import threading
import json
import os
import subprocess

APPDATA_DIR = os.path.join(os.getenv('APPDATA'), 'ElAlehYt_Down')
os.makedirs(APPDATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(APPDATA_DIR, 'config.json')

translations = {
    "es": {
        "title": "Descargador de Videos",
        "url_label": "URL del Video:",
        "path_label": "Ruta de Descarga:",
        "browse_button": "Seleccionar Carpeta",
        "save_path_button": "Guardar Ruta Predeterminada",
        "fetch_button": "Obtener Video",
        "format_label": "Formato:",
        "format_video": "Video con Audio",
        "format_audio": "Solo Audio",
        "quality_label": "Calidad:",
        "metadata_check": "Incluir Metadatos",
        "progress_label": "Progreso de Descarga:",
        "speed_label": "Velocidad de Descarga: N/A",
        "eta_label": "Tiempo Restante: N/A",
        "status_waiting": "Estado: Esperando",
        "status_fetching": "Estado: Obteniendo resoluciones...",
        "status_fetched": "Estado: Resoluciones obtenidas",
        "status_downloading": "Estado: Descargando...",
        "status_processing": "Estado: Procesando...",
        "status_merging": "Estado: Combinando video y audio...",
        "status_complete": "Estado: Proceso completado",
        "status_error_fetching": "Estado: Error al obtener resoluciones",
        "status_error_downloading": "Estado: Error en la descarga",
        "status_error_processing": "Estado: Error en el proceso",
        "status_error_merging": "Estado: Error al combinar video y audio",
        "download_button": "Descargar",
        "language_button": "Change To English",
        "resolutions_fetched": "Las resoluciones disponibles han sido cargadas.",
        "download_confirm_title": "Confirmar Descarga",
        "download_confirm": "El archivo ocupará aproximadamente {}. ¿Deseas continuar con la descarga?",
        "download_confirm_no_size_title": "Confirmar Descarga",
        "download_confirm_no_size": "El tamaño del archivo no está disponible. ¿Deseas continuar con la descarga?",
        "download_complete": "El archivo se ha descargado correctamente.\n\nHaz click en Aceptar para continuar.",
        "download_complete_merged": "El archivo '{}' se ha descargado y combinado correctamente.\n\nHaz click en Aceptar para continuar.",
        "error": "Error",
        "error_fetching": "Hubo un problema al obtener las resoluciones: {}",
        "error_downloading": "Hubo un problema al descargar el archivo: {}",
        "error_merging": "FFmpeg falló al combinar el video y el audio.\n\nDetails: {}\n\nFFmpeg Output:\n{}",
        "path_saved": "La ruta predeterminada se ha guardado correctamente."
    },
    "en": {
        "title": "Video Downloader",
        "url_label": "Video URL:",
        "path_label": "Download Path:",
        "browse_button": "Browse Folder",
        "save_path_button": "Save Default Path",
        "fetch_button": "Fetch Video",
        "format_label": "Format:",
        "format_video": "Video with Audio",
        "format_audio": "Audio Only",
        "quality_label": "Quality:",
        "metadata_check": "Include Metadata",
        "progress_label": "Download Progress:",
        "speed_label": "Download Speed: N/A",
        "eta_label": "Time Remaining: N/A",
        "status_waiting": "Status: Waiting",
        "status_fetching": "Status: Fetching resolutions...",
        "status_fetched": "Status: Resolutions fetched",
        "status_downloading": "Status: Downloading...",
        "status_processing": "Status: Processing...",
        "status_merging": "Status: Merging video and audio...",
        "status_complete": "Status: Process complete",
        "status_error_fetching": "Status: Error fetching resolutions",
        "status_error_downloading": "Status: Download error",
        "status_error_processing": "Status: Processing error",
        "status_error_merging": "Status: Error merging video and audio",
        "download_button": "Download",
        "language_button": "Cambiar a Español",
        "resolutions_fetched": "Available resolutions have been loaded.",
        "download_confirm_title": "Confirm Download",
        "download_confirm": "The file will approximately take {}. Do you want to continue with the download?",
        "download_confirm_no_size_title": "Confirm Download",
        "download_confirm_no_size": "The file size is not available. Do you want to continue with the download?",
        "download_complete": "The file has been downloaded successfully.\n\nClick OK to continue.",
        "download_complete_merged": "The file '{}' has been downloaded and merged successfully.\n\nClick OK to continue.",
        "error": "Error",
        "error_fetching": "There was a problem fetching the resolutions: {}",
        "error_downloading": "There was a problem downloading the file: {}",
        "error_merging": "FFmpeg failed to merge the video and audio.\n\nDetails: {}\n\nFFmpeg Output:\n{}",
        "path_saved": "The default path has been saved successfully."
    }
}

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.load_config()
        self.setup_ui()
        self.update_texts()

    def setup_ui(self):
        self.root.configure(bg='#f0f4c3')

        self.style = ttk.Style()
        self.style.configure('TButton',
                             background='#8bc34a',
                             foreground='black',
                             padding=8,
                             font=('Segoe UI', 9, 'bold'),
                             borderwidth=0,
                             relief='flat')

        self.style.map('TButton',
                       background=[('active', '#689f38')])

        self.style.configure('TLabel',
                             background='#f0f4c3',
                             foreground='#333333',
                             font=('Segoe UI', 9))

        self.style.configure('TCheckbutton',
                             background='#f0f4c3',
                             foreground='#333333',
                             font=('Segoe UI', 9))

        self.style.configure('TRadiobutton',
                             background='#f0f4c3',
                             foreground='#333333',
                             font=('Segoe UI', 9))

        self.style.configure('TCombobox',
                             background='#f0f4c3',
                             foreground='#333333',
                             font=('Segoe UI', 9))

        self.style.configure('Horizontal.TProgressbar',
                             background='#8bc34a',
                             troughcolor='#dcedc8',
                             borderwidth=0)

        self.url_label = ttk.Label(self.root)
        self.url_label.pack(pady=5)

        self.url_entry = tk.Entry(self.root, width=50, font=('Segoe UI', 9))
        self.url_entry.pack(pady=5)

        self.path_label = ttk.Label(self.root)
        self.path_label.pack(pady=5)

        self.path_entry = tk.Entry(self.root, width=50, font=('Segoe UI', 9))
        self.path_entry.pack(pady=5)
        self.path_entry.insert(0, self.config.get("download_path", ""))

        self.browse_button = ttk.Button(self.root, command=self.browse_folder)
        self.browse_button.pack(pady=5)

        self.save_path_button = ttk.Button(self.root, command=self.save_path)
        self.save_path_button.pack(pady=5)

        self.fetch_button = ttk.Button(self.root, command=self.fetch_resolutions)
        self.fetch_button.pack(pady=5)

        self.format_label = ttk.Label(self.root)
        self.format_label.pack(pady=5)

        self.format_var = tk.StringVar(value="video")
        self.format_video = ttk.Radiobutton(self.root, variable=self.format_var, value="video")
        self.format_audio = ttk.Radiobutton(self.root, variable=self.format_var, value="audio")
        self.format_video.pack(pady=5)
        self.format_audio.pack(pady=5)

        self.quality_label = ttk.Label(self.root)
        self.quality_label.pack(pady=5)

        self.quality_combo = ttk.Combobox(self.root, values=[], style='TCombobox')
        self.quality_combo.pack(pady=5)

        self.metadata_var = tk.BooleanVar()
        self.metadata_check = ttk.Checkbutton(self.root, variable=self.metadata_var)
        self.metadata_check.pack(pady=5)

        self.progress_label = ttk.Label(self.root)
        self.progress_label.pack(pady=5)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate",
                                         style='Horizontal.TProgressbar')
        self.progress.pack(pady=5)

        self.speed_label = ttk.Label(self.root)
        self.speed_label.pack(pady=5)

        self.eta_label = ttk.Label(self.root)
        self.eta_label.pack(pady=5)

        self.status_label = ttk.Label(self.root,
                                       font=('Arial', 14, 'bold'))
        self.status_label.pack(pady=10)

        self.download_button = ttk.Button(self.root, command=self.confirm_download)
        self.download_button.pack(pady=20)

        self.language_button = ttk.Button(self.root, command=self.toggle_language)
        self.language_button.pack(pady=5)

    def update_texts(self):
        t = translations[self.current_language]
        self.root.title(t["title"])
        self.url_label.config(text=t["url_label"])
        self.path_label.config(text=t["path_label"])
        self.browse_button.config(text=t["browse_button"])
        self.save_path_button.config(text=t["save_path_button"])
        self.fetch_button.config(text=t["fetch_button"])
        self.format_label.config(text=t["format_label"])
        self.format_video.config(text=t["format_video"])
        self.format_audio.config(text=t["format_audio"])
        self.quality_label.config(text=t["quality_label"])
        self.metadata_check.config(text=t["metadata_check"])
        self.progress_label.config(text=t["progress_label"])
        self.speed_label.config(text=t["speed_label"])
        self.eta_label.config(text=t["eta_label"])
        self.status_label.config(text=t["status_waiting"], foreground='blue')
        self.download_button.config(text=t["download_button"])
        self.language_button.config(text=t["language_button"])

    def toggle_language(self):
        self.current_language = "en" if self.current_language == "es" else "es"
        self.config["language"] = self.current_language
        self.save_config()
        self.update_texts()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
            self.current_language = self.config.get("language", "es")
        else:
            self.config = {}
            self.current_language = "es"

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, folder_selected)

    def save_path(self):
        self.config["download_path"] = self.path_entry.get()
        self.save_config()
        messagebox.showinfo(translations[self.current_language]["path_saved"], translations[self.current_language]["path_saved"])

    def fetch_resolutions(self):
        url = self.url_entry.get()
        self.status_label.config(text=translations[self.current_language]["status_fetching"], foreground='orange')
        self.root.update_idletasks()

        ydl_opts = {'quiet': True, 'no_warnings': True}

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                formats = info_dict.get('formats', [])
                resolutions = set()

                self.total_bytes = info_dict.get('filesize_approx', 0)

                for f in formats:
                    if 'height' in f and f['vcodec'] != 'none':
                        resolutions.add(f"{f['height']}p")

                resolutions = sorted(resolutions, key=lambda x: int(x[:-1]), reverse=True)
                self.quality_combo['values'] = ["Mejor"] + resolutions
                self.quality_combo.current(0)
                messagebox.showinfo(translations[self.current_language]["resolutions_fetched"], translations[self.current_language]["resolutions_fetched"])
                self.status_label.config(text=translations[self.current_language]["status_fetched"], foreground='green')
        except Exception as e:
            messagebox.showerror(translations[self.current_language]["error"], translations[self.current_language]["error_fetching"].format(e))
            self.status_label.config(text=translations[self.current_language]["status_error_fetching"], foreground='red')

    def confirm_download(self):
        t = translations[self.current_language]
        if self.total_bytes == 0:
            answer = messagebox.askyesno(t["download_confirm_no_size_title"], t["download_confirm_no_size"])
        else:
            file_size = self.format_size(self.total_bytes)
            answer = messagebox.askyesno(t["download_confirm_title"], t["download_confirm"].format(file_size))
        if answer:
            self.download_video()

    def progress_hook(self, d):
        t = translations[self.current_language]
        if d['status'] == 'downloading':
            total = d.get('total_bytes', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            if total > 0:
                percent = int(downloaded / total * 100)
                self.progress['value'] = percent

            self.speed_label.config(text=f"{t['speed_label'].split(':')[0]}: {self.format_speed(speed)}")
            self.eta_label.config(text=f"{t['eta_label'].split(':')[0]}: {self.format_eta(eta)}")
            self.status_label.config(text=t["status_downloading"], foreground='blue')

            self.root.update_idletasks()
        elif d['status'] == 'finished':
            self.progress['value'] = 100
            self.speed_label.config(text=t["speed_label"])
            self.eta_label.config(text=t["eta_label"])
            self.status_label.config(text=t["status_processing"], foreground='purple')
            self.root.update_idletasks()

    def format_speed(self, speed):
        if speed is None:
            return "N/A"
        elif speed < 1024:
            return f"{speed:.2f} B/s"
        elif speed < 1024 ** 2:
            return f"{speed / 1024:.2f} KB/s"
        else:
            return f"{speed / 1024 ** 2:.2f} MB/s"

    def format_eta(self, eta):
        if eta is None:
            return "N/A"
        mins, secs = divmod(eta, 60)
        return f"{int(mins)} min {int(secs)} sec"

    def format_size(self, size):
        if size is None:
            return "N/A"
        elif size < 1024:
            return f"{size:.2f} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 ** 3:
            return f"{size / 1024 ** 2:.2f} MB"
        else:
            return f"{size / 1024 ** 3:.2f} GB"

    def download_video(self):
        url = self.url_entry.get()
        download_path = self.path_entry.get()
        format_option = self.format_var.get()
        quality = self.quality_combo.get()
        include_metadata = self.metadata_var.get()

        if format_option == "audio":
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
            }
            threading.Thread(target=self._download, args=(url, ydl_opts)).start()
        else:
            video_opts = {
                'format': 'bestvideo[height<={}]/best'.format(quality[:-1]) if quality != "Mejor" else 'bestvideo/best',
                'progress_hooks': [self.progress_hook],
            }
            audio_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [self.progress_hook],
            }
            threading.Thread(target=self._download_and_merge, args=(url, video_opts, audio_opts, download_path)).start()

    def _download(self, url, ydl_opts):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            t = translations[self.current_language]
            self.status_label.config(text=t["status_complete"], foreground='green')
            messagebox.showinfo(t["download_complete"], t["download_complete"])
        except Exception as e:
            self.status_label.config(text=t["status_error_downloading"], foreground='red')
            messagebox.showerror(t["error"], t["error_downloading"].format(e))

    def _download_and_merge(self, url, video_opts, audio_opts, download_path):
        try:
            with yt_dlp.YoutubeDL(video_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', 'video')

            video_title = "".join([c for c in video_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            video_title = video_title.replace(" ", "_")

            video_filename = os.path.join(download_path, 'tempvideo')
            video_opts['outtmpl'] = video_filename + '.%(ext)s'
            with yt_dlp.YoutubeDL(video_opts) as ydl:
                ydl.download([url])
                video_info = ydl.extract_info(url, download=False)
                video_extension = video_info['ext']
                video_path = video_filename + '.' + video_extension

            audio_filename = os.path.join(download_path, 'tempaudio')
            audio_opts['outtmpl'] = audio_filename + '.%(ext)s'
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.download([url])
                audio_path = audio_filename + '.mp3'

            if not os.path.exists(video_path) or not os.path.exists(audio_path):
                raise Exception(translations[self.current_language]["error_merging"])

            output_path = os.path.join(download_path, f"{video_title}.mp4")

            t = translations[self.current_language]
            self.status_label.config(text=t["status_merging"], foreground='purple')
            self.root.update_idletasks()

            try:
                command = [
                    "ffmpeg",
                    "-i", video_path,
                    "-i", audio_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-strict", "experimental",
                    "-shortest",
                    "-y",
                    output_path
                ]

                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    raise Exception(f"FFmpeg failed with code {process.returncode}\nStdout: {stdout.decode()}\nStderr: {stderr.decode()}")

            except Exception as e:
                messagebox.showerror(t["error"], t["error_merging"].format(e, stderr.decode()))
                self.status_label.config(text=t["status_error_merging"], foreground='red')
                return

            os.remove(video_path)
            os.remove(audio_path)

            self.status_label.config(text=t["status_complete"], foreground='green')
            self.root.update_idletasks()
            messagebox.showinfo(t["download_complete"], t["download_complete_merged"].format(video_title))

        except Exception as e:
            messagebox.showerror(t["error"], t["error_downloading"].format(e))
            self.status_label.config(text=t["status_error_processing"], foreground='red')
            self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()
