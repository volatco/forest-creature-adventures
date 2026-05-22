#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a publish-ready funding preview bundle for an episode."
    )
    parser.add_argument(
        "--episode-dir",
        default="forest-adventure-series/episodes/episode-001-volatco-b-j7-polyforth",
        help="Path to the episode directory.",
    )
    parser.add_argument(
        "--preview-file",
        default="funding/EPISODE_001_PREVIEW.md",
        help="Path to the authored funding preview markdown.",
    )
    parser.add_argument(
        "--output-root",
        default="funding/published",
        help="Output root where the publish bundle will be created.",
    )
    return parser.parse_args()


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def collect_panels(episode_dir: Path) -> tuple[list[str], list[str]]:
    expected = [f"panel-{i:02}.jpg" for i in range(1, 9)]
    found, missing = [], []
    for name in expected:
        if (episode_dir / name).exists():
            found.append(name)
        elif (episode_dir / "panels" / name).exists():
            found.append(f"panels/{name}")
        else:
            missing.append(name)
    return found, missing


def main() -> int:
    args = parse_args()
    episode_dir = Path(args.episode_dir).resolve()
    preview_file = Path(args.preview_file).resolve()
    output_root = Path(args.output_root).resolve()

    slug = episode_dir.name
    out_dir = output_root / slug
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for rel in ("script.md", "panel-prompts.md", "panel-checklist.txt"):
        src = episode_dir / rel
        if copy_if_exists(src, out_dir / "episode" / rel):
            copied.append(f"episode/{rel}")

    yaml_files = sorted(episode_dir.glob("*.yaml"))
    for y in yaml_files:
        if copy_if_exists(y, out_dir / "episode" / y.name):
            copied.append(f"episode/{y.name}")

    preview_ok = copy_if_exists(preview_file, out_dir / "funding" / "EPISODE_PREVIEW.md")
    if preview_ok:
        copied.append("funding/EPISODE_PREVIEW.md")

    hero = Path("images/stories/story-volatco-00.jpg").resolve()
    if copy_if_exists(hero, out_dir / "assets" / hero.name):
        copied.append(f"assets/{hero.name}")

    panel_found, panel_missing = collect_panels(episode_dir)
    for p in panel_found:
        src = episode_dir / p
        copy_if_exists(src, out_dir / "episode" / "panels" / Path(p).name)
    if panel_found:
        copied.extend([f"episode/panels/{Path(p).name}" for p in panel_found])

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "episode_dir": str(episode_dir),
        "preview_file": str(preview_file),
        "copied_files": copied,
        "panel_assets_found": [Path(p).name for p in panel_found],
        "panel_assets_missing": panel_missing,
        "ready_for_public_post": len(panel_missing) == 0,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    summary = [
        f"# Publish Bundle: {slug}",
        "",
        f"- Generated: {manifest['generated_at_utc']}",
        f"- Episode source: `{episode_dir}`",
        f"- Funding preview included: {'yes' if preview_ok else 'no'}",
        f"- Panel assets found: {len(panel_found)}/8",
        f"- Ready for full public post: {'yes' if manifest['ready_for_public_post'] else 'no'}",
        "",
    ]
    if panel_missing:
        summary.append("## Missing Panels")
        summary.extend([f"- `{p}`" for p in panel_missing])
        summary.append("")
    (out_dir / "PUBLISH_SUMMARY.md").write_text("\n".join(summary))

    archive_base = output_root / f"{slug}-bundle"
    shutil.make_archive(str(archive_base), "zip", root_dir=out_dir)

    print(f"Created bundle directory: {out_dir}")
    print(f"Created zip archive: {archive_base}.zip")
    print(f"Panels found: {len(panel_found)}/8")
    if panel_missing:
        print("Missing panels:", ", ".join(panel_missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
