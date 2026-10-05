"""Offline checks for skill metadata, local links, and Python examples (Python 3.10+)."""

import argparse
import ast
import json
import os
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

SKIP = {".git", ".venv", "node_modules", "__pycache__"}
NAME = r"[a-z0-9]+(?:-[a-z0-9]+)*"
VERSION = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:[-+][0-9A-Za-z.+-]+)?"
OBSOLETE = {"MultiMCPTools", "OpenAIChat"}


def markdown(text):
    """Mask fenced code while retaining line numbers; collect executable examples."""
    prose, blocks, code = [], [], []
    fence, language, start = "", "", 0
    for number, line in enumerate(text.splitlines(), 1):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if not fence and marker:
            fence, language, start = marker[1], marker[2].strip().split(), number + 1
            code = []
        elif fence and re.fullmatch(
            r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*", line
        ):
            blocks.append(
                (language[0].lower() if language else "", "\n".join(code), start)
            )
            fence = ""
        elif fence:
            code.append(line)
        else:
            prose.append(line)
            continue
        prose.append("")
    if fence:
        blocks.append((language[0].lower() if language else "", "\n".join(code), start))
    return "\n".join(prose), blocks, start - 1 if fence else None


def links(prose):
    """Read inline destinations and reference definitions, excluding inline code."""
    prose = re.sub(r"(`+)(.+?)\1", "", prose)
    starts = [match.end() for match in re.finditer(r"\[[^]\n]*\]\(\s*", prose)]
    starts += [
        match.end() for match in re.finditer(r"(?m)^ {0,3}\[[^]\n]+\]:\s*", prose)
    ]
    for start in starts:
        if prose[start : start + 1] == "<":
            end = prose.find(">", start + 1)
            if end != -1:
                yield prose[start + 1 : end]
            continue
        end, depth = start, 0
        while end < len(prose):
            char = prose[end]
            if char == "\\" and end + 1 < len(prose):
                end += 2
                continue
            if char.isspace() or (char == ")" and depth == 0):
                break
            depth += (char == "(") - (char == ")")
            end += 1
        yield re.sub(r"\\(.)", r"\1", prose[start:end])


def anchors(text):
    prose, _, _ = markdown(text)
    prose = re.sub(r"\A---\n.*?\n---(?:\n|$)", "", prose, flags=re.S)
    headings = re.findall(r"(?m)^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", prose)
    headings += re.findall(r"(?m)^([^\n]+)\n {0,3}(?:=+|-+)\s*$", prose)
    result = set(re.findall(r'<[^>]+\b(?:id|name)=["\']([^"\']+)', prose))
    counts = {}
    for heading in headings:
        heading = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", heading)
        heading = re.sub(r"<[^>]*>|[`*]", "", heading)
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        result.add(f"{slug}-{count}" if count else slug)
        counts[slug] = count + 1
    return result


