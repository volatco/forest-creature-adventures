from pathlib import Path
import math
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageOps
from rembg import remove


def rgba_from_rembg(path: Path) -> Image.Image:
    raw = path.read_bytes()
    cut = remove(raw)
    # Keep this in-memory: rembg returns PNG bytes.
    from io import BytesIO
    return Image.open(BytesIO(cut)).convert("RGBA")


def non_empty_bbox(alpha_img: Image.Image, threshold: int = 8) -> tuple[int, int, int, int]:
    alpha = alpha_img.split()[-1]
    bw = alpha.point(lambda p: 255 if p >= threshold else 0)
    box = bw.getbbox()
    if box is None:
        return (0, 0, alpha_img.width, alpha_img.height)
    return box


def soft_crop(im: Image.Image, box: tuple[int, int, int, int], feather: int = 8) -> Image.Image:
    x1, y1, x2, y2 = box
    part = im.crop((x1, y1, x2, y2)).copy()
    a = part.split()[-1]
    a = a.filter(ImageFilter.GaussianBlur(feather / 2))
    part.putalpha(a)
    return part


def make_background(width: int, height: int) -> Image.Image:
    bg = Image.new("RGB", (width, height), "#b7e8ff")
    d = ImageDraw.Draw(bg)

    for y in range(height):
        t = y / max(1, height - 1)
        r = int(183 * (1 - t) + 129 * t)
        g = int(232 * (1 - t) + 214 * t)
        b = int(255 * (1 - t) + 146 * t)
        d.line([(0, y), (width, y)], fill=(r, g, b))

    horizon = int(height * 0.68)
    d.rectangle((0, horizon, width, height), fill="#78c95f")
    d.rectangle((0, int(height * 0.77), width, height), fill="#5db24f")

    for tx in [90, 240, 420, 620, 840, 1060]:
        d.rectangle((tx, 260, tx + 24, 560), fill="#7b4f2e")
        d.ellipse((tx - 44, 170, tx + 96, 340), fill="#4ea453")
        d.ellipse((tx - 64, 220, tx + 118, 390), fill="#63b45a")

    return bg


def rotate_part(
    canvas: Image.Image,
    part: Image.Image,
    target_pivot_xy: tuple[int, int],
    pivot_ratio: tuple[float, float],
    angle_deg: float,
) -> None:
    pw, ph = part.size
    pivot_local = (int(pw * pivot_ratio[0]), int(ph * pivot_ratio[1]))
    big = Image.new("RGBA", (pw * 3, ph * 3), (0, 0, 0, 0))
    ox, oy = pw, ph
    big.alpha_composite(part, (ox, oy))

    cx = ox + pivot_local[0]
    cy = oy + pivot_local[1]
    rot = big.rotate(
        angle_deg,
        resample=Image.Resampling.BICUBIC,
        expand=True,
        center=(cx, cy),
    )
    rx, ry = rot.size
    x = int(target_pivot_xy[0] - rx / 2)
    y = int(target_pivot_xy[1] - ry / 2)
    canvas.alpha_composite(rot, (x, y))


