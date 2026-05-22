from __future__ import annotations

import argparse
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build funding-ready MP4 from episode panels.")
    parser.add_argument("--episode-dir", required=True, help="Episode directory containing panel-XX.jpg files.")
    parser.add_argument("--output", default=None, help="Output MP4 path. Defaults to <episode-dir>/output/episode-v2.mp4")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--seconds-per-panel", type=float, default=2.8)
    parser.add_argument("--resolution", default="1280x720")
    return parser.parse_args()


def fit_cover(src: Image.Image, w: int, h: int) -> Image.Image:
    sw, sh = src.size
    scale = max(w / sw, h / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    resized = src.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - w) // 2
    y = (nh - h) // 2
    return resized.crop((x, y, x + w, y + h))


def draw_title_card(w: int, h: int, title: str, subtitle: str) -> Image.Image:
    img = Image.new("RGB", (w, h), (18, 26, 20))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    d.rectangle((0, 0, w, h), fill=(22, 35, 26))
    d.rectangle((34, 34, w - 34, h - 34), outline=(172, 207, 167), width=4)
    d.rectangle((58, 220, w - 58, 360), fill=(245, 239, 215), outline=(0, 0, 0), width=3)
    d.text((88, 255), title, fill=(20, 20, 20), font=font)
    d.text((88, 290), subtitle, fill=(50, 50, 50), font=font)
    d.text((88, 330), "Forest Creature Adventures", fill=(30, 80, 40), font=font)
    return img


def add_lower_third(frame: Image.Image, label: str) -> Image.Image:
    img = frame.copy()
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    w, h = img.size
    box_w = int(w * 0.56)
    d.rounded_rectangle((26, h - 86, 26 + box_w, h - 26), radius=10, fill=(0, 0, 0, 145), outline=(255, 255, 255))
    d.text((42, h - 64), label, fill=(235, 250, 235), font=font)
    return img


def ken_burns_frame(panel: Image.Image, out_w: int, out_h: int, t: float, direction: int) -> Image.Image:
    # Slight zoom from 1.00 to 1.08 over panel duration.
    z = 1.0 + 0.08 * t
    zw, zh = int(out_w / z), int(out_h / z)
    base = fit_cover(panel, out_w, out_h)
    max_x = max(0, out_w - zw)
    max_y = max(0, out_h - zh)
    if direction % 4 == 0:
        x, y = int(max_x * t), int(max_y * t)
    elif direction % 4 == 1:
        x, y = int(max_x * (1.0 - t)), int(max_y * t)
    elif direction % 4 == 2:
        x, y = int(max_x * t), int(max_y * (1.0 - t))
    else:
        x, y = int(max_x * (1.0 - t)), int(max_y * (1.0 - t))
    crop = base.crop((x, y, x + zw, y + zh))
    return crop.resize((out_w, out_h), Image.Resampling.LANCZOS)


def main() -> int:
    args = parse_args()
    episode_dir = Path(args.episode_dir).resolve()
    if not episode_dir.exists():
        raise SystemExit(f"Episode dir not found: {episode_dir}")

    w, h = map(int, args.resolution.lower().split("x"))
    fps = args.fps
    spp = args.seconds_per_panel
    frames_per_panel = max(1, int(fps * spp))

    output_path = Path(args.output).resolve() if args.output else (episode_dir / "output" / "episode-v2.mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    panels = sorted(episode_dir.glob("panel-*.jpg"))
    if not panels:
        raise SystemExit(f"No panel-*.jpg files in {episode_dir}")

    temp_frames = episode_dir / "output" / "_video_frames"
    if temp_frames.exists():
        shutil.rmtree(temp_frames)
    temp_frames.mkdir(parents=True, exist_ok=True)

    frame_index = 0

    title = draw_title_card(w, h, "Episode 001 Preview", "Volatco B at J7 polyForth Bring-up")
    for _ in range(int(fps * 2.0)):
        title.save(temp_frames / f"frame-{frame_index:05d}.png")
        frame_index += 1

    for idx, panel_path in enumerate(panels, start=1):
        panel = Image.open(panel_path).convert("RGB")
        for f in range(frames_per_panel):
            t = f / max(1, frames_per_panel - 1)
            frame = ken_burns_frame(panel, w, h, t, idx)
            frame = add_lower_third(frame, f"Panel {idx:02d}  |  aeonForth mission checkpoint")
            frame.save(temp_frames / f"frame-{frame_index:05d}.png")
            frame_index += 1

        # Brief transition dip.
        for f in range(int(fps * 0.18)):
            alpha = (f + 1) / max(1, int(fps * 0.18))
            dark = Image.new("RGB", (w, h), (0, 0, 0))
            blend = Image.blend(frame, dark, alpha * 0.22)
            blend.save(temp_frames / f"frame-{frame_index:05d}.png")
            frame_index += 1

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(temp_frames / "frame-%05d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        check=True,
    )

    print(f"Created video: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
