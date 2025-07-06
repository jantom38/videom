import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os

os.environ['IMAGEMAGICK_BINARY'] = r'C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe'
import copy


class VideoConfigDialog:
    def __init__(self, parent, title, video_path="", texts_data=None, is_image=False, image_duration=5):
        self.parent = parent
        self.is_image = is_image
        self.image_duration = image_duration
        self.texts_data = copy.deepcopy(texts_data) if texts_data is not None else []
        self.result = None
        self.selected_text_id = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("800x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_dialog_ui(video_path)
        self.populate_texts_tree()
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
        self.toggle_config_controls_state()

    def setup_dialog_ui(self, video_path):
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=3)  # Give more space to config frame
        main_frame.rowconfigure(1, weight=1)

        # --- Left Panel: File and Texts List ---
        left_panel = ttk.Frame(main_frame, padding="10")
        left_panel.grid(row=0, column=0, rowspan=2, sticky="nswe", padx=(0, 10))
        left_panel.rowconfigure(3, weight=1)

        ttk.Label(left_panel, text="File:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.video_var = tk.StringVar(value=video_path)
        ttk.Entry(left_panel, textvariable=self.video_var, state='readonly').grid(row=1, column=0, sticky="ew",
                                                                                  pady=(0, 10))

        ttk.Label(left_panel, text="Text Overlays:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.W,
                                                                                      pady=(0, 5))
        self.setup_texts_tree(left_panel)
        self.setup_text_buttons(left_panel)

        # --- Right Panel: Configuration ---
        self.config_frame = ttk.LabelFrame(main_frame, text="Text Configuration (select a text to edit)", padding="15")
        self.config_frame.grid(row=0, column=1, rowspan=2, sticky="nswe")
        self.config_frame.columnconfigure(1, weight=1)
        self.setup_config_controls(self.config_frame)

        # --- Bottom Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="e")
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT)

    def setup_texts_tree(self, parent):
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=3, column=0, sticky='nswe')
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ('#', 'Text', 'Time')
        self.texts_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
        self.texts_tree.heading('#', text='#', anchor='w')
        self.texts_tree.heading('Text', text='Text Content')
        self.texts_tree.heading('Time', text='Timing (s)')
        self.texts_tree.column('#', width=30, stretch=tk.NO, anchor='w')
        self.texts_tree.column('Text', width=120)
        self.texts_tree.column('Time', width=80)
        self.texts_tree.grid(row=0, column=0, sticky='nswe')

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.texts_tree.yview)
        self.texts_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')

        self.texts_tree.bind('<<TreeviewSelect>>', self.on_text_selected)

    def setup_text_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, pady=(10, 0))
        ttk.Button(button_frame, text="Add", command=self.add_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove", command=self.remove_text).pack(side=tk.LEFT, padx=5)

    def setup_config_controls(self, parent_frame):
        row = 0
        # Text Content
        ttk.Label(parent_frame, text="Text:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.text_var = tk.StringVar()
        self.text_entry = ttk.Entry(parent_frame, textvariable=self.text_var)
        self.text_entry.grid(row=row, column=1, columnspan=2, sticky="ew", pady=5)
        self.text_entry.bind("<KeyRelease>", self.update_selected_text_data)
        row += 1

        # Font Size
        ttk.Label(parent_frame, text="Font Size:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.fontsize_var = tk.IntVar(value=50)
        scale = ttk.Scale(parent_frame, from_=10, to=200, variable=self.fontsize_var, orient=tk.HORIZONTAL,
                          command=self.update_selected_text_data)
        scale.grid(row=row, column=1, sticky="ew", pady=5)
        ttk.Label(parent_frame, textvariable=self.fontsize_var).grid(row=row, column=2, padx=5)
        row += 1

        # Color
        ttk.Label(parent_frame, text="Color:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.color_var = tk.StringVar(value='white')
        color_entry = ttk.Entry(parent_frame, textvariable=self.color_var)
        color_entry.grid(row=row, column=1, sticky="ew")
        color_entry.bind("<KeyRelease>", self.update_selected_text_data)
        ttk.Button(parent_frame, text="Choose", command=self.choose_color).grid(row=row, column=2, padx=5)
        row += 1

        # Opacity
        ttk.Label(parent_frame, text="Opacity:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.opacity_var = tk.DoubleVar(value=0.8)
        scale = ttk.Scale(parent_frame, from_=0.0, to=1.0, variable=self.opacity_var, orient=tk.HORIZONTAL,
                          command=self.update_selected_text_data)
        scale.grid(row=row, column=1, sticky="ew", pady=5)
        self.opacity_label = ttk.Label(parent_frame, text="0.8")
        self.opacity_label.grid(row=row, column=2, padx=5)
        row += 1

        # Timing
        timing_frame = ttk.LabelFrame(parent_frame, text="Timing", padding=10)
        timing_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=10)
        timing_frame.columnconfigure(1, weight=1)
        timing_frame.columnconfigure(3, weight=1)

        ttk.Label(timing_frame, text="Start (s):").grid(row=0, column=0, padx=5)
        self.start_time_var = tk.DoubleVar(value=0)
        start_spin = ttk.Spinbox(timing_frame, from_=0, to=9999, increment=0.1, textvariable=self.start_time_var,
                                 command=self.update_selected_text_data, width=8)
        start_spin.grid(row=0, column=1, sticky="ew")
        start_spin.bind("<KeyRelease>", self.update_selected_text_data)

        ttk.Label(timing_frame, text="Duration (s):").grid(row=0, column=2, padx=5)
        self.duration_var = tk.DoubleVar(value=0)
        dur_spin = ttk.Spinbox(timing_frame, from_=0, to=9999, increment=0.1, textvariable=self.duration_var,
                               command=self.update_selected_text_data, width=8)
        dur_spin.grid(row=0, column=3, sticky="ew")
        dur_spin.bind("<KeyRelease>", self.update_selected_text_data)
        ttk.Label(timing_frame, text="(0=full clip)").grid(row=1, column=2, columnspan=2, sticky='w', padx=5)
        row += 1

        # Movement
        ttk.Label(parent_frame, text="Animation:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.movement_var = tk.StringVar(value='static')
        self.movement_combo = ttk.Combobox(parent_frame, textvariable=self.movement_var,
                                           values=['static', 'bounce', 'slide', 'float'], state='readonly')
        self.movement_combo.grid(row=row, column=1, columnspan=2, sticky="ew", pady=5)
        self.movement_combo.bind("<<ComboboxSelected>>", self.update_selected_text_data)
        row += 1

        # Position
        ttk.Label(parent_frame, text="Position:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.canvas_width, self.canvas_height = 320, 180
        self.position_canvas = tk.Canvas(parent_frame, width=self.canvas_width, height=self.canvas_height, bg='#222222',
                                         cursor='crosshair')
        self.position_canvas.grid(row=row, column=1, columnspan=2, pady=5)
        self.position_canvas.bind("<Button-1>", self.on_canvas_click)
        self.pos_label_var = tk.StringVar(value="Select position for 'static' animation")
        ttk.Label(parent_frame, textvariable=self.pos_label_var).grid(row=row + 1, column=1, columnspan=2)

        # Image Duration (only visible if it's an image)
        if self.is_image:
            img_dur_frame = ttk.LabelFrame(self.config_frame, text="Image Settings", padding=10)
            img_dur_frame.grid(row=row + 2, column=0, columnspan=3, sticky='ew', pady=(20, 0))
            ttk.Label(img_dur_frame, text="Image Duration (s):").pack(side=tk.LEFT, padx=5)
            self.image_duration_var = tk.IntVar(value=self.image_duration)
            ttk.Spinbox(img_dur_frame, from_=1, to=300, textvariable=self.image_duration_var).pack(side=tk.LEFT)

    def populate_texts_tree(self):
        for item in self.texts_tree.get_children():
            self.texts_tree.delete(item)
        for i, text_data in enumerate(self.texts_data):
            text_content = text_data.get('text', 'No Text')
            start = text_data['config'].get('start_time', 0)
            dur = text_data['config'].get('duration', 0)
            timing_str = f"{start} - {start + dur if dur > 0 else 'end'}"
            self.texts_tree.insert('', 'end', iid=i, values=(i + 1, text_content, timing_str))

    # *** FIX: Restored the missing on_text_selected method ***
    def on_text_selected(self, event=None):
        selection = self.texts_tree.selection()
        if not selection:
            self.selected_text_id = None
            self.toggle_config_controls_state(disabled=True)
            return

        # The 'iid' of the selected item is its index in the list
        self.selected_text_id = int(selection[0])

        self.toggle_config_controls_state(disabled=False)
        self.load_config_for_selected_text()

    def load_config_for_selected_text(self):
        if self.selected_text_id is None or self.selected_text_id >= len(self.texts_data):
            return

        data = self.texts_data[self.selected_text_id]
        config = data.get('config', {})

        self.text_var.set(data.get('text', ''))
        self.fontsize_var.set(config.get('fontsize', 50))
        self.color_var.set(config.get('color', 'white'))
        self.opacity_var.set(config.get('opacity', 0.8))
        self.opacity_label.config(text=f"{self.opacity_var.get():.1f}")
        self.start_time_var.set(config.get('start_time', 0))
        self.duration_var.set(config.get('duration', 0))
        self.movement_var.set(config.get('movement', 'static'))

        self.update_canvas(config.get('position'), config.get('movement'))

    def update_selected_text_data(self, event=None):
        if self.selected_text_id is None or self.selected_text_id >= len(self.texts_data):
            return

        try:
            start_time = self.start_time_var.get()
            duration = self.duration_var.get()
        except tk.TclError:
            return

        new_config = {
            'fontsize': self.fontsize_var.get(),
            'color': self.color_var.get(),
            'movement': self.movement_var.get(),
            'opacity': round(self.opacity_var.get(), 2),
            'start_time': start_time,
            'duration': duration,
            'position': self.texts_data[self.selected_text_id]['config'].get('position')
        }

        self.texts_data[self.selected_text_id]['text'] = self.text_var.get()
        self.texts_data[self.selected_text_id]['config'] = new_config

        self.opacity_label.config(text=f"{new_config['opacity']:.1f}")
        self.update_canvas(new_config['position'], new_config['movement'])
        self.populate_texts_tree()

        if self.texts_tree.exists(str(self.selected_text_id)):
            self.texts_tree.selection_set(str(self.selected_text_id))

    def add_text(self):
        center_pos = (self.canvas_width / 2, self.canvas_height / 2)
        new_text_data = {
            'text': 'New Text',
            'config': {
                'fontsize': 50, 'color': 'white', 'movement': 'static',
                'opacity': 0.8, 'position': center_pos,
                'start_time': 0, 'duration': 5, 'font': 'Arial-Bold'
            }
        }
        self.texts_data.append(new_text_data)
        self.populate_texts_tree()
        new_id = len(self.texts_data) - 1
        self.texts_tree.selection_set(new_id)
        self.texts_tree.focus(new_id)

    def remove_text(self):
        if self.selected_text_id is None:
            messagebox.showwarning("Warning", "Please select a text to remove.", parent=self.dialog)
            return

        self.texts_data.pop(self.selected_text_id)
        self.selected_text_id = None
        self.populate_texts_tree()
        self.toggle_config_controls_state(disabled=True)

    def choose_color(self):
        if self.selected_text_id is None: return
        color_code = colorchooser.askcolor(title="Choose color", parent=self.dialog)
        if color_code and color_code[1]:
            self.color_var.set(color_code[1])
            self.update_selected_text_data()

    def on_canvas_click(self, event):
        if self.selected_text_id is None or self.movement_var.get() != 'static': return
        x = max(0, min(event.x, self.canvas_width))
        y = max(0, min(event.y, self.canvas_height))

        self.texts_data[self.selected_text_id]['config']['position'] = (x, y)
        self.update_canvas((x, y), 'static')

    def update_canvas(self, pos, movement):
        self.position_canvas.delete("marker")
        if movement == 'static':
            self.position_canvas.config(state=tk.NORMAL, cursor='crosshair', bg='#222222')
            if pos and isinstance(pos, (tuple, list)):
                x_val, y_val = pos

                x = self.canvas_width / 2 if x_val == 'center' else x_val
                y = self.canvas_height / 2 if y_val == 'center' else y_val

                if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    self.position_canvas.create_line(x - 8, y, x + 8, y, fill='red', tags="marker", width=2)
                    self.position_canvas.create_line(x, y - 8, x, y + 8, fill='red', tags="marker", width=2)
                    self.pos_label_var.set(f"Position: ({int(x)}, {int(y)})")
                else:
                    self.pos_label_var.set("Click to set position")
            else:
                self.pos_label_var.set("Click to set position")
        else:
            self.position_canvas.config(state=tk.DISABLED, cursor='', bg='grey')
            anim_name = movement.capitalize()
            self.pos_label_var.set(f"Position controlled by '{anim_name}'")

    def toggle_config_controls_state(self, disabled=True):
        state = tk.DISABLED if disabled else tk.NORMAL
        for child in self.config_frame.winfo_children():
            if isinstance(child, (ttk.LabelFrame)):
                for sub_child in child.winfo_children():
                    try:
                        sub_child.configure(state=state)
                    except tk.TclError:
                        pass
            else:
                try:
                    child.configure(state=state)
                except tk.TclError:
                    pass

        if disabled or self.movement_var.get() != 'static':
            self.position_canvas.config(state=tk.DISABLED, bg='grey')
        else:
            self.position_canvas.config(state=tk.NORMAL, bg='#222222')

        if disabled:
            self.config_frame.config(text="Text Configuration (select a text to edit)")
        elif self.selected_text_id is not None:
            self.config_frame.config(text=f"Editing Text #{self.selected_text_id + 1}")

    def ok_clicked(self):
        video_path = self.video_var.get().strip()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("Error", "Please select a valid file.", parent=self.dialog)
            return

        if self.is_image:
            duration = self.image_duration_var.get()
            self.result = (video_path, self.texts_data, duration)
        else:
            self.result = (video_path, self.texts_data, None)
        self.dialog.destroy()

    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()