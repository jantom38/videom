# video_merger.py

import os

os.environ['IMAGEMAGICK_BINARY'] = r'C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe'
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ImageClip
import math
import re
import traceback
import data_load  # NOWOŚĆ: Import modułu do ładowania danych


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

    # NOWOŚĆ: Funkcja do rozwiązywania symboli zastępczych
    def _resolve_text(self, text: str, item_no: str) -> str:
        """
        Zamienia wszystkie placeholdery w podanym tekście na realne dane.
        Pozostawia tekst bez zmian, jeśli item_no jest pusty lub żaden symbol nie pasuje.
        """
        if not item_no:
            return text

        # 1. Zbuduj słownik danych (raz – żeby nie wołać do Excela przy każdym symbolu)
        try:
            names = data_load.load_names(item_no)
            data_map = {
                "{INDEKS}": item_no,
                "{NAZWA_PL}": names.get("PL", "Brak nazwy PL"),
                "{NAZWA_EN}": names.get("EN", "Brak nazwy EN"),
                "{OPIS}": data_load.load_description(item_no),
                "{MATERIALY}": data_load.load_materials(item_no),
            }
        except Exception as e:
            print(f"Błąd _resolve_text dla {item_no}: {e}")
            return text  # zostaw oryginał, jeśli nie udało się pobrać danych

        # 2. Podmień *wszystkie* wystąpienia znanych kluczy – bez względu na wielkość liter
        def repl(match):
            key = match.group(0).upper()
            return str(data_map.get(key, match.group(0)))

        pattern = re.compile("|".join(re.escape(k) for k in data_map.keys()), re.IGNORECASE)
        return pattern.sub(repl, text)

    # W pliku video_merger.py

    def create_text_clip(self, text_content, config, clip_duration):
        text_start = config.get('start_time', 0)
        text_dur = config.get('duration')

        duration = text_dur if text_dur else clip_duration

        if text_start > clip_duration:
            return None


        wrap_width = config.get('wrap_width')


        align_raw = config.get('alignment', 'center')
        align_map = {'left': 'west', 'center': 'center', 'right': 'east'}
        align = align_map.get(align_raw.lower(), 'center')

        textclip_kwargs = {
            'txt': text_content,
            'fontsize': config.get('fontsize', 50),
            'color': config.get('color', 'white'),
            'font': config.get('font', 'Arial-Bold'),
            'align': align
        }

        if wrap_width:
            textclip_kwargs['method'] = 'caption'
            textclip_kwargs['size'] = (wrap_width, None)

        txt_clip = TextClip(**textclip_kwargs)

        # --- POCZĄTEK POPRAWIONEJ LOGIKI TŁA ---
        background_color = config.get('bg_color')
        if (background_color and background_color!="None"):
            try:
                # Domyślnie używamy oryginalnej wartości
                rgb_color = background_color

                # Jeśli kolor jest stringiem w formacie hex, konwertujemy go na krotkę RGB
                if isinstance(background_color, str) and background_color.startswith('#'):
                    hex_val = background_color.lstrip('#')
                    # Sprawdzamy, czy ma 6 znaków (RRGGBB)
                    if len(hex_val) == 6:
                        # Konwertujemy pary hex na liczby całkowite
                        rgb_color = tuple(int(hex_val[i:i + 2], 16) for i in (0, 2, 4))
                    else:
                        print(f"Ostrzeżenie: Nieprawidłowy format koloru hex: {background_color}. Oczekiwano #RRGGBB.")

                # Ustawiamy tło, używając skonwertowanego koloru RGB
                txt_clip = txt_clip.on_color(
                    size=(txt_clip.w + 20, txt_clip.h + 20),  # Dodaj trochę paddingu
                    color=rgb_color,  # Przekazujemy krotkę RGB
                    pos=('center', 'center'),
                    col_opacity=config.get('background_opacity', 1.0)
                )
            except Exception as e:
                # Lepsze logowanie błędów
                print(f"Ostrzeżenie: Nie udało się ustawić koloru tła '{background_color}'. Błąd: {e}")
                traceback.print_exc()
        # --- KONIEC POPRAWIONEJ LOGIKI TŁA ---

        txt_clip = txt_clip.set_duration(duration).set_start(text_start)
        txt_clip = txt_clip.set_opacity(config.get('opacity', 0.8))

        movement = config.get('movement')
        if movement == 'static':
            pos = config.get('position', (0.5, 0.5))

            if (isinstance(pos, (tuple, list)) and len(pos) == 2 and
                    all(isinstance(p, (int, float)) for p in pos)):

                if 0 <= pos[0] <= 1 and 0 <= pos[1] <= 1:
                    x = pos[0] * self.final_size[0]
                    y = pos[1] * self.final_size[1]

                    alignment = config.get('alignment', 'center')
                    if alignment == 'left':
                        y -= txt_clip.h / 2
                    elif alignment == 'right':
                        x -= txt_clip.w
                        y -= txt_clip.h / 2
                    else:  # center
                        x -= txt_clip.w / 2
                        y -= txt_clip.h / 2

                    pos = (x, y)

            txt_clip = txt_clip.set_position(pos)

        return txt_clip

    def _bounce_position(self):
        return lambda t: ('center', 50 + 30 * abs(2 * (t % 2) - 1))

    def _slide_position(self, duration):
        return lambda t: ((t / duration) * (self.final_size[0] if hasattr(self, 'final_size') else 1920) - 100,
                          'center')

    def _float_position(self):
        return lambda t: ('center', 100 + 50 * math.sin(2 * math.pi * t / 3))

    # ZMIANA: process_clip przyjmuje teraz item_no do rozwiązywania symboli
    def process_clip(self, clip_data, item_no):
        try:
            base_clip = None
            clip_path = clip_data['path']

            if clip_data['is_image']:
                clip_duration = clip_data['image_duration']
                base_clip = ImageClip(clip_path).set_duration(clip_duration)
            else:
                base_clip = VideoFileClip(clip_path)
                clip_duration = base_clip.duration

            if not hasattr(self, 'final_size') or self.final_size is None:
                if base_clip.size is None:
                    raise ValueError(f"Nie można odczytać rozmiaru klipu: {clip_path}")
                self.final_size = base_clip.size
            base_clip = base_clip.resize(self.final_size)

            text_clips = []
            for text_info in clip_data['texts']:
                # ZMIANA: Rozwiązujemy symbol zastępczy przed utworzeniem klipu tekstowego
                raw_text = text_info.get('text', '').strip()
                resolved_text = self._resolve_text(raw_text, item_no)

                if resolved_text:
                    text_clip = self.create_text_clip(
                        resolved_text,
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

    # ZMIANA: merge_videos przyjmuje teraz item_no
    def merge_videos(self, output_path, item_no, progress_callback=None):
        self.current_progress_callback = progress_callback
        self.final_size = None

        if not self.clips_data:
            return False, "No videos or images added to merge!"

        if not item_no and any('{' in t['text'] for c in self.clips_data for t in c['texts']):
            print(
                "OSTRZEŻENIE: Wykryto symbole zastępcze, ale nie podano numeru indeksu produktu. Symbole nie zostaną podmienione.")

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
                # ZMIANA: Przekazujemy item_no do process_clip
                processed_clip = self.process_clip(clip_data, item_no)
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