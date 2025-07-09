import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess

os.environ['IMAGEMAGICK_BINARY'] = r'C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe'
import threading
from video_merger import VideoMerger
from gui_elements import VideoConfigDialog, TemplateConfigDialog
import data_load  # Potrzebne do nowej funkcji


class VideoMergerGUI:
    def __init__(self, root, template_manager):
        self.root = root
        self.root.title("Video Merger with Floating Text")
        self.root.geometry("900x700")
        self.template_manager = template_manager
        self.merger = VideoMerger()
        self.pre_template_clips = []
        self.post_template_clips = []
        self.item_no_var = tk.StringVar()

        self.load_template()
        self.setup_ui()
        self.update_file_list()  # Zaktualizuj listę po załadowaniu szablonu

    def setup_ui(self):
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        template_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Template", menu=template_menu)
        template_menu.add_command(label="Edit Pre-Clips Template", command=self.edit_pre_clips_template)
        template_menu.add_command(label="Edit Post-Clips Template", command=self.edit_post_clips_template)

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        title_label = ttk.Label(main_frame, text="Video Merger", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # --- Ramka na indeks produktu z nowym przyciskiem ---
        index_frame = ttk.Frame(main_frame)
        index_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky="ew")
        index_frame.columnconfigure(1, weight=1)  # Pozwala polu Entry się rozszerzać

        ttk.Label(index_frame, text="Indeks produktu:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(index_frame, textvariable=self.item_no_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        # NOWY PRZYCISK
        ttk.Button(index_frame, text="Załaduj dane", command=self.reload_all_data).pack(side=tk.LEFT, padx=5)

        ttk.Button(index_frame, text="Odśwież dane", command=self.reload_excel).pack(side=tk.LEFT, padx=5)

        self.setup_video_list(main_frame)
        self.setup_control_buttons(main_frame)
        self.setup_output_settings(main_frame)

        self.setup_progress_area(main_frame)

    def reload_all_data(self):
        """
        Loads data for the given index and replaces placeholders in all clips
        (templates and user-added clips).
        """
        item_no = self.item_no_var.get().strip()
        if not item_no:
            messagebox.showerror("Brak Indeksu", "Proszę podać indeks produktu przed załadowaniem danych.",
                                 parent=self.root)
            return

        # Ostrzeżenie dla użytkownika o trwałej zmianie
        confirm = messagebox.askyesno(
            "Potwierdzenie",
            "Ta operacja podmieni wszystkie symbole (np. {OPIS}, {indeks}) na dane z nowego indeksu we wszystkich klipach, także w szablonach.\n\n"
            "Jeśli zapiszesz szablon po tej operacji, symbole zostaną trwale nadpisane. Czy chcesz kontynuować?",
            parent=self.root
        )
        if not confirm:
            return

        # 1. Wczytaj wszystkie dane dla danego indeksu
        try:
            names = data_load.load_names(item_no)
            description = data_load.load_description(item_no)
            materials = data_load.load_materials(item_no)

            # Słownik mapujący symbole na dane. Klucze muszą być wielkimi literami.
            data_map = {
                "{INDEKS}": item_no,
                "{NAZWA_PL}": names.get("PL", "Brak nazwy PL"),
                "{NAZWA_EN}": names.get("EN", "Brak nazwy EN"),
                "{OPIS}": description,
                "{MATERIALY}": materials
            }
        except Exception as e:
            messagebox.showerror("Błąd ładowania danych", f"Wystąpił błąd podczas komunikacji z plikiem Excel: {e}",
                                 parent=self.root)
            return

        # 2. Funkcja pomocnicza do aktualizacji tekstów w liście klipów
        def update_clip_texts(clips_list):
            for clip in clips_list:
                for text_info in clip.get('texts', []):
                    # Sprawdzanie symbolu jest niewrażliwe na wielkość liter
                    placeholder = text_info.get('text', '').strip().upper()
                    if placeholder in data_map:
                        # Zamień symbol na wczytaną wartość
                        text_info['text'] = data_map[placeholder]

        # 3. Zaktualizuj wszystkie listy klipów: szablony i listę roboczą
        update_clip_texts(self.pre_template_clips)
        update_clip_texts(self.post_template_clips)
        update_clip_texts(self.merger.clips_data)

        # 4. Odśwież widok i poinformuj o sukcesie
        self.update_file_list()

        # ** Zmiana nazwy pliku wyjściowego na podstawie indeksu **
        self.output_var.set(f"{item_no}.mp4")  # Zmieniamy nazwę pliku na przekazany indeks (item_no)

        messagebox.showinfo("Sukces", "Dane zostały pomyślnie zaktualizowane we wszystkich klipach.", parent=self.root)

    def setup_video_list(self, parent):
        list_label = ttk.Label(parent, text="Clip Order (User Clips):", font=('Arial', 12, 'bold'))
        list_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))

        columns = ('Order', 'File', 'Text Overlays')
        self.tree = ttk.Treeview(parent, columns=columns, show='headings', height=10)

        self.tree.heading('Order', text='#')
        self.tree.heading('File', text='File')
        self.tree.heading('Text Overlays', text='Text Overlays')

        self.tree.column('Order', width=50, anchor='center', stretch=tk.NO)
        self.tree.column('File', width=400)
        self.tree.column('Text Overlays', width=150, anchor='center')

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        scrollbar.grid(row=3, column=2, sticky=(tk.N, tk.S), pady=(0, 10))
        parent.rowconfigure(3, weight=1)

    def merge_files_thread(self, output_path, item_no, progress_callback):
        # Logika tworzenia pełnej listy klipów do scalenia
        user_clips_start_index = len(self.pre_template_clips)
        # Klipy użytkownika to te w merger.clips_data, które nie są pre_clips
        user_clips = self.merger.clips_data[user_clips_start_index:]

        # Tworzymy pełną listę na nowo z aktualnych danych
        full_clips = self.pre_template_clips + user_clips + self.post_template_clips

        temp_merger = VideoMerger()
        for clip in full_clips:
            temp_merger.add_clip(
                clip['path'],
                clip['texts'],
                clip.get('image_duration')
            )

        success, message = temp_merger.merge_videos(
            output_path,
            item_no,
            progress_callback
        )
        self.root.after(0, lambda: self.merge_complete(success, message))

    def start_merge_process(self):
        # Upewnij się, że w mergerze są klipy użytkownika, oprócz szablonów
        user_clips_count = len(self.merger.clips_data) - len(self.pre_template_clips)
        if not self.pre_template_clips and not self.post_template_clips and user_clips_count == 0:
            messagebox.showwarning("No Files", "Please add at least one video or image.")
            return
        if not self.output_var.get():
            messagebox.showwarning("No Output File", "Please specify an output file.")
            return

        self.progress_bar['value'] = 0
        self.progress_bar['mode'] = 'determinate'
        self.status_var.set("Processing...")

        item_no = self.item_no_var.get().strip()
        thread = threading.Thread(
            target=self.merge_files_thread,
            args=(self.output_var.get(), item_no, self.update_progress),
            daemon=True
        )
        thread.start()

    def load_template(self):
        success, result = self.template_manager.load_template()
        self.merger.clips_data.clear()
        self.pre_template_clips = []
        self.post_template_clips = []

        if success:
            self.pre_template_clips = result.get('pre_clips', [])
            self.post_template_clips = result.get('post_clips', [])
            # Dodaj pre-clips do głównej listy roboczej
            for clip in self.pre_template_clips:
                self.merger.add_clip(
                    clip['path'],
                    clip['texts'],
                    clip.get('image_duration')
                )
        else:
            print(result)

    def edit_pre_clips_template(self):
        dialog = TemplateConfigDialog(self.root, "Edit Pre-Clips Template", clips_data=self.pre_template_clips)
        self.root.wait_window(dialog.dialog)
        if dialog.result is not None:
            self.pre_template_clips = dialog.result
            if getattr(dialog, 'save_requested', True):  # domyślnie True
                self.update_template()

    def edit_post_clips_template(self):
        dialog = TemplateConfigDialog(self.root, "Edit Post-Clips Template", clips_data=self.post_template_clips)
        self.root.wait_window(dialog.dialog)
        if dialog.result is not None:
            self.post_template_clips = dialog.result
            if getattr(dialog, 'save_requested', True):
                self.update_template()

    def update_template(self):
        success, message = self.template_manager.save_template(self.pre_template_clips, self.post_template_clips)
        if success:
            messagebox.showinfo("Success", message)
            self.load_template()  # Przeładuj szablony do widoku
            self.update_file_list()
        else:
            messagebox.showerror("Error", message)

    def setup_control_buttons(self, parent):
        self.button_frame = ttk.Frame(parent)
        self.button_frame.grid(row=4, column=0, columnspan=3, pady=(0, 20))
        ttk.Button(self.button_frame, text="Add File", command=self.add_file_dialog).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(self.button_frame, text="Edit Selected", command=self.edit_file_dialog).grid(row=0, column=1,
                                                                                                padx=(0, 10))
        ttk.Button(self.button_frame, text="Remove Selected", command=self.remove_file).grid(row=0, column=2,
                                                                                             padx=(0, 10))
        ttk.Button(self.button_frame, text="Move Up", command=self.move_file_up).grid(row=0, column=3, padx=(0, 10))
        ttk.Button(self.button_frame, text="Move Down", command=self.move_file_down).grid(row=0, column=4, padx=(0, 10))
        ttk.Button(self.button_frame, text="Clear All", command=self.clear_all_files).grid(row=0, column=5)

    def setup_output_settings(self, parent):
        output_frame = ttk.LabelFrame(parent, text="Output Settings", padding="10")
        output_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        output_frame.columnconfigure(1, weight=1)
        ttk.Label(output_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.output_var = tk.StringVar(value=f"{self.item_no_var}.mp4")
        ttk.Entry(output_frame, textvariable=self.output_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(output_frame, text="Browse", command=self.browse_output_file).grid(row=0, column=2)
        ttk.Button(output_frame, text="Merge Files", command=self.start_merge_process).grid(row=1, column=0,
                                                                                            columnspan=3, pady=(10, 0))

    def setup_progress_area(self, parent):
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))
        progress_frame.columnconfigure(0, weight=1)
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.status_var).grid(row=1, column=0, sticky=tk.W)

    def add_file_dialog(self):
        path = filedialog.askopenfilename(
            title="Wybierz plik wideo lub obraz",
            filetypes=[("Video/Image", "*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png")]
        )
        if not path: return

        # Predefiniowane napisy, które pojawią się przy dodaniu nowego klipu
        initial_texts = [
            {
                'text': '{indeks}',
                'config': {
                    'fontsize': 30, 'color': 'white', 'movement': 'static',
                    'opacity': 0.9, 'position': (0.15, 0.15),  # Lewy górny róg
                    'start_time': 0, 'duration': 0.0, 'font': 'Arial-Bold'
                }
            },
            {
                'text': '{NAZWA_PL}',
                'config': {
                    'fontsize': 30, 'color': 'white', 'movement': 'static',
                    'opacity': 0.9, 'position': (0.25, 0.1),  # Lewy górny róg
                    'start_time': 0, 'duration': 0.0, 'font': 'Arial-Bold'
                }
            },
            {
                'text': 'vive.com',
                'config': {
                    'fontsize': 30, 'color': 'white', 'movement': 'static',
                    'opacity': 0.9, 'position': (0.85, 0.95),  # Prawy dolny róg
                    'start_time': 0, 'duration': 0.0, 'font': 'Arial-Bold'
                }
            }
        ]

        item_no_from_main = self.item_no_var.get().strip()
        is_image = path.lower().endswith(('.jpg', '.jpeg', '.png'))
        dialog = VideoConfigDialog(self.root, "Dodaj/Edytuj tekst na klipie", video_path=path,
                                   texts_data=initial_texts, is_image=is_image, item_no=item_no_from_main)
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            path, texts_data, duration = dialog.result
            self.merger.add_clip(path, texts_data, image_duration=duration)
            self.update_file_list()

    def edit_file_dialog(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to edit.")
            return
        item = selection[0]
        index = self.tree.index(item)
        clip_index = index + len(self.pre_template_clips)
        if clip_index >= len(self.merger.clips_data): return  # Safety check
        clip_data = self.merger.clips_data[clip_index]
        dialog = VideoConfigDialog(self.root, "Add/Edit Text on Clip",
                                   video_path=clip_data['path'], texts_data=clip_data['texts'],
                                   is_image=clip_data['is_image'], image_duration=clip_data.get('image_duration', 5),
                                   item_no=self.item_no_var.get().strip())
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            path, new_texts_data, new_duration = dialog.result
            clip_data['texts'] = new_texts_data
            if clip_data['is_image']: clip_data['image_duration'] = new_duration
            self.update_file_list()

    def remove_file(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to remove.")
            return
        indices = sorted([self.tree.index(item) + len(self.pre_template_clips) for item in selection], reverse=True)
        for index in indices:
            self.merger.clips_data.pop(index)
        self.update_file_list()

    def move_file_up(self):
        selection = self.tree.selection()
        if not selection: return
        for item in selection:
            index = self.tree.index(item)
            adjusted_index = index + len(self.pre_template_clips)
            # Pozwól przesuwać tylko w obrębie klipów użytkownika
            if adjusted_index > len(self.pre_template_clips):
                self.merger.clips_data.insert(adjusted_index - 1, self.merger.clips_data.pop(adjusted_index))
        self.update_file_list()

    def move_file_down(self):
        selection = self.tree.selection()
        if not selection: return
        user_clips_count = len(self.merger.clips_data) - len(self.pre_template_clips)
        for item in reversed(selection):
            index = self.tree.index(item)
            # Sprawdź, czy nie jest to ostatni klip użytkownika
            if index < user_clips_count - 1:
                adjusted_index = index + len(self.pre_template_clips)
                self.merger.clips_data.insert(adjusted_index + 1, self.merger.clips_data.pop(adjusted_index))
        self.update_file_list()

    def clear_all_files(self):
        user_clips_exist = len(self.merger.clips_data) > len(self.pre_template_clips)
        if user_clips_exist and messagebox.askyesno("Confirm Clear",
                                                    "Are you sure you want to clear all non-template files?"):
            # Usuń tylko klipy użytkownika, zachowaj szablony
            self.merger.clips_data = self.merger.clips_data[:len(self.pre_template_clips)]
            self.update_file_list()

    def update_file_list(self):
        self.tree.selection_remove(self.tree.selection())
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Wyświetlaj tylko klipy dodane przez użytkownika
        start_idx = len(self.pre_template_clips)
        for i, clip_data in enumerate(self.merger.clips_data[start_idx:]):
            filename = os.path.basename(clip_data['path'])
            if clip_data['is_image']:
                duration = clip_data.get('image_duration', 5)
                filename = f"{filename} ({duration}s)"
            num_texts = len(clip_data.get('texts', []))
            text_display = f"{num_texts} overlay(s)" if num_texts > 0 else "No text"
            self.tree.insert('', 'end', values=(i + 1, filename, text_display))

    def browse_output_file(self):
        filename = filedialog.asksaveasfilename(
            title="Save merged video as", defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
        if filename: self.output_var.set(filename)

    def update_progress(self, percentage=None, message=""):
        self.root.after(0, lambda: self._actual_update_progress(percentage, message))

    def _actual_update_progress(self, percentage, message):
        if percentage is not None:
            if self.progress_bar['mode'] == 'indeterminate':
                self.progress_bar.stop()
                self.progress_bar['mode'] = 'determinate'
            self.progress_bar['value'] = percentage
        else:
            if self.progress_bar['mode'] == 'determinate':
                self.progress_bar['mode'] = 'indeterminate'
                self.progress_bar.start()
        self.status_var.set(message)

    def merge_complete(self, success, message):
        self.progress_bar.stop()
        self.progress_bar['value'] = 0
        self.progress_bar['mode'] = 'determinate'
        self.status_var.set("Ready" if success else "Merge Failed!")
        if success:
            messagebox.showinfo("Success", message)
            # Przeładuj szablon i zaktualizuj listę plików po pomyślnym scaleniu
            self.load_template()
            self.update_file_list()
        else:
            messagebox.showerror("Error", message)

    def reload_excel(self, arguments=None, wait=True, capture_output=False):
        """
        Uruchamia plik wykonywalny (.exe) z opcjonalnymi argumentami

        :param exe_path: Ścieżka do pliku .exe
        :param arguments: Lista argumentów jako stringi (opcjonalnie)
        :param wait: Czy czekać na zakończenie procesu (domyślnie True)
        :param capture_output: Przechwytywanie outputu (domyślnie False)
        :return: Obiekt CompletedProcess lub Popen w zależności od parametru wait
        """
        exe_path = "pobieranie_danych_z_nav.exe"
        # Sprawdź czy plik istnieje
        if not os.path.exists(exe_path):
            raise FileNotFoundError(f"Plik '{exe_path}' nie istnieje!")

        # Przygotuj komendę
        command = [exe_path]
        if arguments:
            command.extend(arguments)

        try:
            # Uruchom proces
            if wait:
                if capture_output:
                    # Uruchom i przechwyć output
                    result = subprocess.run(
                        command,
                        check=True,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    return result
                else:
                    # Uruchom bez przechwytywania outputu
                    return subprocess.run(command, check=True)
            else:
                # Uruchom bez oczekiwania na zakończenie
                return subprocess.Popen(command)

        except subprocess.CalledProcessError as e:
            print(f"Błąd podczas uruchamiania: {e}")
            if capture_output:
                print(f"STDOUT: {e.stdout}")
                print(f"STDERR: {e.stderr}")
            raise
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")
            raise