# Next Session Prompt

You are continuing work in this repo:

- `/home/cartheur/ame/aiventure/aiventure-github/volatco/forest-creature-adventures`

Current state:

- We added squirrel animation tooling scripts and committed them in:
  - `8a351d1 Add squirrel animation tooling and ignore generated outputs`
- Render artifacts are ignored via `.gitignore` (`/output/` is ignored).
- Main Blender script:
  - `scripts/blender_squirrel_stick_rig.py`

What went wrong last session:

- The squirrel was not clearly visible in earlier Blender renders.
- We started a `v3` visibility-first update in `blender_squirrel_stick_rig.py`:
  - bigger squirrel card
  - alpha blend
  - emissive material
  - short validation output (`4s`)
- We paused before validating final visual quality.

Your tasks (in order):

1. Run a short validation render first:
   - `LIBGL_ALWAYS_SOFTWARE=1 blender --background --python scripts/blender_squirrel_stick_rig.py`
2. Extract one frame from the output and verify the squirrel is clearly visible.
3. If still unclear, fix material/placement immediately (do not do long render loops first).
4. Once visibility is good, switch output back to 10s and render final.
5. Keep artifacts out of git (no files from `output/` in commits).
6. Commit only script/source changes.

Definition of done:

- Final render clearly shows the squirrel character throughout motion.
- Script is stable and runnable from CLI.
- Clean git status except intended source changes.
