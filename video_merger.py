import os

os.environ['IMAGEMAGICK_BINARY'] = r'C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe'
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ImageClip
import math
import re
import traceback


class MoviePyProgressLogger:
    def __init__(self, callback):
        self.callback = callback

    def __call__(self, message):
        if self.callback:
            match_percent = re.search(r"(\d+)%", message)
            if match_percent:
                percent = int(match_percent.group(1))
                self.callback(percentage=percent, message=f"Zapisywanie: {percent}%")
            else:
                if "MoviePy - " not in message:
                    self.callback(percentage=None, message=message)

    def iter_bar(self, **kwargs):
        iterable = kwargs.get("t", kwargs.get("iterable", None))
        if iterable is None:
            return iter([])
        try:
            total = len(iterable)
        except TypeError:
            total = None
        for i, item in enumerate(iterable):
            if self.callback and total:
                percent = int((i / total) * 100)
                self.callback(percentage=percent, message=f"Krok {i + 1}/{total}")
            yield item


class VideoMerger:
    def __init__(self):
        self.clips_data = []
        self.current_progress_callback = None

    def add_clip(self, clip_path, texts_data, image_duration=None):
        is_image = clip_path.lower().endswith(('.jpg', '.jpeg', '.png'))
        self.clips_data.append({
            'path': clip_path,
            'is_image': is_image,
            'image_duration': image_duration if is_image else None,
            'texts': texts_data  # List of text configs
        })

    def create_text_clip(self, text_content, config, clip_duration):
        text_start = config.get('start_time', 0)
        text_dur = config.get('duration')

        # If duration is 0 or None, it means full length
        duration = text_dur if text_dur else clip_duration

        if text_start > clip_duration:
            return None  # Text starts after the clip ends

        txt_clip = TextClip(
            text_content,
            fontsize=config.get('fontsize', 50),
            color=config.get('color', 'white'),
            font=config.get('font', 'Arial-Bold')
        ).set_duration(duration).set_start(text_start)

        txt_clip = txt_clip.set_opacity(config.get('opacity', 0.8))

        movement = config.get('movement')
        if movement == 'bounce':
            txt_clip = txt_clip.set_position(self._bounce_position())
        elif movement == 'slide':
            txt_clip = txt_clip.set_position(self._slide_position(duration))
        elif movement == 'float':
            txt_clip = txt_clip.set_position(self._float_position())
        else:  # static
            pos = config.get('position', ('center', 'center'))
            # Convert canvas coordinates to moviepy coordinates if they are absolute
            if isinstance(pos, (list, tuple)) and all(isinstance(i, (int, float)) for i in pos):
                # Assuming canvas size was 320x180 for position selection
                # This might need adjustment if your final video size is known and different
                pass  # Moviepy handles absolute pixel coords fine
            txt_clip = txt_clip.set_position(pos)

        return txt_clip

    def _bounce_position(self):
        return lambda t: ('center', 50 + 30 * abs(2 * (t % 2) - 1))

    def _slide_position(self, duration):
        # Slide across the width of the screen
        return lambda t: ((t / duration) * (self.final_size[0] if hasattr(self, 'final_size') else 1920) - 100,
                          'center')

    def _float_position(self):
        return lambda t: ('center', 100 + 50 * math.sin(2 * math.pi * t / 3))

    def process_clip(self, clip_data):
        try:
            base_clip = None
            clip_path = clip_data['path']

            if clip_data['is_image']:
                clip_duration = clip_data['image_duration']
                base_clip = ImageClip(clip_path).set_duration(clip_duration)
            else:
                base_clip = VideoFileClip(clip_path)
                clip_duration = base_clip.duration

            # Set a standard size for all clips to avoid issues with concatenation
            # Using the size of the first clip as the standard
            if not hasattr(self, 'final_size') or self.final_size is None:
                if base_clip.size is None:
                    raise ValueError(f"Nie można odczytać rozmiaru klipu: {clip_path}")
                self.final_size = base_clip.size
            base_clip = base_clip.resize(self.final_size)

            text_clips = []
            for text_info in clip_data['texts']:
                text_content = text_info.get('text', '').strip()
                if text_content:
                    text_clip = self.create_text_clip(
                        text_content,
                        text_info['config'],
                        clip_duration
                    )
                    if text_clip:
                        text_clips.append(text_clip)

            if not text_clips:
                return base_clip

            final_clip = CompositeVideoClip([base_clip] + text_clips)
            return final_clip

        except Exception as e:
            print(f"Error in process_clip for {clip_data['path']}: {str(e)}")
            traceback.print_exc()
            raise

    def merge_videos(self, output_path, progress_callback=None):
        self.current_progress_callback = progress_callback
        self.final_size = None  # Reset final size for each merge

        if not self.clips_data:
            return False, "No videos or images added to merge!"

        processed_clips = []
        total_clips = len(self.clips_data)

        for i, clip_data in enumerate(self.clips_data):
            if self.current_progress_callback:
                self.current_progress_callback(
                    message=f"Przetwarzanie pliku {i + 1}/{total_clips}: {os.path.basename(clip_data['path'])}")

            if not os.path.exists(clip_data['path']):
                print(f"ERROR: Clip file not found: {clip_data['path']}")
                continue

            try:
                processed_clip = self.process_clip(clip_data)
                processed_clips.append(processed_clip)
            except Exception as e:
                print(f"ERROR processing clip {clip_data['path']}: {str(e)}")
                continue

        if not processed_clips:
            return False, "No clips were successfully processed! Check console for detailed error messages."

        try:
            if self.current_progress_callback:
                self.current_progress_callback(message="Łączenie i konkatenacja klipów...")

            final_video = concatenate_videoclips(processed_clips, method="compose")

            if self.current_progress_callback:
                self.current_progress_callback(message="Rozpoczynanie zapisu wideo...")

            print(f"Writing final video to: {output_path}")
            logger = MoviePyProgressLogger(self.current_progress_callback)

            final_video.write_videofile(
                output_path,
                fps=29,
                codec='libx264',
                audio_codec='aac',
                threads=os.cpu_count(),
                preset='ultrafast',
                verbose=False,
                logger=logger
            )

            for clip in processed_clips:
                if clip:
                    clip.close()
            if final_video:
                final_video.close()

            print("Video merge completed successfully!")
            return True, f"Video successfully created: {output_path}"

        except Exception as e:
            print(f"ERROR during video merging: {str(e)}")
            traceback.print_exc()
            return False, f"Error during video merging: {str(e)}"