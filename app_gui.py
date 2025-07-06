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
        list_label = ttk.Label(parent, text="Clip Order:", font=('Arial', 12, 'bold'))
        list_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

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

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.status_var).grid(row=1, column=0, sticky=tk.W)

    def add_file_dialog(self):
        path = filedialog.askopenfilename(
            title="Wybierz plik wideo lub obraz",
            filetypes=[("Video/Image", "*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png")]
        )
        if not path:
            return

        is_image = path.lower().endswith(('.jpg', '.jpeg', '.png'))
        dialog = VideoConfigDialog(self.root, "Add/Edit Text on Clip", video_path=path, texts_data=[],
                                   is_image=is_image)
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

        clip_data = self.merger.clips_data[index]

        dialog = VideoConfigDialog(self.root, "Add/Edit Text on Clip",
                                   video_path=clip_data['path'],
                                   texts_data=clip_data['texts'],
                                   is_image=clip_data['is_image'],
                                   image_duration=clip_data.get('image_duration', 5))
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            path, new_texts_data, new_duration = dialog.result
            clip_data['texts'] = new_texts_data
            if clip_data['is_image']:
                clip_data['image_duration'] = new_duration
            self.update_file_list()

    def remove_file(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to remove.")
            return

        indices = sorted([self.tree.index(item) for item in selection], reverse=True)
        for index in indices:
            self.merger.clips_data.pop(index)
        self.update_file_list()

    def move_file_up(self):
        selection = self.tree.selection()
        if not selection: return
        for item in selection:
            index = self.tree.index(item)
            if index > 0:
                self.merger.clips_data.insert(index - 1, self.merger.clips_data.pop(index))
        self.update_file_list()

    def move_file_down(self):
        selection = self.tree.selection()
        if not selection: return
        for item in reversed(selection):
            index = self.tree.index(item)
            if index < len(self.merger.clips_data) - 1:
                self.merger.clips_data.insert(index + 1, self.merger.clips_data.pop(index))
        self.update_file_list()

    def clear_all_files(self):
        if self.merger.clips_data and messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all files?"):
            self.merger.clips_data.clear()
            self.update_file_list()

    def update_file_list(self):
        # Deselect to avoid issues
        self.tree.selection_remove(self.tree.selection())

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, clip_data in enumerate(self.merger.clips_data):
            filename = os.path.basename(clip_data['path'])

            if clip_data['is_image']:
                duration = clip_data.get('image_duration', 5)
                filename = f"{filename} ({duration}s)"

            num_texts = len(clip_data.get('texts', []))
            text_display = f"{num_texts} overlay(s)" if num_texts > 0 else "No text"

            self.tree.insert('', 'end', values=(i + 1, filename, text_display))

    def browse_output_file(self):
        filename = filedialog.asksaveasfilename(
            title="Save merged video as",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
        if filename: self.output_var.set(filename)

    def start_merge_process(self):
        if not self.merger.clips_data:
            messagebox.showwarning("No Files", "Please add at least one video or image to merge.")
            return
        if not self.output_var.get():
            messagebox.showwarning("No Output File", "Please specify an output file.")
            return

        self.progress_bar['value'] = 0
        self.progress_bar['mode'] = 'determinate'
        self.status_var.set("Processing...")

        thread = threading.Thread(target=self.merge_files_thread, args=(self.output_var.get(), self.update_progress),
                                  daemon=True)
        thread.start()

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

    def merge_files_thread(self, output_path, progress_callback):
        success, message = self.merger.merge_videos(output_path, progress_callback)
        self.root.after(0, lambda: self.merge_complete(success, message))

    def merge_complete(self, success, message):
        self.progress_bar.stop()
        self.progress_bar['value'] = 0
        self.progress_bar['mode'] = 'determinate'
        self.status_var.set("Ready" if success else "Merge Failed!")
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)