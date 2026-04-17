from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math
import subprocess
import shutil


def make_alpha_from_light_background(img: Image.Image) -> Image.Image:
    """Treat near-white pixels as transparent to isolate the character."""
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = pixels[x, y]
            brightness = (r + g + b) / 3
            # Soft matte for very bright backgrounds.
            if brightness > 248:
                a = 0
            elif brightness > 232:
                a = int(max(0, 255 - (brightness - 232) * 16))
            else:
                a = 255
            pixels[x, y] = (r, g, b, a)
    return rgba


def make_background(width: int, height: int) -> Image.Image:
    bg = Image.new("RGB", (width, height), "#d7f1ff")
    draw = ImageDraw.Draw(bg)

    # Sky gradient
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(215 * (1 - t) + 175 * t)
        g = int(241 * (1 - t) + 232 * t)
        b = int(255 * (1 - t) + 170 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Ground layers
    draw.rectangle([(0, int(height * 0.68)), (width, height)], fill="#6fbf5f")
    draw.rectangle([(0, int(height * 0.75)), (width, height)], fill="#58a84f")

    # Simple trees for depth
    for tx in [120, 330, 560, 840, 1090]:
        draw.rectangle([(tx, 240), (tx + 28, 540)], fill="#7a5230")
        draw.ellipse([(tx - 50, 160), (tx + 110, 340)], fill="#4e9d4f")
        draw.ellipse([(tx - 75, 210), (tx + 135, 380)], fill="#5cab57")

    return bg


def find_character_bbox(img: Image.Image, threshold: int = 245) -> tuple[int, int, int, int]:
    rgb = img.convert("RGB")
    pix = rgb.load()
    w, h = rgb.size
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            r, g, b = pix[x, y]
            if (r + g + b) / 3 < threshold:
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
    return (minx, miny, maxx + 1, maxy + 1)


def make_soft_rect_mask(size: tuple[int, int], feather: int = 10) -> Image.Image:
    w, h = size
    m = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(m)
    draw.rectangle((0, 0, w, h), fill=255)
    if feather > 0:
        m = m.filter(ImageFilter.GaussianBlur(feather))
    return m


def extract_part(character: Image.Image, box: tuple[int, int, int, int], feather: int = 8) -> Image.Image:
    x1, y1, x2, y2 = box
    part = character.crop((x1, y1, x2, y2)).copy()
    mask = make_soft_rect_mask(part.size, feather=feather)
    part.putalpha(mask)
    return part


def place_rotated(
    canvas: Image.Image,
    part_img: Image.Image,
    pivot_on_canvas: tuple[int, int],
    pivot_in_part: tuple[int, int],
    angle_deg: float,
) -> None:
    px, py = pivot_in_part
    w, h = part_img.size
    big = Image.new("RGBA", (w * 3, h * 3), (0, 0, 0, 0))
    ox = w
    oy = h
    big.alpha_composite(part_img, (ox, oy))

    cx = ox + px
    cy = oy + py
    rotated = big.rotate(
        angle_deg,
        resample=Image.Resampling.BICUBIC,
        expand=True,
        center=(cx, cy),
    )

    rw, rh = rotated.size
    tx = int(pivot_on_canvas[0] - rw / 2)
    ty = int(pivot_on_canvas[1] - rh / 2)
    canvas.alpha_composite(rotated, (tx, ty))


def main() -> None:
    source = Path("images/stills/character-squirrel.jpg")
    out_dir = Path("output")
    frames_dir = out_dir / "squirrel_dance_limb_rig_frames"
    out_mp4 = out_dir / "squirrel-dance-limb-rig-10s.mp4"
    out_gif = out_dir / "squirrel-dance-limb-rig-10s.gif"

    width, height = 1280, 720
    fps = 24
    seconds = 10
    total_frames = fps * seconds

    out_dir.mkdir(exist_ok=True)
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    squirrel_full = Image.open(source)
    squirrel_full = make_alpha_from_light_background(squirrel_full)

    target_h = 320
    scale = target_h / squirrel_full.height
    squirrel_full = squirrel_full.resize(
        (int(squirrel_full.width * scale), target_h),
        Image.Resampling.LANCZOS,
    )

    bbox = find_character_bbox(squirrel_full)
    squirrel = squirrel_full.crop(bbox)
    sw, sh = squirrel.size

    def rb(x1: float, y1: float, x2: float, y2: float) -> tuple[int, int, int, int]:
        return (
            int(sw * x1),
            int(sh * y1),
            int(sw * x2),
            int(sh * y2),
        )

    # Approximate limb regions (relative to detected squirrel bounds).
    parts = {
        "head": {"box": rb(0.16, 0.02, 0.74, 0.34), "pivot": (0.52, 0.84)},
        "arm_l": {"box": rb(0.08, 0.30, 0.44, 0.64), "pivot": (0.72, 0.18)},
        "arm_r": {"box": rb(0.32, 0.30, 0.74, 0.66), "pivot": (0.26, 0.18)},
        "leg_l": {"box": rb(0.14, 0.60, 0.44, 0.98), "pivot": (0.58, 0.12)},
        "leg_r": {"box": rb(0.40, 0.60, 0.76, 0.98), "pivot": (0.36, 0.12)},
        "tail": {"box": rb(0.56, 0.18, 0.98, 0.82), "pivot": (0.08, 0.64)},
    }

    part_images: dict[str, Image.Image] = {}
    for name, spec in parts.items():
        part_images[name] = extract_part(squirrel, spec["box"], feather=7)

    # Build torso base by punching out moving part areas.
    torso = squirrel.copy()
    erase = Image.new("L", (sw, sh), 0)
    edraw = ImageDraw.Draw(erase)
    for spec in parts.values():
        x1, y1, x2, y2 = spec["box"]
        edraw.rectangle((x1, y1, x2, y2), fill=200)
    erase = erase.filter(ImageFilter.GaussianBlur(6))
    alpha = torso.getchannel("A")
    alpha = Image.composite(alpha, Image.new("L", (sw, sh), 0), erase)
    torso.putalpha(alpha)

    bg = make_background(width, height)

    x_start = -sw - 40
    x_end = width + 40
    y_base = int(height * 0.50)

    for i in range(total_frames):
        t = i / (total_frames - 1)
        frame = bg.copy().convert("RGBA")

        x = int(x_start + (x_end - x_start) * t)
        bob = int(16 * math.sin(i * 0.52))
        y = y_base + bob
        body_lean = 6.0 * math.sin(i * 0.42)

        arm_l = 24.0 * math.sin(i * 0.65)
        arm_r = -24.0 * math.sin(i * 0.65)
        leg_l = -16.0 * math.sin(i * 0.65 + 0.8)
        leg_r = 16.0 * math.sin(i * 0.65 + 0.8)
        head_nod = 8.0 * math.sin(i * 0.55 + 0.3)
        tail_swing = 20.0 * math.sin(i * 0.45 + 1.2)

        # Shadow under character.
        shadow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        shadow_w = int(sw * 0.58)
        shadow_h = int(sh * 0.12)
        sx = x + sw // 2
        sy = y + sh - 10
        sdraw.ellipse(
            [(sx - shadow_w // 2, sy - shadow_h // 2), (sx + shadow_w // 2, sy + shadow_h // 2)],
            fill=(20, 40, 20, 85),
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(6))
        frame.alpha_composite(shadow)

        # Place torso first with slight body lean.
        torso_rot = torso.rotate(body_lean, resample=Image.Resampling.BICUBIC, expand=True)
        tx = x - (torso_rot.width - sw) // 2
        ty = y - (torso_rot.height - sh) // 2
        frame.alpha_composite(torso_rot, (tx, ty))

        # Limb placement around torso anchor.
        for name, angle in [
            ("tail", tail_swing + body_lean * 0.5),
            ("leg_l", leg_l),
            ("leg_r", leg_r),
            ("arm_l", arm_l),
            ("arm_r", arm_r),
            ("head", head_nod + body_lean * 0.4),
        ]:
            spec = parts[name]
            box = spec["box"]
            pivot_ratio = spec["pivot"]
            part_img = part_images[name]
            pw, ph = part_img.size
            pivot_in_part = (int(pw * pivot_ratio[0]), int(ph * pivot_ratio[1]))
            pivot_on_canvas = (
                x + box[0] + pivot_in_part[0],
                y + box[1] + pivot_in_part[1],
            )
            place_rotated(frame, part_img, pivot_on_canvas, pivot_in_part, angle)

        frame.convert("RGB").save(frames_dir / f"frame-{i:04d}.png", quality=95)

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(frames_dir / "frame-%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(out_mp4),
        ],
        check=True,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(out_mp4),
            "-vf",
            "fps=12,scale=960:-1:flags=lanczos",
            str(out_gif),
        ],
        check=True,
    )

    print(f"Created: {out_mp4}")
    print(f"Created: {out_gif}")


if __name__ == "__main__":
    main()
