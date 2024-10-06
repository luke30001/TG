import os

# Set the environment variable to the current directory where your script and kaggle.json are located
os.environ['KAGGLE_CONFIG_DIR'] = os.path.dirname(os.path.abspath(__file__))
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import kaggle
import time
import shutil
import json
import urllib.request
import markdown2
from bs4 import BeautifulSoup
import webbrowser
import subprocess
from pathlib import Path
def add_table_borders(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')

    for table in tables:
        if 'style' in table.attrs:
            table['style'] += '; border: 1px solid black; border-collapse: collapse;'
        else:
            table['style'] = 'border: 1px solid black; border-collapse: collapse;'

        for cell in table.find_all(['td', 'th']):
            if 'style' in cell.attrs:
                cell['style'] += '; border: 1px solid black;'
            else:
                cell['style'] = 'border: 1px solid black;'

    return str(soup)

class KaggleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Carica file audio su Kaggle e avvia notebook")
        self.label = tk.Label(root, text="Seleziona quante parole deve contenere il riassunto:")
        self.label.pack(pady=10)
        self.nword = tk.IntVar(value=3000)
        self.frl = tk.StringVar(value="EN")
        self.tol = tk.StringVar(value="English")
        
        vcmd = (root.register(self.validate_n), '%P')
        
        # Spinbox with validation to prevent values > 40000
        self.spinbox = tk.Spinbox(
            root, textvariable=self.nword, from_=0, to=3000, increment=100, width=5, validate='key', validatecommand=vcmd
        )
        self.spinbox.pack(pady=10)
        self.label2 = tk.Label(root, text="From language")
        self.label2.pack(pady=10)
        self.fr = tk.Entry(root, width=40,textvariable=self.frl)
        self.fr.pack(pady=10)
        self.label3 = tk.Label(root, text="To language")
        self.label3.pack(pady=10)
        self.to = tk.Entry(root, width=40,textvariable=self.tol)
        self.to.pack(pady=10)

        self.upload_btn = tk.Button(root, text="Carica file audio e avvia notebook", command=self.upload_file)
        self.upload_btn.pack(pady=20)

        self.show_html_btn = tk.Button(root, text="Mostra nel browser", command=self.show_html_file, state=tk.DISABLED)
        self.show_html_btn.pack(pady=10)

        self.show_md_btn = tk.Button(root, text="Mostra nell'esplora file", command=self.show_md_file, state=tk.DISABLED)
        self.show_md_btn.pack(pady=10)

    def validate_n(self, value):
        # Allow only values that are digits and less than or equal to 4000
        if value == "":
            return True
        if value.isdigit() and int(value) <= 3000:
            return True
        else:
            return False

    def upload_file(self):
        print(self.tol.get(),self.frl.get())
        filepath = filedialog.askopenfilename(title="Seleziona un file audio", filetypes=(("Audio files", "*.wav *.mp3"), ("All files", "*.*")))
        if not filepath:
            return

        try:
            # Authentication
            kaggle.api.authenticate()

            # Determine the file extension and set the filename to audio.{format}
            file_extension = os.path.splitext(filepath)[-1].lower()
            self.fn = f"audio{file_extension}"

            # Save the file as audio.{format} in the script's folder
            shutil.copy(filepath, self.fn)

            self.create_dataset_metadata(self.fn)

            temp_dir = "temp_upload_dir"
            os.makedirs(temp_dir, exist_ok=True)

            # Copy the file and metadata to the temp directory
            shutil.copy(self.fn, temp_dir)
            shutil.copy('dataset-metadata.json', temp_dir)

            kaggle.api.dataset_create_version(
                folder=temp_dir,
                version_notes="Prima versione del dataset con file audio e metadati."
            )

            shutil.rmtree(temp_dir)
            # Start the Kaggle notebook
            self.start_kaggle_notebook(self.fn)
            self.show_results()

        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def create_dataset_metadata(self, filepath):
        filename = os.path.basename(filepath)
        metadata = {
            "title": "Dataset con File Audio",
            "id": "lucaromanello/audio-lezz",
            "licenses": [
                {
                    "name": "CC0-1.0",
                    "url": "https://creativecommons.org/publicdomain/zero/1.0/"
                }
            ],
            "description": "Questo dataset contiene un file audio MP3 o WAV.",
            "files": [
                {
                    "filename": filename,
                    "format": "MP3" if filename.lower().endswith(".mp3") else "WAV",
                }
            ],
            "tags": ["audio", "dataset"]
        }

        with open('dataset-metadata.json', 'w') as f:
            json.dump(metadata, f, indent=4)

    def start_kaggle_notebook(self, filepath):
        time.sleep(60)
        filename = os.path.basename(filepath)

        notebook_path = "summarizerainetor.ipynb"
        with open(notebook_path, "r") as file:
            notebook_content = file.read()
        toch=str(self.nword.get())
        if toch=="":
            toch="0"
        notebook_content = notebook_content.replace("INPUT_FILE", "/kaggle/input/audio-lezz/" + self.fn).replace("N_WORD",toch).replace("FROM_LAN",str(self.frl.get())).replace("TO_LAN",str(self.tol.get()))

        with open("ntb/summarizerainetor.ipynb", "w+") as file:
            file.write(notebook_content)

        kaggle.api.kernels_push("ntb")

    def show_results(self):
        tt=True
        while tt:
            try:
                time.sleep(60)
                jj=kaggle.api.kernel_output(user_name="lucaromanello", kernel_slug="summarizerainetor")
                for v in json.loads(jj["logNullable"]):
                    if("capybaararararararrarararrararrarararrar" in v["data"]):
                        tt=False
            except:
                pass
            
        jj = kaggle.api.kernel_output(user_name="lucaromanello", kernel_slug="summarizerainetor")["files"]
        for v in jj:
            if v["fileName"] == "out.txt":
                urllib.request.urlretrieve(v["url"], "out.txt")

        output_file_path = "out.txt"
        if os.path.exists(output_file_path):
            with open(output_file_path, "r") as file:
                output = file.read()

            # Convert Markdown to HTML
            mrk = markdown2.Markdown(extras=["tables"])
            html_output = '<meta charset="UTF-8">' + add_table_borders(mrk.convert(output))
            os.makedirs("output", exist_ok=True)
            # Save Markdown and HTML output
            self.markdown_file_path = "output/output.md"
            self.html_file_path = "output.html"
            with open(self.markdown_file_path, "w") as md_file:
                md_file.write(output)
            with open(self.html_file_path, "w") as html_file:
                html_file.write(html_output)

            # Enable the buttons to show the files
            self.show_html_btn.config(state=tk.NORMAL)
            self.show_md_btn.config(state=tk.NORMAL)

        else:
            messagebox.showwarning("Warning", "Non è stato trovato un file di output da visualizzare.")

    def show_html_file(self):
        if hasattr(self, 'html_file_path'):
            webbrowser.open(f"file://{os.path.realpath(self.html_file_path)}")

    def show_md_file(self):
        if hasattr(self, 'markdown_file_path'):
            subprocess.run(["open", Path(self.markdown_file_path).parent])

if __name__ == "__main__":
    root = tk.Tk()
    app = KaggleApp(root)
    root.mainloop()