def validate(root):
    root = Path(root).resolve()
    errors, files = [], []

    def fail(path, message):
        errors.append(f"{path.relative_to(root)}: {message}")

    def inside(path):
        return path.resolve().is_relative_to(root)

    for directory, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs if name not in SKIP]
        files.extend(Path(directory) / name for name in names)
    markdown_files = [path for path in files if path.suffix.lower() == ".md"]
    for path in markdown_files:
        if not inside(path):
            fail(path, "file escapes repository")
            continue
        text = path.read_text(encoding="utf-8")
        prose, blocks, unclosed = markdown(text)
        if unclosed is not None:
            fail(path, f"line {unclosed}: unclosed code fence")
        resolved = set()
        for destination in links(prose):
            try:
                url = urlsplit(destination)
            except ValueError:
                fail(path, f"invalid link: {destination}")
                continue
            if url.scheme or url.netloc:
                continue
            target = (
                (path.parent / unquote(url.path)).resolve()
                if url.path
                else path.resolve()
            )
            if not inside(target):
                fail(path, f"link escapes repository: {destination}")
            elif not target.exists():
                fail(path, f"missing link target: {destination}")
            else:
                resolved.add(target)
                if url.fragment and target.suffix.lower() == ".md" and target.is_file():
                    if unquote(url.fragment) not in anchors(
                        target.read_text(encoding="utf-8")
                    ):
                        fail(path, f"missing heading anchor: {destination}")
        if path.name == "SKILL.md":
            match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
            try:
                metadata = yaml.safe_load(match[1]) if match else None
                if not isinstance(metadata, dict):
                    raise ValueError("missing YAML frontmatter mapping")
                name, description = metadata.get("name"), metadata.get("description")
                if (
                    not isinstance(name, str)
                    or len(name) > 64
                    or not re.fullmatch(NAME, name)
                ):
                    raise ValueError(
                        "name must be 1-64 lowercase letters/digits with single hyphens"
                    )
                if name != path.parent.name:
                    raise ValueError("name must match skill directory")
                if (
                    not isinstance(description, str)
                    or not description.strip()
                    or len(description) > 1024
                ):
                    raise ValueError(
                        "description must be a nonempty string of at most 1024 characters"
                    )
            except (yaml.YAMLError, ValueError) as error:
                fail(path, f"frontmatter: {error}")
            for reference in path.parent.glob("references/**/*.md"):
                if reference.resolve() not in resolved:
                    fail(
                        path, f"orphan reference: {reference.relative_to(path.parent)}"
                    )
        for language, code, start in blocks:
            if language not in {"python", "py", "python3"}:
                continue
            try:
                compile(code, str(path), "exec")
                tree = ast.parse(code)
            except SyntaxError as error:
                fail(
                    path,
                    f"line {start + (error.lineno or 1) - 1}: invalid Python: {error.msg}",
                )
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = getattr(node.func, "id", getattr(node.func, "attr", ""))
                    if name in OBSOLETE:
                        fail(
                            path,
                            f"line {start + node.lineno - 1}: unsupported example API {name}",
                        )
                if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                    "agno."
                ):
                    for alias in node.names:
                        if alias.name in OBSOLETE or (
                            node.module == "agno.tools.mcp"
                            and alias.name == "MCPToolbox"
                        ):
                            fail(
                                path,
                                f"line {start + node.lineno - 1}: unsupported example import {alias.name}",
                            )
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if re.fullmatch(r"(?:openai:)?gpt-4o(?:-[a-z0-9.-]+)?", node.value):
                        fail(
                            path,
                            f"line {start + node.lineno - 1}: obsolete example model {node.value}",
                        )

    marketplace = root / ".claude-plugin/marketplace.json"
    registered = set()
    try:
        if not inside(marketplace):
            raise ValueError("marketplace escapes repository")
        market = json.loads(marketplace.read_text(encoding="utf-8"))
        if (
            not isinstance(market, dict)
            or not isinstance(market.get("name"), str)
            or not market["name"].strip()
        ):
            raise ValueError("marketplace needs a name")
        entries = market.get("plugins")
        if not isinstance(entries, list) or not entries:
            raise ValueError("marketplace needs a nonempty plugins array")
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("source"), str):
                raise ValueError("plugin needs a local source string")
            source = (root / entry["source"]).resolve()
            if not inside(source):
                raise ValueError("plugin source escapes repository")
            manifest = source / ".claude-plugin/plugin.json"
            if not inside(manifest):
                raise ValueError("plugin manifest escapes repository")
            if not any((source / "skills").rglob("SKILL.md")):
                raise ValueError(
                    "each plugin must contain at least one SKILL.md in skills/"
                )
            registered.add(manifest.resolve())
            plugin = json.loads(manifest.read_text(encoding="utf-8"))
            if not isinstance(plugin, dict):
                raise ValueError("plugin manifest must be an object")
            for key, pattern in (("name", NAME), ("version", VERSION)):
                value = plugin.get(key)
                if (
                    not isinstance(value, str)
                    or not re.fullmatch(pattern, value)
                    or entry.get(key) != value
                ):
                    raise ValueError(
                        f"plugin {key} must be valid and match marketplace"
                    )
            if plugin["name"] in seen:
                raise ValueError("duplicate marketplace plugin name")
            seen.add(plugin["name"])
        manifests = {
            p.resolve()
            for p in files
            if p.name == "plugin.json" and p.parent.name == ".claude-plugin"
        }
        if manifests != registered:
            raise ValueError(
                "plugin manifests must all be registered in the marketplace"
            )
    except (OSError, ValueError) as error:
        fail(marketplace, f"manifest: {error}")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1]
    )
    problems = validate(parser.parse_args().root)
    print("\n".join(problems) if problems else "Skill validation passed.")
    raise SystemExit(bool(problems))
