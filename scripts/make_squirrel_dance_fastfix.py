from io import BytesIO
from pathlib import Path
import math
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFilter
from rembg import remove


def cutout(path: Path) -> Image.Image:
    rgba = Image.open(BytesIO(remove(path.read_bytes()))).convert("RGBA")
    alpha = rgba.split()[-1]
    box = alpha.point(lambda p: 255 if p > 6 else 0).getbbox()
    if box:
        rgba = rgba.crop(box)
    return rgba


def make_bg(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), "#c8ecff")
    d = ImageDraw.Draw(img)

    for y in range(h):
        t = y / max(1, h - 1)
        r = int(200 * (1 - t) + 130 * t)
        g = int(236 * (1 - t) + 214 * t)
        b = int(255 * (1 - t) + 150 * t)
        d.line([(0, y), (w, y)], fill=(r, g, b))

    horizon = int(h * 0.68)
    d.rectangle((0, horizon, w, h), fill="#74c85f")
    d.rectangle((0, int(h * 0.78), w, h), fill="#5aae4d")

    for x in [90, 230, 380, 560, 760, 960, 1140]:
        d.rectangle((x, 250, x + 22, 560), fill="#775031")
        d.ellipse((x - 42, 170, x + 90, 336), fill="#4ca052")
        d.ellipse((x - 58, 215, x + 110, 378), fill="#60b35a")

    return img.filter(ImageFilter.GaussianBlur(0.7))


def main() -> None:
    src = Path("images/stills/character-squirrel.jpg")
    out_dir = Path("output")
    frames_dir = out_dir / "squirrel_dance_fastfix_frames"
    out_mp4 = out_dir / "squirrel-dance-grounded-10s.mp4"
    out_gif = out_dir / "squirrel-dance-grounded-10s.gif"

    w, h = 1280, 720
    fps = 24
    seconds = 10
    n = fps * seconds

    out_dir.mkdir(exist_ok=True)
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    squirrel = cutout(src)
    target_h = 320
    scale = target_h / squirrel.height
    squirrel = squirrel.resize((int(squirrel.width * scale), target_h), Image.Resampling.LANCZOS)
    sw, sh = squirrel.size

    bg = make_bg(w, h).convert("RGBA")
    cx = w // 2
    x_amp = int(w * 0.34)
    y_base = int(h * 0.54)

    prev_pos = None
    for i in range(n):
        # Loop-perfect cycle.
        theta = (2 * math.pi * i) / n
        frame = bg.copy()

        # Grounded sideways movement.
        x = int(cx + x_amp * math.sin(theta))
        step_phase = (i % 24) / 24.0
        # Keep feet planted most of the cycle; only small lift during swing.
        if step_phase < 0.65:
            lift = 0.0
        else:
            t = (step_phase - 0.65) / 0.35
            lift = 7.0 * (1.0 - (2.0 * t - 1.0) ** 2)
        y = int(y_base - lift + 2.0 * math.sin(2 * theta))
        tilt = 3.5 * math.sin(4 * theta)
        squash = 1.0 + 0.018 * math.sin(4 * theta + math.pi / 2)

        # Mild motion blur trail from previous frame (subtle).
        if prev_pos is not None:
            px, py, pt = prev_pos
            ghost = squirrel.rotate(pt, resample=Image.Resampling.BICUBIC, expand=True)
            ghost = ghost.resize(
                (max(1, int(ghost.width * 0.98)), max(1, int(ghost.height * 0.98))),
                Image.Resampling.LANCZOS,
            )
            gm = ghost.split()[-1].point(lambda a: int(a * 0.14))
            ghost.putalpha(gm)
            frame.alpha_composite(ghost, (px - ghost.width // 2, py - ghost.height // 2))

        # Ground shadow.
        shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        shadow_w = int(sw * (0.64 - 0.02 * math.sin(4 * theta)))
        shadow_h = int(sh * 0.11)
        sx = x
        sy = y + sh // 2 + 28
        sd.ellipse(
            (sx - shadow_w // 2, sy - shadow_h // 2, sx + shadow_w // 2, sy + shadow_h // 2),
            fill=(20, 40, 20, 110),
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(7))
        frame.alpha_composite(shadow)

        # Main character.
        sw2 = max(1, int(sw * (1.0 / squash)))
        sh2 = max(1, int(sh * squash))
        dancer = squirrel.resize((sw2, sh2), Image.Resampling.LANCZOS)
        dancer = dancer.rotate(tilt, resample=Image.Resampling.BICUBIC, expand=True)
        px = x - dancer.width // 2
        py = y - dancer.height // 2
        frame.alpha_composite(dancer, (px, py))

        prev_pos = (x, y, tilt)
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
