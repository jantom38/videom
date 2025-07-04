#!/usr/bin/env python3
"""
Video Merger with Floating Text - GUI Application

A graphical user interface for merging videos with floating text overlays.

Requirements:
pip install moviepy pillow tkinter

Usage:
python video_merger_gui.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os
import threading
from pathlib import Path
import sys
import os
os.environ['IMAGEMAGICK_BINARY'] = r'C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe'

# Import the VideoMerger class from the previous script
import os
import sys
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import math


class VideoMerger:
    def __init__(self):
        self.videos = []
        self.text_configs = []

    def add_video(self, video_path, text_content, text_config=None):
        default_config = {
            'fontsize': 50,
            'color': 'white',
            'font': 'Arial-Bold',
            'position': ('center', 'center'),
            'duration': None,
            'start_time': 0,
            'movement': 'static',
            'opacity': 0.8
        }

        if text_config:
            default_config.update(text_config)

        self.videos.append(video_path)
        self.text_configs.append({
            'text': text_content,
            'config': default_config
        })

    def create_floating_text(self, text_content, config, video_duration):
        duration = config['duration'] if config['duration'] else video_duration

        txt_clip = TextClip(
            text_content,
            fontsize=config['fontsize'],
            color=config['color'],
            font=config['font']
        ).set_duration(duration).set_start(config['start_time'])

        txt_clip = txt_clip.set_opacity(config['opacity'])

        if config['movement'] == 'bounce':
            txt_clip = txt_clip.set_position(self._bounce_position(duration))
        elif config['movement'] == 'slide':
            txt_clip = txt_clip.set_position(self._slide_position(duration))
        elif config['movement'] == 'float':
            txt_clip = txt_clip.set_position(self._float_position(duration))
        else:
            txt_clip = txt_clip.set_position(config['position'])

        return txt_clip

    def _bounce_position(self, duration):
        return lambda t: ('center', 50 + 30 * abs(2 * (t % 2) - 1))

    def _slide_position(self, duration):
        return lambda t: (50 + (t / duration) * 500, 'center')

    def _float_position(self, duration):
        return lambda t: ('center', 100 + 50 * math.sin(2 * math.pi * t / 3))

    def process_video_with_text(self, video_path, text_data):
        """Process a single video with its text overlay"""
        try:
            print(f"Loading video: {video_path}")
            video = VideoFileClip(video_path)
            print(f"Video loaded successfully. Duration: {video.duration}s, Size: {video.size}")

            print(f"Creating text clip: '{text_data['text']}'")
            text_clip = self.create_floating_text(
                text_data['text'],
                text_data['config'],
                video.duration
            )
            print(f"Text clip created successfully")

            print(f"Compositing video with text...")
            final_video = CompositeVideoClip([video, text_clip])
            print(f"Video composited successfully")

            return final_video

        except Exception as e:
            print(f"Error in process_video_with_text: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def merge_videos(self, output_path, progress_callback=None):
        if not self.videos:
            return False, "No videos added to merge!"

        processed_clips = []
        total_videos = len(self.videos)

        print(f"Starting merge process with {total_videos} videos...")

        for i, (video_path, text_data) in enumerate(zip(self.videos, self.text_configs)):
            if progress_callback:
                progress_callback(f"Processing video {i + 1}/{total_videos}: {os.path.basename(video_path)}")

            print(f"\n--- Processing video {i + 1}/{total_videos} ---")
            print(f"Video path: {video_path}")
            print(f"Text: '{text_data['text']}'")
            print(f"Config: {text_data['config']}")

            if not os.path.exists(video_path):
                print(f"ERROR: Video file not found: {video_path}")
                continue

            try:
                processed_clip = self.process_video_with_text(video_path, text_data)
                processed_clips.append(processed_clip)
                print(f"Successfully processed video {i + 1}")

            except Exception as e:
                print(f"ERROR processing video {video_path}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

        print(f"\nProcessed {len(processed_clips)} out of {total_videos} videos")

        if not processed_clips:
            return False, "No videos were successfully processed! Check console for detailed error messages."

        try:
            if progress_callback:
                progress_callback("Merging videos...")

            print("Concatenating video clips...")
            final_video = concatenate_videoclips(processed_clips, method="compose")

            if progress_callback:
                progress_callback("Writing final video...")

            print(f"Writing final video to: {output_path}")
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )

            for clip in processed_clips:
                clip.close()
            final_video.close()

            print("Video merge completed successfully!")
            return True, f"Video successfully created: {output_path}"

        except Exception as e:
            print(f"ERROR during video merging: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, f"Error during video merging: {str(e)}"


class VideoMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Merger with Floating Text")
        self.root.geometry("900x700")

        self.merger = VideoMerger()
        self.video_entries = []

        self.setup_ui()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="Video Merger with Floating Text",
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Video list frame
        self.setup_video_list(main_frame)

        # Control buttons
        self.setup_control_buttons(main_frame)

        # Output settings
        self.setup_output_settings(main_frame)

        # Progress bar and status
        self.setup_progress_area(main_frame)

    def setup_video_list(self, parent):
        # Video list label
        list_label = ttk.Label(parent, text="Video List:", font=('Arial', 12, 'bold'))
        list_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        # Create treeview for video list
        columns = ('Order', 'Video File', 'Text Overlay', 'Animation', 'Color')
        self.tree = ttk.Treeview(parent, columns=columns, show='headings', height=8)

        # Define column headings and widths
        self.tree.heading('Order', text='#')
        self.tree.heading('Video File', text='Video File')
        self.tree.heading('Text Overlay', text='Text Overlay')
        self.tree.heading('Animation', text='Animation')
        self.tree.heading('Color', text='Color')

        self.tree.column('Order', width=50)
        self.tree.column('Video File', width=200)
        self.tree.column('Text Overlay', width=150)
        self.tree.column('Animation', width=100)
        self.tree.column('Color', width=80)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Grid the treeview and scrollbar
        self.tree.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        scrollbar.grid(row=2, column=2, sticky=(tk.N, tk.S), pady=(0, 10))

        # Configure row weight
        parent.rowconfigure(2, weight=1)

    def setup_control_buttons(self, parent):
        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(0, 20))

        # Add video button
        add_button = ttk.Button(button_frame, text="Add Video", command=self.add_video_dialog)
        add_button.grid(row=0, column=0, padx=(0, 10))

        # Edit video button
        edit_button = ttk.Button(button_frame, text="Edit Selected", command=self.edit_video_dialog)
        edit_button.grid(row=0, column=1, padx=(0, 10))

        # Remove video button
        remove_button = ttk.Button(button_frame, text="Remove Selected", command=self.remove_video)
        remove_button.grid(row=0, column=2, padx=(0, 10))

        # Move up button
        up_button = ttk.Button(button_frame, text="Move Up", command=self.move_video_up)
        up_button.grid(row=0, column=3, padx=(0, 10))

        # Move down button
        down_button = ttk.Button(button_frame, text="Move Down", command=self.move_video_down)
        down_button.grid(row=0, column=4, padx=(0, 10))

        # Clear all button
        clear_button = ttk.Button(button_frame, text="Clear All", command=self.clear_all_videos)
        clear_button.grid(row=0, column=5)

    def setup_output_settings(self, parent):
        # Output frame
        output_frame = ttk.LabelFrame(parent, text="Output Settings", padding="10")
        output_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        output_frame.columnconfigure(1, weight=1)

        # Output path
        ttk.Label(output_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.output_var = tk.StringVar(value="merged_video.mp4")
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var)
        output_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        browse_button = ttk.Button(output_frame, text="Browse", command=self.browse_output_file)
        browse_button.grid(row=0, column=2)

        # Merge button
        merge_button = ttk.Button(output_frame, text="Merge Videos", command=self.start_merge_process)
        merge_button.grid(row=1, column=0, columnspan=3, pady=(10, 0))

    def setup_progress_area(self, parent):
        # Progress frame
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))
        progress_frame.columnconfigure(0, weight=1)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                            mode='indeterminate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, sticky=tk.W)

    def add_video_dialog(self):
        """Open dialog to add a new video with text configuration"""
        dialog = VideoConfigDialog(self.root, "Add Video")
        self.root.wait_window(dialog.dialog)  # Wait for dialog to close
        if dialog.result:
            video_path, text_content, text_config = dialog.result
            self.merger.add_video(video_path, text_content, text_config)
            self.update_video_list()
            print(f"Added video: {video_path}")  # Debug print

    def edit_video_dialog(self):
        """Open dialog to edit selected video"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a video to edit.")
            return

        item = selection[0]
        index = int(self.tree.item(item, 'values')[0]) - 1

        current_video = self.merger.videos[index]
        current_text_data = self.merger.text_configs[index]

        dialog = VideoConfigDialog(self.root, "Edit Video",
                                   video_path=current_video,
                                   text_content=current_text_data['text'],
                                   text_config=current_text_data['config'])
        self.root.wait_window(dialog.dialog)  # Wait for dialog to close
        if dialog.result:
            video_path, text_content, text_config = dialog.result
            self.merger.videos[index] = video_path
            self.merger.text_configs[index] = {
                'text': text_content,
                'config': text_config
            }
            self.update_video_list()

    def remove_video(self):
        """Remove selected video from the list"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a video to remove.")
            return

        item = selection[0]
        index = int(self.tree.item(item, 'values')[0]) - 1

        self.merger.videos.pop(index)
        self.merger.text_configs.pop(index)
        self.update_video_list()

    def move_video_up(self):
        """Move selected video up in the list"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        index = int(self.tree.item(item, 'values')[0]) - 1

        if index > 0:
            # Swap with previous item
            self.merger.videos[index], self.merger.videos[index - 1] = \
                self.merger.videos[index - 1], self.merger.videos[index]
            self.merger.text_configs[index], self.merger.text_configs[index - 1] = \
                self.merger.text_configs[index - 1], self.merger.text_configs[index]
            self.update_video_list()

    def move_video_down(self):
        """Move selected video down in the list"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        index = int(self.tree.item(item, 'values')[0]) - 1

        if index < len(self.merger.videos) - 1:
            # Swap with next item
            self.merger.videos[index], self.merger.videos[index + 1] = \
                self.merger.videos[index + 1], self.merger.videos[index]
            self.merger.text_configs[index], self.merger.text_configs[index + 1] = \
                self.merger.text_configs[index + 1], self.merger.text_configs[index]
            self.update_video_list()

    def clear_all_videos(self):
        """Clear all videos from the list"""
        if self.merger.videos:
            if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all videos?"):
                self.merger.videos.clear()
                self.merger.text_configs.clear()
                self.update_video_list()

    def update_video_list(self):
        """Update the video list display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add current videos
        for i, (video_path, text_data) in enumerate(zip(self.merger.videos, self.merger.text_configs)):
            filename = os.path.basename(video_path)
            text_content = text_data['text']
            animation = text_data['config']['movement']
            color = text_data['config']['color']

            self.tree.insert('', 'end', values=(i + 1, filename, text_content, animation, color))

        # Debug print
        print(f"Video list updated. Total videos: {len(self.merger.videos)}")
        for i, video in enumerate(self.merger.videos):
            print(f"  {i + 1}: {os.path.basename(video)}")

    def browse_output_file(self):
        """Browse for output file location"""
        filename = filedialog.asksaveasfilename(
            title="Save merged video as",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("AVI files", "*.avi"), ("All files", "*.*")]
        )
        if filename:
            self.output_var.set(filename)

    def start_merge_process(self):
        """Start the video merging process in a separate thread"""
        if not self.merger.videos:
            messagebox.showwarning("No Videos", "Please add at least one video to merge.")
            return

        output_path = self.output_var.get()
        if not output_path:
            messagebox.showwarning("No Output File", "Please specify an output file.")
            return

        # Start progress bar
        self.progress_bar.start()
        self.status_var.set("Processing...")

        # Start merging in separate thread
        thread = threading.Thread(target=self.merge_videos_thread, args=(output_path,))
        thread.daemon = True
        thread.start()

    def merge_videos_thread(self, output_path):
        """Thread function for merging videos"""

        def progress_callback(message):
            self.root.after(0, lambda: self.status_var.set(message))

        success, message = self.merger.merge_videos(output_path, progress_callback)

        # Update UI in main thread
        self.root.after(0, lambda: self.merge_complete(success, message))

    def merge_complete(self, success, message):
        """Handle completion of merge process"""
        self.progress_bar.stop()

        if success:
            self.status_var.set("Merge completed successfully!")
            messagebox.showinfo("Success", message)
        else:
            self.status_var.set("Merge failed!")
            messagebox.showerror("Error", message)


