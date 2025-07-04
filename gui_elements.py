import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os
os.environ['IMAGEMAGICK_BINARY'] = r'C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe'

class VideoConfigDialog:
    def __init__(self, parent, title, video_path="", text_content="", text_config=None, is_image=False, image_duration=5):
        self.is_image = is_image
        self.initial_image_duration = image_duration # Store initial value for image duration
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.update_idletasks()
        x = (parent.winfo_rootx() + parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = (parent.winfo_rooty() + parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Initialize duration widgets to None
        self.duration_label = None
        self.duration_scale = None
        self.duration_var = tk.IntVar(value=self.initial_image_duration) # Always create var

        self.setup_dialog_ui(video_path, text_content, text_config)

    def update_scale_value(self, value, label_widget, decimals=0):
        """Update the label next to a scale with the current value"""
        try:
            if decimals == 0:
                display_value = int(float(value))
                label_widget.config(text=str(display_value))
            else:
                display_value = round(float(value), decimals)
                label_widget.config(text=f"{display_value:.{decimals}f}")
        except ValueError:
            pass

    def setup_dialog_ui(self, video_path, text_content, text_config):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)

        # Video/Image File
        ttk.Label(main_frame, text="File:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        self.video_var = tk.StringVar(value=video_path)
        video_frame = ttk.Frame(main_frame)
        video_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        video_frame.columnconfigure(0, weight=1)
        ttk.Entry(video_frame, textvariable=self.video_var).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(video_frame, text="Browse", command=self.browse_file).grid(row=0, column=1)

        # Text Overlay
        ttk.Label(main_frame, text="Text Overlay:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        self.text_var = tk.StringVar(value=text_content)
        self.text_entry = ttk.Entry(main_frame, textvariable=self.text_var)
        self.text_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        self.text_entry.bind("<KeyRelease>", self.toggle_position_controls)


        # Config Frame
        # Name the config_frame so we can reference it later
        self.config_frame = ttk.LabelFrame(main_frame, text="Text Configuration", padding="10", name="config_frame")
        self.config_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 20))
        self.config_frame.columnconfigure(1, weight=1)

        default_config = {'fontsize': 50, 'color': 'white', 'movement': 'static', 'opacity': 0.8,
                          'position': ('center', 'center')}
        if text_config: default_config.update(text_config)

        # Config Controls
        self.setup_config_controls(self.config_frame, default_config)

        # OK/Cancel Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT)

        # Initial call to set correct state
        self.update_duration_visibility() # Call this first to ensure correct initial state
        self.toggle_position_controls()

    def setup_config_controls(self, parent_frame, config):
        row_idx = 0

        # Font Size
        ttk.Label(parent_frame, text="Font Size:").grid(row=row_idx, column=0, sticky=tk.W, pady=5)
        self.fontsize_var = tk.IntVar(value=config['fontsize'])
        self.fontsize_value = ttk.Label(parent_frame, text=str(self.fontsize_var.get()))
        self.fontsize_value.grid(row=row_idx, column=2, sticky=tk.W, padx=(10, 0), pady=5)

        fontsize_scale = ttk.Scale(parent_frame, from_=20, to=150, variable=self.fontsize_var,
                                   orient=tk.HORIZONTAL,
                                   command=lambda v: self.update_scale_value(v, self.fontsize_value))
        fontsize_scale.grid(row=row_idx, column=1, sticky=(tk.W, tk.E), pady=5)
        row_idx += 1

        # Color
        ttk.Label(parent_frame, text="Color:").grid(row=row_idx, column=0, sticky=tk.W, pady=5)
        color_frame = ttk.Frame(parent_frame)
        color_frame.grid(row=row_idx, column=1, sticky=(tk.W, tk.E), pady=5)
        self.color_var = tk.StringVar(value=config['color'])
        ttk.Entry(color_frame, textvariable=self.color_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(color_frame, text="Choose", command=self.choose_color).pack(side=tk.RIGHT)
        row_idx += 1

        # Opacity
        ttk.Label(parent_frame, text="Opacity:").grid(row=row_idx, column=0, sticky=tk.W, pady=5)
        self.opacity_var = tk.DoubleVar(value=config['opacity'])
        self.opacity_value = ttk.Label(parent_frame, text=f"{self.opacity_var.get():.1f}")
        self.opacity_value.grid(row=row_idx, column=2, sticky=tk.W, padx=(10, 0), pady=5)

        opacity_scale = ttk.Scale(parent_frame, from_=0.1, to=1.0, variable=self.opacity_var,
                                  orient=tk.HORIZONTAL,
                                  command=lambda v: self.update_scale_value(v, self.opacity_value, 1))
        opacity_scale.grid(row=row_idx, column=1, sticky=(tk.W, tk.E), pady=5)
        row_idx += 1

        # Placeholder for image duration
        self.duration_row_idx = row_idx
        row_idx += 1

        # Movement
        ttk.Label(parent_frame, text="Animation:").grid(row=row_idx, column=0, sticky=tk.W, pady=5)
        self.movement_var = tk.StringVar(value=config['movement'])
        self.movement_combo = ttk.Combobox(parent_frame, textvariable=self.movement_var,
                                           values=['static', 'bounce', 'slide', 'float'], state='readonly')
        self.movement_combo.grid(row=row_idx, column=1, sticky=(tk.W, tk.E), pady=5)
        self.movement_combo.bind("<<ComboboxSelected>>", self.toggle_position_controls)
        row_idx += 1

        # Position Canvas
        ttk.Label(parent_frame, text="Position:").grid(row=row_idx, column=0, sticky=tk.W, pady=5)
        position_frame = ttk.Frame(parent_frame)
        position_frame.grid(row=row_idx, column=1, sticky=(tk.W, tk.E), pady=5)
        self.canvas_width, self.canvas_height = 320, 180
        self.position_canvas = tk.Canvas(position_frame, width=self.canvas_width, height=self.canvas_height,
                                         bg='#222222', cursor='crosshair')
        self.position_canvas.pack()
        self.position_canvas.bind("<Button-1>", self.on_canvas_click)
        self.pos_label_var = tk.StringVar()
        self.pos_label = ttk.Label(position_frame, textvariable=self.pos_label_var)
        self.pos_label.pack(pady=(5, 0))

        self.selected_position = self._get_initial_pos_coords(config.get('position'))
        self.update_canvas_marker(self.selected_position)

    def toggle_position_controls(self, event=None):
        is_static = self.movement_var.get() == 'static'
        has_text = self.text_var.get().strip() != ""

        if is_static and has_text:
            self.position_canvas.config(state=tk.NORMAL, cursor='crosshair', bg='#222222')
            self.position_canvas.bind("<Button-1>", self.on_canvas_click)
            self.update_canvas_marker(self.selected_position)
        else:
            self.position_canvas.config(state=tk.DISABLED, cursor='', bg='grey')
            self.position_canvas.delete("marker")
            self.position_canvas.unbind("<Button-1>") # Disable click
            if not has_text:
                self.pos_label_var.set("Add text to enable position controls")
            elif not is_static:
                anim_name = self.movement_var.get().capitalize()
                self.pos_label_var.set(f"Position controlled by '{anim_name}' animation")


    def _get_initial_pos_coords(self, position_val):
        if isinstance(position_val, (tuple, list)) and len(position_val) == 2 and isinstance(position_val[0], (int, float)):
            return position_val
        return (int(self.canvas_width / 2), int(self.canvas_height / 2))

    def update_canvas_marker(self, pos, color='red'):
        x, y = pos
        self.position_canvas.delete("marker")
        self.position_canvas.create_line(x - 8, y, x + 8, y, fill=color, tags="marker", width=2)
        self.position_canvas.create_line(x, y - 8, x, y + 8, fill=color, tags="marker", width=2)
        self.pos_label_var.set(f"Position: ({x}, {y})")

    def on_canvas_click(self, event):
        # Ensure click is within canvas bounds
        x = max(0, min(event.x, self.canvas_width))
        y = max(0, min(event.y, self.canvas_height))
        self.selected_position = (x, y)
        self.update_canvas_marker(self.selected_position)

    def browse_file(self):
        filename = filedialog.askopenfilename(title="Select video or image file",
                                              filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"),
                                                         ("Image files", "*.jpg *.jpeg *.png"),
                                                         ("All files", "*.*")])
        if filename:
            self.video_var.set(filename)
            # Update is_image and toggle duration controls
            self.is_image = filename.lower().endswith(('.jpg', '.jpeg', '.png'))
            self.update_duration_visibility()

    def update_duration_visibility(self):
        # Dynamically add/remove duration controls based on self.is_image
        if self.is_image:
            # Create widgets if they don't exist
            if self.duration_label is None:
                self.duration_label = ttk.Label(self.config_frame, text="Duration (seconds):")
                self.duration_var = tk.IntVar(value=self.initial_image_duration)
                self.duration_value = ttk.Label(self.config_frame, text=str(self.duration_var.get()))
                self.duration_scale = ttk.Scale(self.config_frame, from_=1, to=30, variable=self.duration_var,
                                                orient=tk.HORIZONTAL,
                                                command=lambda v: self.update_scale_value(v, self.duration_value))

            # Place them in the correct grid positions
            self.duration_label.grid(row=self.duration_row_idx, column=0, sticky=tk.W, pady=5)
            self.duration_scale.grid(row=self.duration_row_idx, column=1, sticky=(tk.W, tk.E))
            self.duration_value.grid(row=self.duration_row_idx, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        else:
            # Hide/destroy if not an image
            if self.duration_label is not None:
                self.duration_label.grid_forget()
                self.duration_scale.grid_forget()
                if hasattr(self, 'duration_value'):
                    self.duration_value.grid_forget()

    def choose_color(self):
        color = colorchooser.askcolor(title="Choose text color")
        if color and color[1]: self.color_var.set(color[1])

    def ok_clicked(self):
        video_path = self.video_var.get().strip()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("Error", "Please select a valid file.", parent=self.dialog)
            return

        text_content = self.text_var.get().strip()
        text_config = {
            'fontsize': self.fontsize_var.get(),
            'color': self.color_var.get(),
            'movement': self.movement_var.get(),
            'opacity': round(self.opacity_var.get(), 2),
            'position': self.selected_position if self.movement_var.get() == 'static' else ('center', 'center')
        }

        if self.is_image:
            duration = self.duration_var.get()
            self.result = (video_path, text_content, text_config, duration)
        else:
            self.result = (video_path, text_content, text_config)
        self.dialog.destroy()

    def cancel_clicked(self):
        self.dialog.destroy()