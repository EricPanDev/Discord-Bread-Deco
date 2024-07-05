import os
os.makedirs("processing", exist_ok=True)

from PIL import Image, ImageDraw

def process_gif(input_path, overlay_path, output_path, output_frame_delay=500, target_duration=3500):
    def closest_factor(duration, factors):
        return min(factors, key=lambda x: abs(x - duration))

    def create_circular_mask(size):
        mask = Image.new('L', size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0) + size, fill=255)
        return mask

    def apply_circular_mask(image):
        result = Image.new('RGBA', image.size)
        result.paste(image, (0, 0), create_circular_mask(image.size))
        return result

    def format_gif(img):
        total_duration = 0
        frames = []
        frame_duration = img.info['duration']
        factors = [1,2,4,5,10,20, 25, 50, 100, 125, 250, 500]
        chosen_factor = closest_factor(frame_duration, factors)

        while True:
            try:
                frame = img.copy()
                frame = frame.resize((240, 240), Image.Resampling.LANCZOS)
                frame = apply_circular_mask(frame.convert("RGBA"))
                new_frame = Image.new('RGBA', (288, 288), (255, 255, 255, 0))
                position = ((new_frame.width - frame.width) // 2, (new_frame.height - frame.height) // 2)
                new_frame.paste(frame, position, frame)
                frames.append(new_frame)
                img.seek(img.tell() + 1)
                total_duration += chosen_factor
            except EOFError:
                break

        index = 0
        target_duration = output_frame_delay * 7
        while total_duration < target_duration:
            frames.append(frames[index % len(frames)].copy())
            total_duration += chosen_factor
            index += 1

        return frames, chosen_factor

    def duplicate_frames(img, duplicate_count):
        frames = []
        while True:
            try:
                frame = img.copy()
                for _ in range(duplicate_count):
                    frames.append(frame.copy())
                img.seek(img.tell() + 1)
            except EOFError:
                break
        return frames

    def trim_gif(frames, target_duration):
        total_duration = 0
        trimmed_frames = []
        for frame in frames:
            duration = frame.info.get('duration', 100)
            if total_duration + duration > target_duration:
                break
            trimmed_frames.append(frame.copy())
            total_duration += duration
        return trimmed_frames

    with Image.open(input_path) as input_gif:
        formatted_frames, chosen_factor = format_gif(input_gif)

        with Image.open(overlay_path) as overlay_gif:
            duplicate_count = round(output_frame_delay / chosen_factor)
            overlay_frames = duplicate_frames(overlay_gif, duplicate_count)

        input_frames = [frame.copy().convert('RGBA') for frame in formatted_frames]
        overlay_frames = [frame.copy().convert('RGBA') for frame in overlay_frames]

        output_frames = []
        for i, frame in enumerate(input_frames):
            overlay_index = i % len(overlay_frames)
            overlay_frame = overlay_frames[overlay_index]
            overlay_frame = overlay_frame.resize((288, 288), Image.Resampling.LANCZOS)
            combined_frame = frame.copy()
            position = ((combined_frame.width - overlay_frame.width) // 2, (combined_frame.height - overlay_frame.height) // 2)
            combined_frame.paste(overlay_frame, position, overlay_frame)
            output_frames.append(combined_frame)

        trimmed_frames = trim_gif(output_frames, target_duration)
        first_frame_duration = input_gif.info['duration']
        trimmed_frames[0].save(
            output_path,
            save_all=True,
            append_images=trimmed_frames[1:],
            duration=[first_frame_duration] + [input_gif.info['duration']] * (len(trimmed_frames) - 1),
            loop=0,
            disposal=2
        )

process_gif(
    input_path='source/basketball-slam-dunk.gif', # the gif you want
    overlay_path='source/overlay.gif', # dont touch this
    output_path='output.gif' # where you want it save to
)
