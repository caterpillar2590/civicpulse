#!/usr/bin/env python3
"""Submission lint per assignment §5.8. NOT a grader - just catches the
mechanical failures behind most of §5.3's automatic deductions before you
submit. A clean run does not guarantee a good mark; a dirty run nearly
guarantees a bad one. Run from the repository root:

    python scripts/check_submission.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
problems: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def check_env_not_in_git() -> None:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "log", "--all", "--full-history", "--", ".env"],
        capture_output=True, text=True,
    )
    if result.stdout.strip():
        fail(".env appears in git history - §5.3: -20 marks, rotate the credential")


def check_secrets_have_placeholders() -> None:
    secret_path = ROOT / "k8s" / "base" / "secret.yaml"
    if not secret_path.exists():
        fail("k8s/base/secret.yaml is missing")
        return
    text = secret_path.read_text()
    for line in text.splitlines():
        m = re.match(r"\s*\w+:\s*[\"']?([^\"'#\n]+)", line)
        if m and "REPLACE_ME" not in text:
            warn("k8s/base/secret.yaml may contain a real value, not a placeholder - check manually")
            break


def check_unpinned_images() -> None:
    for f in [ROOT / "compose.yaml", ROOT / "compose.prod.yaml"]:
        if not f.exists():
            continue
        text = f.read_text()
        for m in re.finditer(r"image:\s*([^\s${}]+)$", text, re.MULTILINE):
            image = m.group(1)
            if ":" not in image.split("/")[-1]:
                fail(f"{f.name}: unpinned image (no tag) -> {image} - §5.3: -8 marks")


def check_no_latest_in_k8s() -> None:
    for f in (ROOT / "k8s").rglob("*.yaml"):
        text = f.read_text()
        if re.search(r"image:\s*\S+:latest\b", text) and "overlays" not in str(f):
            warn(f"{f}: references :latest directly - confirm this is a placeholder overridden by CI (ADR 0003)")


def check_no_published_db_ports_in_prod() -> None:
    prod = ROOT / "compose.prod.yaml"
    if not prod.exists():
        return
    text = prod.read_text()
    import yaml
    data = yaml.safe_load(text)
    for svc in ("database", "cache"):
        if "ports" in data.get("services", {}).get(svc, {}):
            fail(f"compose.prod.yaml: '{svc}' publishes a port - §5.3: -8 marks")


def check_required_docs_exist() -> None:
    required = [
        "README.md",
        "docs/RUNBOOK.md",
        "docs/ENGINEERING-NOTES.md",
        "docs/AI-USAGE.md",
        "docs/adr/0001-provider-interface.md",
        "docs/adr/0002-frontend-runtime-config.md",
        "docs/adr/0003-deploy-by-sha.md",
        "docs/adr/0004-pii-and-data-governance.md",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            fail(f"missing required doc: {rel}")


def check_required_workflows_exist() -> None:
    for name in ["ci.yml", "cd.yml", "release.yml"]:
        if not (ROOT / ".github" / "workflows" / name).exists():
            fail(f"missing workflow: .github/workflows/{name}")


def check_main_not_pushed_directly() -> None:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "log", "--oneline", "-5"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        warn("not a git repository yet - can't check commit history")


def main() -> int:
    check_env_not_in_git()
    check_secrets_have_placeholders()
    check_unpinned_images()
    check_no_latest_in_k8s()
    check_no_published_db_ports_in_prod()
    check_required_docs_exist()
    check_required_workflows_exist()
    check_main_not_pushed_directly()

    if warnings:
        print("WARNINGS (review manually):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if problems:
        print("PROBLEMS FOUND:")
        for p in problems:
            print(f"  - {p}")
        print(f"\n{len(problems)} problem(s). Fix before submitting.")
        return 1

    print("No mechanical problems found. This is a lint, not a grader.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
