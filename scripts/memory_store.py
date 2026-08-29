#!/usr/bin/env python3
"""Deterministic helpers for the save-conversation skill.

The LLM still writes conversation summaries and performs ingest judgment.
This script handles repeatable filesystem work: config, target routing,
same-day append decisions, and raw/ statistics.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


CONFIG_NAME = "config.json"
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")
INCREMENT_RE = re.compile(r"^##\s+增量更新：", re.MULTILINE)
TRANSCRIPT_INCREMENT_RE = re.compile(r"^##\s+完整对话原文增量：", re.MULTILINE)
TRANSCRIPT_SECTION_RE = re.compile(r"^##\s+完整对话原文", re.MULTILINE)
MESSAGE_RE = re.compile(r"^###\s+(?:用户|助手|工具调用|工具结果)\s*$", re.MULTILINE)
TOPIC_RE = re.compile(r"^topic:\s*(.+)$", re.MULTILINE)
TAGS_RE = re.compile(r"^tags:\s*\[(.*?)\]\s*$", re.MULTILINE)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def fail(message: str, code: int = 2) -> None:
    print(json.dumps({"ok": False, "error": message}, ensure_ascii=False), file=sys.stderr)
    raise SystemExit(code)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def today_str() -> str:
    return date.today().isoformat()


def config_path(skill_dir: Path, explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    return (skill_dir / CONFIG_NAME).resolve()


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"配置不存在：{path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"配置 JSON 无法解析：{exc}")
    storage_root = data.get("storage_root")
    if not storage_root:
        fail("配置缺少 storage_root")
    data["storage_root"] = str(Path(storage_root).expanduser().resolve())
    data.setdefault("default_scope", "general")
    return data


def write_config(path: Path, storage_root: str, default_scope: str) -> dict[str, Any]:
    root = Path(storage_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        fail(f"storage_root 不是目录：{root}")
    if not os.access(root, os.W_OK):
        fail(f"storage_root 不可写：{root}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "storage_root": str(root),
        "default_scope": default_scope,
        "created_at": today_str(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def slugify(value: str, fallback: str = "project") -> str:
    value = value.strip().lower()
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff.-]+", "", value)
    value = value.strip(".-")
    return value or fallback


def kebab_title(value: str, fallback: str = "conversation") -> str:
    value = value.strip().lower()
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff.-]+", "", value)
    value = value.strip(".-")
    return value or fallback


def markdown_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted([p for p in path.iterdir() if p.is_file() and p.suffix.lower() == ".md"])


def date_from_name(path: Path) -> str | None:
    match = DATE_RE.match(path.name)
    return match.group(1) if match else None


def infer_title(path: Path, text: str | None = None) -> str:
    stem = path.stem
    match = DATE_RE.match(path.name)
    fallback = stem[11:] if match and len(stem) > 11 else stem
    if text:
        topic = TOPIC_RE.search(text)
        if topic:
            return topic.group(1).strip().strip('"')
        h1 = H1_RE.search(text)
        if h1:
            return h1.group(1).strip()
    return fallback


def choose_today_file(raw_dir: Path, day: str, title: str | None = None) -> tuple[Path | None, list[Path]]:
    files = [p for p in markdown_files(raw_dir) if p.name.startswith(f"{day}-")]
    if not files:
        return None, []
    if len(files) == 1:
        return files[0], files
    title_slug = kebab_title(title or "")
    if title_slug:
        for path in files:
            if title_slug in path.stem:
                return path, files
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0], files


def available_path(raw_dir: Path, day: str, title_slug: str) -> Path:
    candidate = raw_dir / f"{day}-{title_slug}.md"
    if not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = raw_dir / f"{day}-{title_slug}-{index}.md"
        if not candidate.exists():
            return candidate
        index += 1


def cmd_config(args: argparse.Namespace) -> None:
    path = config_path(Path(args.skill_dir), args.config)
    if args.action == "show":
        data = load_config(path)
        emit({"ok": True, "config_path": str(path), "config": data})
        return
    if not args.storage_root:
        fail("init 需要 --storage-root")
    data = write_config(path, args.storage_root, args.default_scope)
    emit({"ok": True, "config_path": str(path), "config": data})


def cmd_target(args: argparse.Namespace) -> None:
    root = Path(args.storage_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    raw_root = root / "raw"
    scope = args.scope
    if scope == "general":
        bucket = "general"
    else:
        if not args.project_name:
            fail("scope=project 需要 --project-name")
        bucket = slugify(args.project_name)
    raw_dir = raw_root / bucket
    raw_dir.mkdir(parents=True, exist_ok=True)
    day = args.date or today_str()
    title_slug = kebab_title(args.title or "conversation")
    selected, today_files = choose_today_file(raw_dir, day, args.title)
    if scope == "project" and selected and not args.force_new:
        mode = "append"
        target = selected
    else:
        mode = "create"
        target = available_path(raw_dir, day, title_slug)
    emit(
        {
            "ok": True,
            "mode": mode,
            "scope": bucket if scope == "project" else "general",
            "raw_dir": str(raw_dir),
            "target_path": str(target),
            "today_files": [str(p) for p in today_files],
        }
    )


def cmd_append(args: argparse.Namespace) -> None:
    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        fail(f"追加目标不存在：{target}")
    content = Path(args.content_file).read_text(encoding="utf-8")
    sep = "\n\n" if target.read_text(encoding="utf-8").endswith("\n") else "\n\n"
    with target.open("a", encoding="utf-8") as fh:
        fh.write(sep)
        fh.write(content.strip())
        fh.write("\n")
    emit({"ok": True, "target_path": str(target), "mode": "append"})


@dataclass
class RawDoc:
    project: str
    path: Path
    date: str | None
    title: str
    increments: int
    transcript_increments: int
    transcript_sections: int
    message_blocks: int
    characters: int
    mtime: datetime
    tags: list[str]


def extract_tags(text: str) -> list[str]:
    match = TAGS_RE.search(text)
    if not match:
        return []
    return [t.strip().strip('"').strip("'") for t in match.group(1).split(",") if t.strip()]


def collect_docs(storage_root: Path) -> tuple[list[RawDoc], int]:
    raw_root = storage_root / "raw"
    if not raw_root.exists():
        return [], 0
    docs: list[RawDoc] = []
    general_count = 0
    for directory in sorted([p for p in raw_root.iterdir() if p.is_dir()]):
        for path in markdown_files(directory):
            text = path.read_text(encoding="utf-8", errors="replace")
            if directory.name == "general":
                general_count += 1
            docs.append(
                RawDoc(
                    project=directory.name,
                    path=path,
                    date=date_from_name(path),
                    title=infer_title(path, text),
                    increments=len(INCREMENT_RE.findall(text)),
                    transcript_increments=len(TRANSCRIPT_INCREMENT_RE.findall(text)),
                    transcript_sections=len(TRANSCRIPT_SECTION_RE.findall(text)),
                    message_blocks=len(MESSAGE_RE.findall(text)),
                    characters=len(text),
                    mtime=datetime.fromtimestamp(path.stat().st_mtime),
                    tags=extract_tags(text),
                )
            )
    return docs, general_count


def frequent_terms(docs: list[RawDoc]) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    stop = {"conversation", "general", "对话", "记录", "标题", "项目", "内容"}
    for doc in docs:
        for tag in doc.tags:
            if tag:
                counter[tag.lstrip("#").lower()] += 1
        parts = re.split(r"[-_\s/：:，,。()\[\]【】]+", doc.title)
        for part in parts:
            part = part.strip("# ")
            key = part.lower()
            if len(part) >= 2 and key not in stop and not re.fullmatch(r"\d+", part):
                counter[key] += 1
    return counter.most_common(8)


def cmd_stats(args: argparse.Namespace) -> None:
    root = Path(args.storage_root).expanduser().resolve()
    docs, general_count = collect_docs(root)
    if not docs:
        print("## 记忆统计看板\n\n暂无可统计内容。")
        return
    projects = sorted({d.project for d in docs if d.project != "general"})
    by_project: dict[str, list[RawDoc]] = {}
    for doc in docs:
        by_project.setdefault(doc.project, []).append(doc)
    dates = sorted([d.date for d in docs if d.date])
    now = datetime.now()
    recent_7 = sum(1 for d in docs if d.mtime >= now - timedelta(days=7))
    recent_30 = sum(1 for d in docs if d.mtime >= now - timedelta(days=30))
    transcript_docs = sum(1 for d in docs if d.transcript_sections)
    transcript_increments = sum(d.transcript_increments for d in docs)
    message_blocks = sum(d.message_blocks for d in docs)
    characters = sum(d.characters for d in docs)
    rows = []
    for project, items in by_project.items():
        if project == "general":
            continue
        latest = max(items, key=lambda d: d.mtime)
        rows.append((project, len(items), sum(d.increments + d.transcript_increments for d in items), latest.mtime.date().isoformat()))
    rows.sort(key=lambda r: (r[1] + r[2], r[3]), reverse=True)
    most_active = rows[0] if rows else ("无", 0, 0, "")
    recent_docs = sorted(docs, key=lambda d: d.mtime, reverse=True)[: args.recent_limit]
    terms = frequent_terms(docs)

    print("## 记忆统计看板\n")
    print("### 总览")
    print(f"- 项目数：{len(projects)}")
    print(f"- 记忆文档：{len(docs)}")
    print(f"- 全局文档：{general_count}")
    print(f"- 原始内容字符数：{characters}")
    print(f"- 完整对话记录：{transcript_docs}，完整对话增量：{transcript_increments}，消息块：{message_blocks}")
    print(f"- 时间范围：{dates[0] if dates else '未知'} 至 {dates[-1] if dates else '未知'}")
    print(f"- 最近 7 天新增/更新：{recent_7}")
    print(f"- 最近 30 天新增/更新：{recent_30}\n")
    print("### 项目分布")
    print("| 项目 | 文档数 | 增量讨论 | 最近更新 |")
    print("| --- | ---: | ---: | --- |")
    for project, count, increments, latest in rows:
        print(f"| {project} | {count} | {increments} | {latest} |")
    print("\n### 讨论最多")
    print(f"- 最活跃项目：{most_active[0]}")
    print(f"- 主要依据：文档数 {most_active[1]}，增量讨论 {most_active[2]}\n")
    print("### 高频主题")
    if terms:
        for term, count in terms:
            print(f"- {term}：{count}")
    else:
        print("- 暂无可识别主题")
    print("\n### 近期更新")
    for doc in recent_docs:
        rel = doc.path.relative_to(root)
        print(f"- `{rel}`：{doc.title}")
    print("\n### 回顾建议")
    print(f"- 优先回顾 `{most_active[0]}`，它是当前最活跃的项目。")
    print("- 查看最近 7 天更新，补充还没有沉淀成原则或复用流程的内容。")
    print("- 对增量讨论多的项目做一次阶段复盘，避免上下文只堆积不提炼。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="save-conversation filesystem helper")
    sub = parser.add_subparsers(dest="command", required=True)

    config = sub.add_parser("config", help="read or initialize config")
    config.add_argument("action", choices=["show", "init"])
    config.add_argument("--skill-dir", default=str(Path(__file__).resolve().parents[1]))
    config.add_argument("--config")
    config.add_argument("--storage-root")
    config.add_argument("--default-scope", default="general")
    config.set_defaults(func=cmd_config)

    target = sub.add_parser("target", help="compute raw target path")
    target.add_argument("--storage-root", required=True)
    target.add_argument("--scope", choices=["general", "project"], required=True)
    target.add_argument("--project-name")
    target.add_argument("--title", required=True)
    target.add_argument("--date")
    target.add_argument("--force-new", action="store_true", help="create a separate same-day document")
    target.set_defaults(func=cmd_target)

    append = sub.add_parser("append", help="append prepared markdown to an existing raw file")
    append.add_argument("--target", required=True)
    append.add_argument("--content-file", required=True)
    append.set_defaults(func=cmd_append)

    stats = sub.add_parser("stats", help="print markdown statistics dashboard")
    stats.add_argument("--storage-root", required=True)
    stats.add_argument("--recent-limit", type=int, default=8)
    stats.set_defaults(func=cmd_stats)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
