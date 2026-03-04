from pathlib import Path
from PIL import Image

PANELS_DIR = Path("panels")
OUTPUT = "forest-adventure-episode.gif"

FRAME_DURATION = 1000  # milliseconds per panel
LOOP = 0               # 0 = infinite loop

def main():

    # collect panels matching naming convention
    panels = sorted(PANELS_DIR.glob("panel-*.jpg"))

    if not panels:
        raise SystemExit("No panel images found.")

    print("Panels found:")
    for p in panels:
        print("  ", p.name)

    frames = [Image.open(p) for p in panels]

    # normalize size
    w, h = frames[0].size
    frames = [im.resize((w, h)) for im in frames]

    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION,
        loop=LOOP
    )

    print(f"\nGIF created: {OUTPUT}")


if __name__ == "__main__":
    main()