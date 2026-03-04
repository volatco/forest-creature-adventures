## How to animate the series via gif

`pip install pillow`

### Folder structure for automation

```
episode-001/
│
├── panels/
│   ├── panel-01.jpg
│   ├── panel-02.jpg
│   ├── panel-03.jpg
│   ├── panel-04.jpg
│   ├── panel-05.jpg
│   ├── panel-06.jpg
│   └── panel-07.jpg
│
└── build_episode_gif.py
```

### Run

`python build_episode_gif.py`

### Optimizations

_faster_

`FRAME_DURATION = 800`

_slower_

`FRAME_DURATION = 1500`

_pacing_

`1000 ms`

## Advanced mode

`pip install pyyaml`

### Style lock

```
STYLE LOCK

Use the same characters as the reference images:

Fox:
small orange fox, cream chest, fluffy white tail tip,
simple oval black eyes, rounded cartoon proportions.

Hedgehog:
round brown hedgehog with fuzzy spines,
small nose, tiny feet.

Environment:
sunny woodland clearing, soft watercolor style,
storybook illustration aesthetic.

Maintain identical character design and proportions
as earlier panels in this episode.
```

### Prompt structure

```
Generate ONE comic panel.

STYLE LOCK
[insert style lock block]

PANEL ACTION
[describe the scene]

DIALOGUE
Fox: "..."
Hedgehog: "..."
```

_poses_

Add these to the references.

```
poses/
│
├── fox-explaining.png
├── fox-thinking.png
├── hedgehog-confused.png
├── hedgehog-thinking.png
└── owl-debugging.png
```

_reference reminder_

`Use the same fox and hedgehog design as previous panels in this episode.`

_episode generator flow_

```
episode-*.yaml
      ↓
generate_episode.py
      ↓
panel prompts
      ↓
generate panel images
      ↓
panel-01.jpg
panel-02.jpg
...
      ↓
build_episode.py
      ↓
comic page + GIF
```