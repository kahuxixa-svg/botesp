"""Original, reproducible cartoon scenes for the portrait idle screen.

These drawings are independent of the unchanged Troko GIFs. Pillow is only a
build-time dependency; the device uses its existing bounded GIF decoder.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'xiaozhi-esp32/main/boards/lilygo/troko-t-display-s3/assets/idle'
SIZE = (160, 256)
FRAMES = 96
FRAME_MS = 80
WHITE = '#e8fbff'
CYAN = '#58dfea'
GOLD = '#ffc56a'
PINK = '#fc83b0'
BLUE = '#658cff'


class Drawing:
    def __init__(self):
        self.image = Image.new('RGB', (320, 512), 'black')
        self.draw = ImageDraw.Draw(self.image)

    def ellipse(self, box, color, outline=None, width=1):
        self.draw.ellipse(tuple(round(v * 2) for v in box), fill=color,
                          outline=outline, width=width * 2)

    def line(self, points, color, width=2):
        self.draw.line([(round(x * 2), round(y * 2)) for x, y in points],
                       fill=color, width=width * 2, joint='curve')

    def polygon(self, points, color):
        self.draw.polygon([(round(x * 2), round(y * 2)) for x, y in points], fill=color)

    def eyes(self, t, target=None, joy=0, drowsy=0, surprise=0,
             center=(80, 54), scale=1, background='black'):
        """Aim solid white eyes using their position, shape and eyelids only."""
        cx, cy = center
        target_x, target_y = target if target is not None else center
        gaze_x = max(-8, min(8, (target_x - cx) / 6)) * scale
        gaze_y = max(-7, min(9, (target_y - cy) / 14)) * scale
        blink_phase = (t * 2 + 0.25) % 1
        blink = max(0, 1 - abs(blink_phase - 0.94) / 0.055)
        closure = max(blink, drowsy)
        for side in (-1, 1):
            x = cx + side * 23 * scale + gaze_x
            y = cy + gaze_y + 1.5 * scale * math.sin(t * 4 * math.pi)
            rx = 13 * scale
            ry = max(2, (16 + 3 * surprise - 5 * joy) * (1 - closure)) * scale
            if closure > 0.85:
                # Resting lids follow a shallow curve; happy lids arch upwards.
                points = [(x + rx * u, y + (3 if drowsy > 0.5 else -5) *
                           (1 - u * u) * scale) for u in [i / 8 for i in range(-8, 9)]]
                self.line(points, WHITE, max(1, round(3 * scale)))
                continue
            self.ellipse((x - rx, y - ry, x + rx, y + ry), WHITE)
            if joy > 0.15:
                # Lift the lower eyelid into a smiling crescent as joy grows.
                cut_y = y + ry * (1.15 - 1.65 * joy)
                self.ellipse((x - rx * 1.2, cut_y, x + rx * 1.2,
                              cut_y + ry * 2.5), background)
        if joy > 0.55 and scale >= 0.8:
            for side in (-1, 1):
                x = cx + side * 38 + gaze_x
                self.line([(x - 3, cy + 23), (x + 2, cy + 24)], PINK, 2)

    def star(self, x, y, r, color):
        self.line([(x - r, y), (x + r, y)], color, 1)
        self.line([(x, y - r), (x, y + r)], color, 1)

    def finish(self):
        return self.image.resize(SIZE, Image.Resampling.LANCZOS)


def dog_scene(t):
    d = Drawing()
    phase = t * 2 * math.pi
    ball_x = 80 + 58 * math.sin(phase)
    ball_y = 205 - 62 * abs(math.cos(phase * 2))
    d.line([(16, 229), (144, 229)], '#20414a', 1)
    x = 58 + 29 * math.sin(phase - 0.55)
    y = 199 - 4 * abs(math.sin(phase * 6))
    catch = max(0, 1 - abs(ball_x - (x + 29)) / 43)
    # Watch the puppy's head and the ball, and smile when it catches up.
    d.eyes(t, target=(0.7 * (x + 27) + 0.3 * ball_x,
                      0.7 * (y - 25) + 0.3 * ball_y), joy=0.25 + 0.7 * catch)
    # Wagging tail, running legs, floppy ear and bright collar.
    d.line([(x - 20, y - 4), (x - 29, y - 14),
            (x - 33, y - 26 + 8 * math.sin(phase * 8))], GOLD, 5)
    for side in (-1, 1):
        step = 6 * math.sin(phase * 6 + side * math.pi / 2)
        d.line([(x + side * 13, y + 4), (x + side * 13 + step, y + 24)], GOLD, 6)
    d.ellipse((x - 24, y - 14, x + 21, y + 12), GOLD)
    d.ellipse((x + 7, y - 36, x + 38, y - 5), GOLD)
    d.ellipse((x + 5, y - 34, x + 16, y - 6), '#b87842')
    d.ellipse((x + 29, y - 23, x + 44, y - 9), WHITE)
    d.ellipse((x + 38, y - 25, x + 44, y - 18), '#161e31')
    d.ellipse((x + 25, y - 31, x + 29, y - 26), '#161e31')
    d.line([(x + 14, y - 6), (x + 30, y - 5)], CYAN, 3)
    d.ellipse((ball_x - 9, ball_y - 9, ball_x + 9, ball_y + 9), PINK)
    d.line([(ball_x - 6, ball_y - 5), (ball_x + 5, ball_y + 6)], WHITE, 2)
    if t > 0.75:
        d.star(28, 106, 4, GOLD)
        d.star(133, 99, 3, PINK)
    return d.finish()


def rocket_scene(t):
    d = Drawing()
    phase = t * 2 * math.pi
    for i in range(17):
        x = 9 + (i * 47) % 144
        y = 10 + ((i * 37 + t * 472) % 236)
        d.star(x, y, 1 + i % 3, '#42617c' if i % 2 else WHITE)
    x, y = 80 + 18 * math.sin(phase), 154 + 23 * math.cos(phase)
    # The character is the pilot: its only pair of eyes lives inside the cabin.
    excitement = (1 - math.cos(phase)) / 2
    d.ellipse((15, 222, 59, 235), '#142c49')
    d.ellipse((112, 83, 143, 114), BLUE)
    d.line([(105, 105), (148, 91)], CYAN, 2)
    d.polygon([(x - 11, y + 35), (x, y + 70 + 7 * math.sin(phase * 12)),
               (x + 11, y + 35)], GOLD)
    d.polygon([(x - 6, y + 35), (x, y + 56), (x + 6, y + 35)], PINK)
    d.polygon([(x - 17, y + 2), (x - 31, y + 36), (x - 12, y + 28)], CYAN)
    d.polygon([(x + 17, y + 2), (x + 31, y + 36), (x + 12, y + 28)], CYAN)
    d.ellipse((x - 20, y - 46, x + 20, y + 37), WHITE)
    d.polygon([(x - 17, y - 26), (x, y - 58), (x + 17, y - 26)], PINK)
    d.ellipse((x - 15, y - 17, x + 15, y + 15), '#132338', CYAN, 2)
    d.eyes(t, target=(x + 15 * math.sin(phase), y - 85),
           joy=0.3 * excitement, center=(x, y - 2), scale=0.25,
           background='#132338')
    return d.finish()


def aquarium_scene(t):
    d = Drawing()
    p = 2 * math.pi * t
    # Follow the gold fish and smile as it turns back toward the others.
    d.eyes(t, target=(80 + 43 * math.sin(p), 123 + 7 * math.cos(p * 2)),
           joy=0.18 + 0.65 * abs(math.sin(p)) ** 6)
    d.line([(13, 231), (147, 231)], '#20414a', 1)
    for i in range(4):
        x = 20 + i * 39
        d.line([(x, 230), (x - 4 + 3 * math.sin(p + i), 211),
                (x + 3 * math.cos(p + i), 195 - i % 2 * 14)], '#39b58c', 3)
    for i in range(7):
        x, y = 12 + i * 22, 227 - (t * 146 + i * 31) % 130
        d.ellipse((x - 2, y - 2, x + 2, y + 2), None, '#39717c')
    for i, color in enumerate((GOLD, CYAN, PINK)):
        x = 80 + 43 * math.sin(p + i * 2)
        y = 123 + 32 * i + 7 * math.cos(p * 2 + i)
        direction = 1 if math.cos(p + i * 2) >= 0 else -1
        d.polygon([(x - direction * 14, y), (x - direction * 25, y - 10),
                   (x - direction * 25, y + 10)], color)
        d.ellipse((x - 16, y - 10, x + 16, y + 10), color)
        d.ellipse((x + direction * 9 - 2, y - 4, x + direction * 9 + 2, y), '#102031')
    return d.finish()


def juggling_scene(t):
    d = Drawing()
    p = 2 * math.pi * t
    balls = []
    for i, color in enumerate((CYAN, PINK, GOLD)):
        phase = (t * 2 + i / 3) % 1
        balls.append((39 + 82 * phase, 204 - 91 * math.sin(phase * math.pi), color))
    # Follow whichever ball is highest, with a delighted squint at each catch.
    highest = min(balls, key=lambda ball: ball[1])
    catch = max(abs(2 * ((t * 2 + i / 3) % 1) - 1) for i in range(3))
    d.eyes(t, target=highest[:2], joy=0.15 + 0.65 * catch ** 8,
           surprise=0.35 * (1 - catch))
    for x, shift in ((39, 0), (121, math.pi)):
        y = 211 + 5 * math.sin(p * 4 + shift)
        d.line([(x - 11, y - 5), (x, y), (x + 11, y - 5)], WHITE, 4)
    for x, y, color in balls:
        d.ellipse((x - 9, y - 9, x + 9, y + 9), color)
        d.ellipse((x - 4, y - 5, x - 1, y - 2), WHITE)
    for i in range(3):
        d.star(38 + i * 42, 91 + 4 * math.sin(p + i), 3, BLUE)
    return d.finish()


def sleep_scene(t):
    d = Drawing()
    p = 2 * math.pi * t
    # Look down at the puppy, nod off together, then gently open the eyes again.
    drowsy = (0.5 - 0.5 * math.cos(p)) ** 0.55
    d.eyes(t, target=(65, 181), joy=0.3 * (1 - drowsy), drowsy=drowsy)
    d.ellipse((42, 160, 119, 223), '#304168')
    d.ellipse((47, 156, 114, 202), BLUE)
    # A curled-up puppy on a pillow, breathing quietly.
    shift = 2 * math.sin(p * 2)
    d.ellipse((54, 170 + shift, 107, 202 + shift), GOLD)
    d.ellipse((47, 168 + shift, 78, 195 + shift), GOLD)
    d.ellipse((47, 169 + shift, 56, 190 + shift), '#b87842')
    d.line([(61, 179 + shift), (65, 182 + shift), (70, 179 + shift)], '#161e31', 2)
    d.line([(96, 180 + shift), (87, 181 + shift), (85, 190 + shift)], '#b87842', 3)
    for i in range(3):
        z = (t + i / 3) % 1
        x, y, s = 97 + 26 * z, 155 - 53 * z, 4 + 3 * z
        d.line([(x, y), (x + s, y), (x, y + s), (x + s, y + s)], CYAN, 1)
    d.ellipse((20, 91, 42, 113), GOLD)
    d.ellipse((28, 87, 47, 107), 'black')
    for x, y in ((130, 115), (37, 142), (119, 88)):
        d.star(x, y, 2 + int(t * 4) % 2, WHITE)
    return d.finish()


SCENES = {'idle_dog': dog_scene, 'idle_rocket': rocket_scene,
          'idle_fish': aquarium_scene, 'idle_juggle': juggling_scene, 'idle_sleep': sleep_scene}


def generate():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # One fixed palette for every full frame avoids flashing/dithered backgrounds.
    all_colors = ['#000000', WHITE, CYAN, GOLD, PINK, BLUE, '#20414a', '#b87842',
                  '#161e31', '#42617c', '#142c49', '#132338', '#39b58c', '#39717c',
                  '#102031', '#304168']
    palette = [int(c[j:j+2], 16) for c in all_colors for j in (1, 3, 5)]
    reference = Image.new('P', (1, 1))
    reference.putpalette(palette + [0] * (768 - len(palette)))
    previews = []
    for name, draw in SCENES.items():
        frames = [draw(n / FRAMES).quantize(palette=reference, dither=Image.Dither.NONE)
                  for n in range(FRAMES)]
        path = OUTPUT / f'{name}.gif'
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=FRAME_MS,
                       loop=0, disposal=2, optimize=False)
        previews.append(frames[24].convert('RGB'))
        print(f'{name}: {FRAMES} frames, {path.stat().st_size} bytes')
    sheet = Image.new('RGB', (SIZE[0] * len(previews), SIZE[1]), 'black')
    for i, preview in enumerate(previews):
        sheet.paste(preview, (SIZE[0] * i, 0))
    (ROOT / '.local').mkdir(exist_ok=True)
    sheet.save(ROOT / '.local/idle-scenes-preview.png')


if __name__ == '__main__':
    generate()
