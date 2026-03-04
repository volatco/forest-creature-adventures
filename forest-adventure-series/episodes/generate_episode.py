import yaml
from pathlib import Path

EPISODE_FILE = "episode.yaml"
OUTPUT_DIR = Path("episode")

OUTPUT_DIR.mkdir(exist_ok=True)

with open(EPISODE_FILE) as f:
    data = yaml.safe_load(f)

title = data["title"]
objective = data["objective"]
hardware = data["hardware_focus"]
outcome = data["expected_outcome"]

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

(Path("episode") / "script.md").write_text(script)

prompts = f"""
Use the Forest Adventure Series characters.

Environment: woodland forest clearing.

Episode: {title}

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

(Path("episode") / "panel-prompts.md").write_text(prompts)

checklist = "\n".join([f"panel-{i:02}.jpg" for i in range(1,9)])

(Path("episode") / "panel-checklist.txt").write_text(checklist)

print("Episode generated.")