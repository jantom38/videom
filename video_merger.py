import os
os.environ['IMAGEMAGICK_BINARY'] = r'C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe'
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ImageClip
import math

import re

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
        """
        Obsługa paska postępu MoviePy, zgodna z API MoviePy 2.x.
        """
        iterable = kwargs.get("t", kwargs.get("iterable", None))

        if iterable is None:
            # Jeśli nie ma iterable, po prostu zwróć pusty iterator
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
        self.videos = []
        self.text_configs = []
        self.current_progress_callback = None  # Nowy atrybut do przechowywania callbacku postępu

    def add_video(self, video_path, text_content, text_config=None, duration=None):
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

        is_image = video_path.lower().endswith(('.jpg', '.jpeg', '.png'))

        self.videos.append(video_path)
        self.text_configs.append({
            'text': text_content,
            'config': default_config,
            'is_image': is_image,
            'image_duration': duration if is_image else None
        })

    def create_floating_text(self, text_content, config, clip_duration):
        custom_duration = config.get('duration')
        duration = custom_duration if custom_duration is not None else clip_duration
        start_time = config.get('start_time', 0)
        font = config.get('font', 'Arial-Bold')

        txt_clip = TextClip(
            text_content,
            fontsize=config.get('fontsize', 50),
            color=config.get('color', 'white'),
            font=font
        ).set_duration(duration).set_start(start_time)

        txt_clip = txt_clip.set_opacity(config.get('opacity', 0.8))

        movement = config.get('movement')
        if movement == 'bounce':
            txt_clip = txt_clip.set_position(self._bounce_position())
        elif movement == 'slide':
            txt_clip = txt_clip.set_position(self._slide_position(duration))
        elif movement == 'float':
            txt_clip = txt_clip.set_position(self._float_position())
        else:  # static or 'center'
            txt_clip = txt_clip.set_position(config.get('position', ('center', 'center')))

        return txt_clip

    def _bounce_position(self):
        return lambda t: ('center', 50 + 30 * abs(2 * (t % 2) - 1))

    def _slide_position(self, duration):
        return lambda t: (50 + (t / duration) * 500, 'center')

    def _float_position(self):
        return lambda t: ('center', 100 + 50 * math.sin(2 * math.pi * t / 3))

    def process_clip_with_text(self, clip_path, text_data):
        """Process a single video or image clip, adding text if provided."""
        try:
            clip = None
            clip_duration = None

            if text_data.get('is_image', False):
                clip_duration = text_data.get('image_duration', 5)  # Default to 5 seconds for images
                clip = ImageClip(clip_path).set_duration(clip_duration)
            else:
                clip = VideoFileClip(clip_path)
                clip_duration = clip.duration

            text_content = text_data.get('text', '').strip()

            if not text_content:
                return clip

            text_clip = self.create_floating_text(
                text_content,
                text_data['config'],
                clip_duration
            )
            final_clip = CompositeVideoClip([clip, text_clip])

            return final_clip

        except Exception as e:
            print(f"Error in process_clip_with_text for {clip_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def _moviepy_progress_logger(self, message=None, **kwargs):
        """
        Niestandardowy logger dla MoviePy, który wywołuje callback postępu GUI.
        """
        if self.current_progress_callback:
            match_percent = re.search(r'(\d+)%', message)
            if match_percent:
                percentage = int(match_percent.group(1))
                self.current_progress_callback(percentage=percentage, message=f"Zapisywanie: {percentage}%")
            else:
                if "MoviePy - " not in message:
                    self.current_progress_callback(percentage=None, message=message)

    def merge_videos(self, output_path, progress_callback=None):
        self.current_progress_callback = progress_callback  # Zapisz callback na potrzeby loggera

        if not self.videos:
            return False, "No videos or images added to merge!"

        processed_clips = []
        total_clips = len(self.videos)

        for i, (clip_path, text_data) in enumerate(zip(self.videos, self.text_configs)):
            if self.current_progress_callback:
                # To są wiadomości z naszej logiki, nie z MoviePy loggera
                self.current_progress_callback(
                    message=f"Przetwarzanie pliku {i + 1}/{total_clips}: {os.path.basename(clip_path)}")

            if not os.path.exists(clip_path):
                print(f"ERROR: Clip file not found: {clip_path}")
                continue

            try:
                processed_clip = self.process_clip_with_text(clip_path, text_data)
                processed_clips.append(processed_clip)
            except Exception as e:
                print(f"ERROR processing clip {clip_path}: {str(e)}")
                continue

        if not processed_clips:
            return False, "No clips were successfully processed! Check console for detailed error messages."

        try:
            if self.current_progress_callback:
                self.current_progress_callback(message="Łączenie i konkatenacja klipów...")

            # MoviePy może wydrukować logi podczas concatenate_videoclips.
            # Jeśli chcemy przechwycić postęp z tego etapu, potrzebowalibyśmy bardziej złożonego systemu.
            # Na razie skupiamy się na postępie write_videofile.
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
                if clip:  # Upewnij się, że klip istnieje przed zamknięciem
                    clip.close()
            if final_video:  # Upewnij się, że final_video istnieje
                final_video.close()

            print("Video merge completed successfully!")
            return True, f"Video successfully created: {output_path}"

        except Exception as e:
            print(f"ERROR during video merging: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, f"Error during video merging: {str(e)}"