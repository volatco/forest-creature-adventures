#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

W, H = 1280, 720
EPISODE_DIR = Path('forest-adventure-series/episodes/episode-001-volatco-b-j7-polyforth')

BACKGROUNDS = [
    Path('images/stories/story-volatco-00.jpg'),
    Path('images/stories/story-volatco-01.jpg'),
    Path('images/stories/story-forth-00.jpg'),
    Path('images/stories/cover-image.jpg'),
    Path('images/intros/IntroVolatco-00.jpg'),
    Path('images/intros/IntroVolatco-01.jpg'),
    Path('images/stories/jez-vev-forth-trick.jpg'),
    Path('images/first-adventures/owl-at-J8.jpg'),
]

CAPTIONS = {
    1: 'MISSION START: Commission VOLATCO-B polyForth path',
    2: 'RISK CHECK: What fails first in the field?',
    3: 'SETUP: VOLATCO-B @ 921600 and status checks',
    4: 'VALIDATION: attach B and confirm ok prompt',
    5: 'CHECKLIST: profiles -> status -> attach B -> ok',
    6: 'STRESS TEST: reset/reconnect and recover ok',
    7: 'RESULT: Repeatable bring-up achieved',
    8: 'HANDOFF: Ready for future Forth program episodes',
}

SPEECH = {
    1: 'Fox: "No stable link, no safe decisions."',
    2: 'Hedgehog: "Can we recover after reset?"',
    3: 'Owl: "Role, baud, then verify."',
    4: 'Owl: "Enter... and we want ok."',
    5: 'Squirrel: "Write it so anyone can run it."',
    6: 'Fox: "Prove it twice, not once."',
    7: 'Team: "Same outcome, two passes."',
    8: 'Owl: "Understand. Repair. Teach."',
}


def fit_crop(img: Image.Image, w: int, h: int) -> Image.Image:
    return ImageOps.fit(img.convert('RGB'), (w, h), method=Image.Resampling.LANCZOS)


def comic_tone(img: Image.Image) -> Image.Image:
    # Boost contrast/color then posterize for comic vibe.
    img = ImageEnhance.Color(img).enhance(1.35)
    img = ImageEnhance.Contrast(img).enhance(1.25)
    img = ImageEnhance.Sharpness(img).enhance(1.5)
    img = ImageOps.posterize(img, 4)

    # Edge ink layer.
    edges = img.convert('L').filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.invert(edges)
    edges = ImageEnhance.Contrast(edges).enhance(2.2)
    ink = Image.merge('RGB', (edges, edges, edges))
    ink = ImageOps.posterize(ink, 3)
    img = Image.blend(img, ink, 0.22)
    return img


def halftone_overlay(w: int, h: int, step: int = 18) -> Image.Image:
    dot = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(dot)
    for y in range(0, h, step):
      for x in range(0, w, step):
        r = 1 + ((x + y) // step) % 3
        d.ellipse((x, y, x + r, y + r), fill=(20, 20, 20, 24))
    return dot


def draw_panel(frame: Image.Image, i: int) -> Image.Image:
    img = frame.convert('RGBA')
    d = ImageDraw.Draw(img)

    # Thick comic border
    d.rectangle((8, 8, W - 8, H - 8), outline=(0, 0, 0, 255), width=12)
    d.rectangle((28, 28, W - 28, H - 28), outline=(255, 255, 255, 180), width=3)

    # Top caption box
    d.rounded_rectangle((40, 38, W - 40, 112), radius=14, fill=(255, 245, 210, 230), outline=(0, 0, 0, 255), width=3)
    d.text((58, 62), CAPTIONS[i], fill=(15, 15, 15, 255))

    # Speech box
    d.rounded_rectangle((70, H - 150, W - 70, H - 58), radius=12, fill=(255, 255, 255, 230), outline=(0, 0, 0, 255), width=3)
    d.text((90, H - 121), SPEECH[i], fill=(10, 10, 10, 255))

    # Tech tag box
    d.rectangle((W - 420, 122, W - 50, 170), fill=(25, 25, 25, 220), outline=(250, 250, 250, 230), width=2)
    d.text((W - 405, 140), f'EP001 PANEL-{i:02d}  VOLATCO-B 921600', fill=(220, 255, 220, 255))

    return img.convert('RGB')


def main() -> None:
    ht = halftone_overlay(W, H)
    for i in range(1, 9):
        bg_path = BACKGROUNDS[i - 1]
        bg = fit_crop(Image.open(bg_path), W, H)
        bg = comic_tone(bg).convert('RGBA')
        bg.alpha_composite(ht)
        out = draw_panel(bg.convert('RGB'), i)
        out.save(EPISODE_DIR / f'panel-{i:02d}.jpg', quality=93)
    print('Generated comic-style preview panels in', EPISODE_DIR)


if __name__ == '__main__':
    main()
