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
    lead = characters[0] if len(characters) > 0 else "Fox"
    learner = "Hedgehog" if "Hedgehog" in characters else (characters[1] if len(characters) > 1 else lead)
    debugger = "Owl" if "Owl" in characters else (characters[2] if len(characters) > 2 else lead)
    stabilizer = "Squirrel" if "Squirrel" in characters else (characters[-1] if characters else lead)

    script = f"""
# {title}

Objective
{objective}

Hardware Focus
{hardware}

Expected Outcome
{outcome}

---

Story Stakes
- Hunter-gatherer practicality: wasted daylight and failed field decisions if systems are unreliable.
- Technical autonomy: avoid dependence on opaque outside systems the team cannot repair.
- Shared knowledge: cooperation and documentation keep capability in the group.
- Time and season awareness: technical progress supports better orientation to patterns in their habitat.
- Series purpose: every episode advances the team's ability to work confidently with aeonForth.

Panel 1
{lead} frames the real-world field problem and why this mission matters for their aeonForth journey.

Panel 2
{learner} asks the hardest practical question: what failure hurts us most if this breaks in the field?

Panel 3
{debugger} explains the hardware focus and the first repeatable check.

Panel 4
The team runs a concrete validation step and records what success should look like.

Panel 5
{stabilizer} enforces setup discipline so the result is reproducible by others.

Panel 6
The team stress-tests one realistic failure mode and adapts their approach together.

Panel 7
Successful result: {outcome}

Panel 8
Closing handoff: this result strengthens the team's ability to work with aeonForth in future Forth program episodes.
"""

    (output_dir / "script.md").write_text(script)

    prompts = f"""
Use the Forest Adventure Series characters.

Environment: woodland forest clearing.

Episode: {title}
Cast: {cast_line}

Theme anchors:
- Hunter-gatherer practicality: preserve daylight, support tracking/foraging decisions.
- Technical autonomy: resist opaque external systems with local, understandable workflows.
- Cooperation and friendship: shared process over heroics.
- Time/season orientation: gather reliable signals that improve place awareness.
- Series direction: this episode should visibly contribute to working with aeonForth.

Panel prompts:

panel-01
Introduce the practical field mission: {objective}

panel-02
{learner} asks a concrete failure-risk question tied to real-world consequences.

panel-03
Explain hardware: {hardware}

panel-04
Validation scene: explicit success signal is visible and understandable by the whole team.

panel-05
Reproducibility scene: checklist, role clarity, and shared notes prevent hidden knowledge.

panel-06
Stress-test scene: one realistic failure appears, and the team resolves it cooperatively.

panel-07
Successful result: {outcome}

panel-08
Handoff panel: this episode's workflow directly improves the team's ability to work with aeonForth in future Forth program episodes.
"""

    (output_dir / "panel-prompts.md").write_text(prompts)

    checklist = "\n".join([f"panel-{i:02}.jpg" for i in range(1, 9)])

    (output_dir / "panel-checklist.txt").write_text(checklist)

    print(f"Episode generated from: {episode_file}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
