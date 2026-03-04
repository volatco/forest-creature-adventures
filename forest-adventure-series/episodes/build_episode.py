from pathlib import Path
from PIL import Image

# --------------------------------------------------
# Configuration
# --------------------------------------------------

PANELS_DIR = Path("panels")
OUTPUT_DIR = Path("output")

GIF_NAME = "episode.gif"
COMIC_NAME = "comic-page.png"
COMIC_HD_NAME = "comic-page-hd.png"

FRAME_DURATION = 1000  # milliseconds per panel
PANELS_PER_ROW = 4     # comic layout

OUTPUT_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# Load panels
# --------------------------------------------------

panels = sorted(PANELS_DIR.glob("panel-*.jpg"))

if not panels:
    raise SystemExit("No panels found (panel-01.jpg etc).")

print("Panels detected:")
for p in panels:
    print(" ", p.name)

frames = [Image.open(p) for p in panels]

# normalize sizes
w, h = frames[0].size
frames = [img.resize((w, h)) for img in frames]

# --------------------------------------------------
# Build GIF
# --------------------------------------------------

gif_path = OUTPUT_DIR / GIF_NAME

frames[0].save(
    gif_path,
    save_all=True,
    append_images=frames[1:],
    duration=FRAME_DURATION,
    loop=0
)

print("GIF created:", gif_path)

# --------------------------------------------------
# Build comic page layout
# --------------------------------------------------

rows = (len(frames) + PANELS_PER_ROW - 1) // PANELS_PER_ROW

page_w = w * PANELS_PER_ROW
page_h = h * rows

comic = Image.new("RGB", (page_w, page_h), "white")

for i, frame in enumerate(frames):

    row = i // PANELS_PER_ROW
    col = i % PANELS_PER_ROW

    x = col * w
    y = row * h

    comic.paste(frame, (x, y))

comic_path = OUTPUT_DIR / COMIC_NAME
comic.save(comic_path)

print("Comic page created:", comic_path)

# --------------------------------------------------
# HD export
# --------------------------------------------------

scale = 2

comic_hd = comic.resize((page_w * scale, page_h * scale), Image.LANCZOS)

hd_path = OUTPUT_DIR / COMIC_HD_NAME
comic_hd.save(hd_path)

print("HD comic page created:", hd_path)

print("\nForest Adventure episode build complete.")