def main() -> None:
    src = Path("images/stills/character-squirrel.jpg")
    out_dir = Path("output")
    frames_dir = out_dir / "squirrel_dance_v2_frames"
    out_mp4 = out_dir / "squirrel-dance-v2-10s.mp4"
    out_gif = out_dir / "squirrel-dance-v2-10s.gif"

    width, height = 1280, 720
    fps = 24
    seconds = 10
    total = fps * seconds

    out_dir.mkdir(exist_ok=True)
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Cleaner source extraction than simple brightness keying.
    squirrel = rgba_from_rembg(src)
    squirrel = squirrel.crop(non_empty_bbox(squirrel, threshold=5))

    target_h = 340
    scale = target_h / squirrel.height
    squirrel = squirrel.resize((int(squirrel.width * scale), target_h), Image.Resampling.LANCZOS)
    sw, sh = squirrel.size

    def rb(x1: float, y1: float, x2: float, y2: float) -> tuple[int, int, int, int]:
        return (int(sw * x1), int(sh * y1), int(sw * x2), int(sh * y2))

    regions = {
        "head": (rb(0.15, 0.03, 0.73, 0.34), (0.52, 0.85)),
        "arm_l": (rb(0.06, 0.28, 0.43, 0.63), (0.72, 0.16)),
        "arm_r": (rb(0.31, 0.28, 0.73, 0.64), (0.25, 0.15)),
        "leg_l": (rb(0.14, 0.59, 0.44, 0.97), (0.58, 0.12)),
        "leg_r": (rb(0.39, 0.59, 0.76, 0.98), (0.36, 0.12)),
        "tail": (rb(0.55, 0.18, 0.99, 0.83), (0.10, 0.62)),
    }

    parts: dict[str, Image.Image] = {}
    for k, (box, _pivot) in regions.items():
        parts[k] = soft_crop(squirrel, box, feather=6)

    # Torso base with motion part holes
    torso = squirrel.copy()
    erase = Image.new("L", (sw, sh), 0)
    ed = ImageDraw.Draw(erase)
    for box, _ in regions.values():
        ed.rounded_rectangle(box, radius=12, fill=180)
    erase = erase.filter(ImageFilter.GaussianBlur(6))
    a = torso.split()[-1]
    a2 = Image.composite(a, Image.new("L", (sw, sh), 0), erase)
    torso.putalpha(a2)

    bg = make_background(width, height)
    x_start = -sw - 30
    x_end = width + 40
    y_base = int(height * 0.49)

    for i in range(total):
        t = i / (total - 1)
        frame = bg.copy().convert("RGBA")

        x = int(x_start + (x_end - x_start) * t)
        bob = int(16 * math.sin(i * 0.52) + 6 * math.sin(i * 1.07))
        y = y_base + bob

        body_lean = 7.5 * math.sin(i * 0.42)
        head_nod = 10.0 * math.sin(i * 0.58 + 0.4)
        arm_l = 30.0 * math.sin(i * 0.72 + 0.2)
        arm_r = -30.0 * math.sin(i * 0.72 + 0.2)
        leg_l = -18.0 * math.sin(i * 0.72 + 1.0)
        leg_r = 18.0 * math.sin(i * 0.72 + 1.0)
        tail = 24.0 * math.sin(i * 0.47 + 1.1)

        # Ground shadow reacts to bounce.
        shadow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        shadow_w = int(sw * (0.62 - 0.08 * math.sin(i * 0.52)))
        shadow_h = int(sh * 0.12)
        sx = x + sw // 2
        sy = y + sh - 10
        sd.ellipse((sx - shadow_w // 2, sy - shadow_h // 2, sx + shadow_w // 2, sy + shadow_h // 2), fill=(18, 38, 18, 85))
        shadow = shadow.filter(ImageFilter.GaussianBlur(7))
        frame.alpha_composite(shadow)

        torso_rot = torso.rotate(body_lean, resample=Image.Resampling.BICUBIC, expand=True)
        tx = x - (torso_rot.width - sw) // 2
        ty = y - (torso_rot.height - sh) // 2
        frame.alpha_composite(torso_rot, (tx, ty))

        draw_order = [
            ("tail", tail + body_lean * 0.4),
            ("leg_l", leg_l),
            ("leg_r", leg_r),
            ("arm_l", arm_l),
            ("arm_r", arm_r),
            ("head", head_nod + body_lean * 0.35),
        ]
        for name, ang in draw_order:
            box, pivot_ratio = regions[name]
            part = parts[name]
            pw, ph = part.size
            pivot_xy = (
                x + box[0] + int(pw * pivot_ratio[0]),
                y + box[1] + int(ph * pivot_ratio[1]),
            )
            rotate_part(frame, part, pivot_xy, pivot_ratio, ang)

        frame_rgb = frame.convert("RGB")
        # Mild contrast/sat boost to pop the subject.
        frame_rgb = ImageOps.autocontrast(frame_rgb, cutoff=1)
        frame_rgb.save(frames_dir / f"frame-{i:04d}.png", quality=95)

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
