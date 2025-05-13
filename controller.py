#!/usr/bin/env python3
import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
from PIL import Image, ImageTk  # Nécessite Pillow : pip install pillow

# Mapping des noms courts vers les scripts Python
PROGRAMS = {
    "Note": "note.py",
    "Correction llm": "correction_1.py",
    "Correction sans llm": "correction_2.py",
    "Réécriture": "rewriting.py",
    "horaires": "horaires.py",
    "Classification": "classification.py",
    "Détection de mots suspects": "flags.py",
    "tel-mail": "tel-mail.py",
}

# Descriptions des programmes
PROGRAM_DESCRIPTIONS = {
    "Note": "Attribue une note au texte vis-à-vis de sa simplicité",
    "Correction llm": "Correction d'erreurs de frappe/grammaire",
    "Correction sans llm": "Correction automatique sans IA",
    "Réécriture": "Réécriture automatique du des descriptions en language simple",
    "Détection de mots suspects": "Détection de termes problématiques",
    "horaires": "Extraction des horaires, numéros et emails",
    "Classification": "Détecte les services attribués dans les mauvaises catégories",
}

# Chemin vers flags.py pour la configuration
FLAGS_PY = os.path.join(os.path.dirname(__file__), 'flags.py')

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.showtip)
        self.widget.bind("<Leave>", self.hidetip)

    def showtip(self, event=None):
        "Display text in tooltip window"
        if self.tipwindow or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class ControllerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sélecteur de programmes")
        self.geometry("700x450")

        # --- Champ 'Nombre de lignes' ---
        frame_rows = ttk.Frame(self)
        frame_rows.pack(fill=tk.X, padx=10, pady=(10,0))
        ttk.Label(frame_rows, text="Nombre de lignes à analyser (vide = toutes) :")\
            .pack(side=tk.LEFT)
        self.rows_var = tk.StringVar()
        ttk.Entry(frame_rows, textvariable=self.rows_var, width=10)\
            .pack(side=tk.LEFT, padx=(5,0))

        # --- Cases à cocher programmes ---
        self.frame_chk = ttk.LabelFrame(self, text="Programmes disponibles")
        self.frame_chk.pack(fill=tk.X, padx=10, pady=(10,0))
        self.vars = {}
        for name in PROGRAMS:
            if name == "horaires":  # on ne l'affiche pas directement
                continue
            self._add_program_checkbox(name)

        # --- Boutons ---
        frame_btn = ttk.Frame(self)
        frame_btn.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(frame_btn, text="Exécuter sélection", command=self.run_selected)\
            .pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(frame_btn, text="Tout sélectionner", command=self.select_all)\
            .pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(frame_btn, text="Tout désélectionner", command=self.select_none)\
            .pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(frame_btn, text="⚙️", command=self.configure_flags)\
            .pack(side=tk.RIGHT)
        
        # Info-bulle pour le bouton Configurer Flags
        ToolTip(frame_btn.children['!button4'], 
               "Configurer la liste des mots suspects à extraire")

        # --- Zone de log ---
        self.log = scrolledtext.ScrolledText(self, state='disabled', height=15)
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        
                # --- Bouton info avec icône ---
        try:
            info_img = Image.open("fichiers_csv/info.jpg")  # ou renomme en "info.png"
            info_img = info_img.resize((20, 20), Image.LANCZOS)

            self.info_icon = ImageTk.PhotoImage(info_img)
            info_btn = ttk.Button(self, image=self.info_icon, command=self.show_info)
            info_btn.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)

            ToolTip(info_btn, "Informations détaillées sur les programmes")
        except Exception as e:
            print(f"Erreur chargement image info : {e}")




        # Flag pour ajouter horaires.py après flags.py
        self.run_horaires = False

    def _add_program_checkbox(self, name):
        var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(self.frame_chk, text=name, variable=var)
        chk.pack(side=tk.LEFT, padx=5, pady=5)
        self.vars[name] = var
        # Ajout de l'info-bulle
        ToolTip(chk, PROGRAM_DESCRIPTIONS.get(name, "Pas de description disponible"))

    def select_all(self):
        for v in self.vars.values():
            v.set(True)

    def select_none(self):
        for v in self.vars.values():
            v.set(False)

    def run_selected(self):
        # Lecture et validation du nombre de lignes
        rows_txt = self.rows_var.get().strip()
        if rows_txt:
            try:
                rows = int(rows_txt)
                if rows < 1:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Valeur invalide",
                                     "Le nombre de lignes doit être un entier positif.",
                                     parent=self)
                return
        else:
            rows = None

        selected = [n for n,v in self.vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Aucun programme",
                                   "Veuillez sélectionner au moins un programme.",
                                   parent=self)
            return

        # Si demandé, enchaîner horaires après flags
        if self.run_horaires and "Détection de mots suspects" in selected:
            for addon in ("horaires", "tel-mail"):
                if addon not in selected:
                    selected.append(addon)

        # Lancement en threads
        self.set_widget_state(self, 'disabled')
        for name in selected:
            threading.Thread(
                target=self.run_script,
                args=(name, rows),
                daemon=True
            ).start()

    def run_script(self, name, rows):
        script = PROGRAMS[name]
        cmd = [sys.executable, script]
        if rows is not None:
            cmd.append(str(rows))
        self.log_message(f"\n▶ Démarrage de '{name}' : {' '.join(cmd)}")
        env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', env=env, bufsize=1
        )
        for line in proc.stdout:
            self.log_message(f"[{name}] {line.rstrip()}")
        proc.wait()
        self.log_message(f"✔ Fin de '{name}' (code {proc.returncode})")

        # Réactivation de l'UI quand tous les threads sont terminés
        if not any(t.is_alive() for t in threading.enumerate()
                   if t is not threading.main_thread()):
            self.set_widget_state(self, 'normal')

    def configure_flags(self):
        win = tk.Toplevel(self)
        win.title("Configurer Flags & Horaires")
        win.geometry("400x220")
        win.transient(self)

        # Lecture flags.py
        try:
            with open(FLAGS_PY, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire {FLAGS_PY} :\n{e}",
                                 parent=win)
            return

        m = re.search(r'FLAGS\s*=\s*\[(.*?)\]', content, re.S)
        current = []
        if m:
            current = [w.strip().strip('"') for w in m.group(1).split(',') if w.strip()]

        ttk.Label(win, text="Mots à flag (séparés par des virgules):")\
            .pack(anchor='w', padx=10, pady=(10,0))
        txt = tk.Text(win, width=50, height=4)
        txt.pack(fill='x', padx=10, pady=(0,10))
        txt.insert('1.0', ", ".join(current))

        var = tk.BooleanVar(value=self.run_horaires)
        chk = ttk.Checkbutton(win,
            text="Horaires - Téléphone - Adresses-emails",
            variable=var
        )
        chk.pack(anchor='w', padx=10, pady=(0,10))
        ToolTip(chk, "Activer l'extraction automatique des horaires, numéros de téléphone et adresses email")

        frm = ttk.Frame(win)
        frm.pack(fill='x', pady=10)
        def on_ok():
            # Mise à jour de flags.py
            new_list = [w.strip() for w in txt.get('1.0','end').split(',') if w.strip()]
            repl = 'FLAGS = [\n' + ',\n'.join(f'    "{w}"' for w in new_list) + '\n]'
            new_content = re.sub(r'FLAGS\s*=\s*\[.*?\]', repl, content, flags=re.S)
            try:
                with open(FLAGS_PY, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            except Exception as e:
                messagebox.showerror("Erreur",
                                     f"Impossible d'écrire {FLAGS_PY} :\n{e}",
                                     parent=win)
                return

            # Enregistrer le choix pour lancer horaires après flags
            self.run_horaires = var.get()
            messagebox.showinfo("Succès", "Configuration mise à jour.", parent=win)
            win.destroy()

        ttk.Button(frm, text="Annuler", command=win.destroy)\
            .pack(side=tk.RIGHT, padx=5)
        ttk.Button(frm, text="OK", command=on_ok)\
            .pack(side=tk.RIGHT)

    def log_message(self, msg):
        self.log.configure(state='normal')
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.configure(state='disabled')

    def set_widget_state(self, widget, state):
        try:
            widget.configure(state=state)
        except (tk.TclError, AttributeError):
            pass
        for c in widget.winfo_children():
            self.set_widget_state(c, state)
            
    def show_info(self):
        win = tk.Toplevel(self)
        win.title("Informations sur les programmes")
        win.geometry("800x500")
        win.transient(self)

        txt = tk.Text(win, wrap='word', state='normal')
        txt.pack(fill='both', expand=True, padx=10, pady=10)

        # 🔽 Lecture du fichier de descriptions
        desc_path = os.path.join(os.path.dirname(__file__), "fichiers_csv/descriptions.txt")
        print("Chargement du fichier descriptions depuis :", desc_path)  # pour debug

        try:
            with open(desc_path, 'r', encoding='utf-8') as f:
                for line in f:
                    txt.insert(tk.END, line)

        except Exception as e:
            txt.insert(tk.END, f"[Erreur lecture fichier descriptions.txt] {e}\n\n")

        txt.configure(state='disabled')



if __name__ == '__main__':
    app = ControllerGUI()
    app.mainloop()