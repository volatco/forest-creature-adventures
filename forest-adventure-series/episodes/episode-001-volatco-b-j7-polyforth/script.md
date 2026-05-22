
# Volatco B at J7 polyForth Bring-up

Objective
Commission a reliable Volatco B polyForth path so the team can write and run Forth programs for future episodes.

Hardware Focus
Volatco B board, J7 connector path, polyForth session bootstrap, cable orientation and signal sanity checks.

Expected Outcome
A repeatable VOLATCO-B workflow that survives reset and is ready for real program loading in later episodes.

---

Success Signals (from aeonForth workflow)
- `VOLATCO-B` is the active polyForth raise path at `921600` baud.
- `./scripts/monitor.sh status` shows a valid `VOLATCO-B` profile path.
- `./scripts/monitor.sh attach B` (or `attach V`) reaches live board interaction.
- Pressing Enter returns `ok` at the board console.
- The sequence still works after an intentional reset and reconnect.

Panel 1
Fox introduces the real mission: commission `VOLATCO-B` so future episodes can focus on building Forth programs, not fighting setup.

Panel 2
Hedgehog asks why `VOLATCO-B` matters if another port "sort of works."

Panel 3
Owl explains port roles and fixed speed: `VOLATCO-B` for raise path, `921600` baud.

Panel 4
They run `./scripts/monitor.sh profiles` and `./scripts/monitor.sh status` to confirm mapping before attach.

Panel 5
Fox runs `./scripts/monitor.sh attach B`; Owl checks for prompt behavior and `ok` on Enter.

Panel 6
A reset is forced; Hedgehog watches reconnect behavior while Squirrel checks cable seating at J7.

Panel 7
They repeat attach and command echo checks; second pass matches the first pass, so program work can begin.

Panel 8
Owl closes with the commissioning rule: "No repeatable `ok` after reset means we are not ready to write new episode code yet."
