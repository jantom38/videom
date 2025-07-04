import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
os.environ['IMAGEMAGICK_BINARY'] = r'C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe'
import threading
from video_merger import VideoMerger
from gui_elements import VideoConfigDialog


class VideoMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Merger with Floating Text")
        self.root.geometry("900x700")

        self.merger = VideoMerger()
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        title_label = ttk.Label(main_frame, text="Video Merger with Floating Text", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        self.setup_video_list(main_frame)
        self.setup_control_buttons(main_frame)
        self.setup_output_settings(main_frame)
        self.setup_progress_area(main_frame)

    def setup_video_list(self, parent):
        list_label = ttk.Label(parent, text="Video/Image List:", font=('Arial', 12, 'bold'))
        list_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        columns = ('Order', 'File', 'Text Overlay', 'Animation', 'Position', 'Color')
        self.tree = ttk.Treeview(parent, columns=columns, show='headings', height=10)

        self.tree.heading('Order', text='#')
        self.tree.heading('File', text='File')
        self.tree.heading('Text Overlay', text='Text Overlay')
        self.tree.heading('Animation', text='Animation')
        self.tree.heading('Position', text='Position')
        self.tree.heading('Color', text='Color')

        self.tree.column('Order', width=40, anchor='center')
        self.tree.column('File', width=200)
        self.tree.column('Text Overlay', width=150)
        self.tree.column('Animation', width=100)
        self.tree.column('Position', width=100, anchor='center')
        self.tree.column('Color', width=80)

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        scrollbar.grid(row=2, column=2, sticky=(tk.N, tk.S), pady=(0, 10))
        parent.rowconfigure(2, weight=1)

    def setup_control_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(0, 20))

        ttk.Button(button_frame, text="Add File", command=self.add_file_dialog).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Edit Selected", command=self.edit_file_dialog).grid(row=0, column=1,
                                                                                           padx=(0, 10))
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_file).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(button_frame, text="Move Up", command=self.move_file_up).grid(row=0, column=3, padx=(0, 10))
        ttk.Button(button_frame, text="Move Down", command=self.move_file_down).grid(row=0, column=4, padx=(0, 10))
        ttk.Button(button_frame, text="Clear All", command=self.clear_all_files).grid(row=0, column=5)

    def setup_output_settings(self, parent):
        output_frame = ttk.LabelFrame(parent, text="Output Settings", padding="10")
        output_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.output_var = tk.StringVar(value="merged_output.mp4")
        ttk.Entry(output_frame, textvariable=self.output_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(output_frame, text="Browse", command=self.browse_output_file).grid(row=0, column=2)
        ttk.Button(output_frame, text="Merge Files", command=self.start_merge_process).grid(row=1, column=0,
                                                                                            columnspan=3, pady=(10, 0))

    def setup_progress_area(self, parent):
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)  # Zmieniono na determinate
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.status_var).grid(row=1, column=0, sticky=tk.W)

    def add_file_dialog(self):
        path = filedialog.askopenfilename(
            title="Wybierz plik wideo lub obraz",
            filetypes=[("Video/Image", "*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png")]
        )

        if path:
            is_image = path.lower().endswith(('.jpg', '.jpeg', '.png'))
            dialog = VideoConfigDialog(self.root, "Dodaj plik", video_path=path, is_image=is_image)

            # Czekamy na zamknięcie okna dialogowego
            self.root.wait_window(dialog.dialog)

            if dialog.result:
                if len(dialog.result) == 4:
                    path, text, config, duration = dialog.result
                    self.merger.add_video(path, text, config, duration=duration)
                else:
                    path, text, config = dialog.result
                    self.merger.add_video(path, text, config)

                self.update_file_list()

    def edit_file_dialog(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to edit.")
            return

        item = selection[0]
        index = self.tree.index(item)
        current_file_path = self.merger.videos[index]
        current_text_data = self.merger.text_configs[index]
        is_image = current_text_data.get('is_image', False)
        image_duration = current_text_data.get('image_duration', 5)

        dialog = VideoConfigDialog(self.root, "Edit Video/Image",
                                   video_path=current_file_path,
                                   text_content=current_text_data['text'],
                                   text_config=current_text_data['config'],
                                   is_image=is_image,
                                   image_duration=image_duration)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            file_path, text_content, new_text_config = dialog.result[0:3]
            new_image_duration = dialog.result[3] if len(dialog.result) == 4 else None

            # Update existing configuration
            current_text_data['config'].update(new_text_config)
            current_text_data['text'] = text_content
            current_text_data['is_image'] = file_path.lower().endswith(('.jpg', '.jpeg', '.png'))
            current_text_data['image_duration'] = new_image_duration if current_text_data['is_image'] else None
            self.merger.videos[index] = file_path  # Update path in case it changed

            self.update_file_list()

    def remove_file(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to remove.")
            return

        indices = sorted([self.tree.index(item) for item in selection], reverse=True)
        for index in indices:
            self.merger.videos.pop(index)
            self.merger.text_configs.pop(index)
        self.update_file_list()

    def move_file_up(self):
        selection = self.tree.selection()
        if not selection: return
        for item in selection:
            index = self.tree.index(item)
            if index > 0:
                self.merger.videos.insert(index - 1, self.merger.videos.pop(index))
                self.merger.text_configs.insert(index - 1, self.merger.text_configs.pop(index))
        self.update_file_list()

    def move_file_down(self):
        selection = self.tree.selection()
        if not selection: return
        for item in reversed(selection):
            index = self.tree.index(item)
            if index < len(self.merger.videos) - 1:
                self.merger.videos.insert(index + 1, self.merger.videos.pop(index))
                self.merger.text_configs.insert(index + 1, self.merger.text_configs.pop(index))
        self.update_file_list()

    def clear_all_files(self):
        if self.merger.videos and messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all files?"):
            self.merger.videos.clear()
            self.merger.text_configs.clear()
            self.update_file_list()

    def update_file_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, (file_path, text_data) in enumerate(zip(self.merger.videos, self.merger.text_configs)):
            filename = os.path.basename(file_path)
            config = text_data.get('config', {})
            text_content = text_data.get('text', '').strip() or "-"
            animation = config.get('movement', 'static')
            color = config.get('color', 'white')

            if text_data.get('is_image', False):
                duration = text_data.get('image_duration', 5)
                filename = f"{filename} ({duration}s)"

            position = config.get('position', '-')
            pos_display = "-"
            if text_content != "-":  # Only show position if there's text
                if animation == 'static':
                    if isinstance(position, (tuple, list)) and len(position) > 1 and isinstance(position[0],
                                                                                                (int, float)):
                        pos_display = f"({int(position[0])}, {int(position[1])})"
                    else:
                        pos_display = str(position)
                else:
                    pos_display = "Auto"

            self.tree.insert('', 'end', values=(i + 1, filename, text_content, animation, pos_display, color))

    def browse_output_file(self):
        filename = filedialog.asksaveasfilename(
            title="Save merged video as",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
        if filename: self.output_var.set(filename)

    def start_merge_process(self):
        if not self.merger.videos:
            messagebox.showwarning("No Files", "Please add at least one video or image to merge.")
            return
        if not self.output_var.get():
            messagebox.showwarning("No Output File", "Please specify an output file.")
            return

        # Reset progress bar and status before starting
        self.progress_bar.stop()  # Stop if it was already running as indeterminate
        self.progress_bar['value'] = 0  # Reset value
        self.progress_bar['mode'] = 'determinate'  # Set mode
        self.status_var.set("Processing...")

        # Pass a lambda that calls the GUI's update_progress method
        thread = threading.Thread(target=self.merge_files_thread, args=(self.output_var.get(), self.update_progress),
                                  daemon=True)
        thread.start()

    def update_progress(self, percentage=None, message=""):
        """
        Aktualizuje pasek postępu i status w GUI.
        Wywoływana z wątku MoviePy (przez MoviePy's logger).
        """
        self.root.after(0, lambda: self._actual_update_progress(percentage, message))

    def _actual_update_progress(self, percentage, message):
        """Metoda wykonywana w głównym wątku Tkinter."""
        if percentage is not None:
            self.progress_bar['value'] = percentage
            self.status_var.set(f"{message}")
        else:
            # Jeśli nie ma procentu, aktualizujemy tylko wiadomość statusu
            self.status_var.set(message)
            self.progress_bar['mode'] = 'indeterminate'  # Przełącz na indeterminate, jeśli brak procentów
            self.progress_bar.start()  # Uruchom, jeśli był zatrzymany

    def merge_files_thread(self, output_path, progress_callback):
        # Przekazujemy progres callback bezpośrednio do VideoMerger
        success, message = self.merger.merge_videos(output_path, progress_callback)
        self.root.after(0, lambda: self.merge_complete(success, message))

    def merge_complete(self, success, message):
        self.progress_bar.stop()
        self.progress_bar['value'] = 0  # Reset progress bar value
        self.progress_bar['mode'] = 'indeterminate'  # Set back to indeterminate for future use
        self.status_var.set("Ready" if success else "Merge Failed!")
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)