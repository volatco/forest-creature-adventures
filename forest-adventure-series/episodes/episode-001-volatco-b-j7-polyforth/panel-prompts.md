
Use the Forest Adventure Series characters.

Environment: woodland forest clearing.

Episode: Volatco B at J7 polyForth Bring-up
Cast: Fox, Owl, Hedgehog, Squirrel

Technical anchors to keep visible in relevant panels:
- Port label `VOLATCO-B`
- Baud `921600`
- Monitor commands: `profiles`, `status`, `attach B` (or `attach V`)
- polyForth console response `ok` after Enter
- Reset and reconnect verification

Panel prompts:

panel-01
Introduce the mission: commission Volatco B at J7 polyForth so future episodes can focus on writing and loading Forth programs.

panel-02
Hedgehog confusion moment.

panel-03
Explain hardware: Volatco B board, J7 connector path, polyForth session bootstrap, cable orientation and signal sanity checks.

panel-04
Owl debugging scene running `./scripts/monitor.sh profiles` and `./scripts/monitor.sh status`, confirming `VOLATCO-B` mapping.

panel-05
Attach sequence scene: `./scripts/monitor.sh attach B` and visible console `ok` after Enter.

panel-06
Intentional reset and reconnect scene; Hedgehog tracks whether the same prompt behavior returns.

panel-07
Successful result: A repeatable workflow that survives reset and is ready for loading future Forth programs.

panel-08
Practical handoff panel: Owl and Fox confirm the board is now ready for future Forth program development episodes.