class VideoConfigDialog:
    def __init__(self, parent, title, video_path="", text_content="", text_config=None):
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"500x600+{x}+{y}")

        self.setup_dialog_ui(video_path, text_content, text_config)

    def setup_dialog_ui(self, video_path, text_content, text_config):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        row = 0

        # Video file selection
        ttk.Label(main_frame, text="Video File:").grid(row=row, column=0, sticky=tk.W, pady=(0, 10))
        self.video_var = tk.StringVar(value=video_path)
        video_frame = ttk.Frame(main_frame)
        video_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        video_frame.columnconfigure(0, weight=1)

        ttk.Entry(video_frame, textvariable=self.video_var).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(video_frame, text="Browse", command=self.browse_video).grid(row=0, column=1)

        row += 1

        # Text content
        ttk.Label(main_frame, text="Text Overlay:").grid(row=row, column=0, sticky=tk.W, pady=(0, 10))
        self.text_var = tk.StringVar(value=text_content)
        ttk.Entry(main_frame, textvariable=self.text_var).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(0, 10))

        row += 1

        # Text configuration
        config_frame = ttk.LabelFrame(main_frame, text="Text Configuration", padding="10")
        config_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        config_frame.columnconfigure(1, weight=1)

        # Default values
        default_config = {
            'fontsize': 50,
            'color': 'white',
            'movement': 'static',
            'position': 'center',
            'opacity': 0.8
        }
        if text_config:
            default_config.update(text_config)

        # Font size
        ttk.Label(config_frame, text="Font Size:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        self.fontsize_var = tk.IntVar(value=default_config['fontsize'])
        fontsize_frame = ttk.Frame(config_frame)
        fontsize_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Scale(fontsize_frame, from_=20, to=100, variable=self.fontsize_var, orient=tk.HORIZONTAL).pack(side=tk.LEFT,
                                                                                                           fill=tk.X,
                                                                                                           expand=True)
        ttk.Label(fontsize_frame, textvariable=self.fontsize_var).pack(side=tk.RIGHT)

        # Color
        ttk.Label(config_frame, text="Color:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        color_frame = ttk.Frame(config_frame)
        color_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        self.color_var = tk.StringVar(value=default_config['color'])
        ttk.Entry(color_frame, textvariable=self.color_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(color_frame, text="Choose", command=self.choose_color).pack(side=tk.RIGHT)

        # Movement
        ttk.Label(config_frame, text="Animation:").grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        self.movement_var = tk.StringVar(value=default_config['movement'])
        movement_combo = ttk.Combobox(config_frame, textvariable=self.movement_var,
                                      values=['static', 'bounce', 'slide', 'float'], state='readonly')
        movement_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 10))

        # Position
        ttk.Label(config_frame, text="Position:").grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        self.position_var = tk.StringVar(value=default_config['position'])
        position_combo = ttk.Combobox(config_frame, textvariable=self.position_var,
                                      values=['center', 'top', 'bottom', 'left', 'right'], state='readonly')
        position_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 10))

        # Opacity
        ttk.Label(config_frame, text="Opacity:").grid(row=4, column=0, sticky=tk.W, pady=(0, 10))
        self.opacity_var = tk.DoubleVar(value=default_config['opacity'])
        opacity_frame = ttk.Frame(config_frame)
        opacity_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Scale(opacity_frame, from_=0.1, to=1.0, variable=self.opacity_var, orient=tk.HORIZONTAL).pack(side=tk.LEFT,
                                                                                                          fill=tk.X,
                                                                                                          expand=True)
        ttk.Label(opacity_frame, textvariable=self.opacity_var).pack(side=tk.RIGHT)

        row += 1

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT)

    def browse_video(self):
        """Browse for video file"""
        filename = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if filename:
            self.video_var.set(filename)

    def choose_color(self):
        """Choose text color"""
        color = colorchooser.askcolor(title="Choose text color")
        if color[1]:  # color[1] is the hex color
            self.color_var.set(color[1])

    def ok_clicked(self):
        """Handle OK button click"""
        video_path = self.video_var.get().strip()
        text_content = self.text_var.get().strip()

        if not video_path:
            messagebox.showerror("Error", "Please select a video file.")
            return
        if not text_content:
            messagebox.showerror("Error", "Please enter text content.")
            return
        if not os.path.exists(video_path):
            messagebox.showerror("Error", "Video file does not exist.")
            return

        # Create text configuration
        position = self.position_var.get()
        if position == 'center':
            position = ('center', 'center')
        elif position == 'top':
            position = ('center', 'top')
        elif position == 'bottom':
            position = ('center', 'bottom')
        elif position == 'left':
            position = ('left', 'center')
        elif position == 'right':
            position = ('right', 'center')

        text_config = {
            'fontsize': self.fontsize_var.get(),
            'color': self.color_var.get(),
            'movement': self.movement_var.get(),
            'position': position,
            'opacity': self.opacity_var.get()
        }

        self.result = (video_path, text_content, text_config)
        print(f"Dialog result set: {self.result}")  # Debug print
        self.dialog.destroy()

    def cancel_clicked(self):
        """Handle Cancel button click"""
        self.dialog.destroy()


def main():
    root = tk.Tk()
    app = VideoMergerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()