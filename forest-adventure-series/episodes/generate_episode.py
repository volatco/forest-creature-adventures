import argparse
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate episode scaffold files from YAML.")
    parser.add_argument(
        "--episode-file",
        default="episode.yaml",
        help="Path to episode YAML file (default: episode.yaml).",
    )
    parser.add_argument(
        "--output-dir",
        default="episode",
        help="Directory for generated files (default: episode).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    episode_file = Path(args.episode_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with episode_file.open() as f:
        data = yaml.safe_load(f)

    title = data["title"]
    objective = data["objective"]
    hardware = data["hardware_focus"]
    outcome = data["expected_outcome"]
    characters = data.get("characters", [])
    cast_line = ", ".join(characters) if characters else "Forest cast"

    script = f"""
# {title}

Objective
{objective}

Hardware Focus
{hardware}

Expected Outcome
{outcome}

---

Panel 1
Fox introduces the engineering problem.

Panel 2
Hedgehog misunderstands the concept.

Panel 3
Fox explains the hardware.

Panel 4
Owl observes the signal behaviour.

Panel 5
Fox clarifies the system architecture.

Panel 6
Hedgehog imagines an animal analogy.

Panel 7
The hardware works.

Panel 8
Humorous closing remark.
"""

    (output_dir / "script.md").write_text(script)

    prompts = f"""
Use the Forest Adventure Series characters.

Environment: woodland forest clearing.

Episode: {title}
Cast: {cast_line}

Panel prompts:

panel-01
Introduce the problem: {objective}

panel-02
Hedgehog confusion moment.

panel-03
Explain hardware: {hardware}

panel-04
Owl debugging scene.

panel-05
System explanation.

panel-06
Animal metaphor joke.

panel-07
Successful result: {outcome}

panel-08
Humorous closing panel.
"""

    (output_dir / "panel-prompts.md").write_text(prompts)

    checklist = "\n".join([f"panel-{i:02}.jpg" for i in range(1, 9)])

    (output_dir / "panel-checklist.txt").write_text(checklist)

    print(f"Episode generated from: {episode_file}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
