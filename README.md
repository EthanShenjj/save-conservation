# Save Conversation

Save Conversation is a Codex / Claude Code skill for turning useful AI conversations into a personal knowledge base.

It supports two main workflows:

- **Quick save**: type `save` to archive the current conversation.
- **Memory dashboard**: type `统计看板` to review saved conversation statistics.

The skill does not assume a default storage path. Each user must configure their own knowledge-base root directory before saving or generating statistics.

## What It Does

Save Conversation helps you build a lightweight LLM wiki from your AI collaboration history:

- Reconstructs the current conversation into a structured Markdown memory document.
- Routes global knowledge to `raw/general/`.
- Routes project-specific conversations to `raw/{project-name}/`.
- Appends same-project same-day updates to the existing daily document instead of creating many fragmented files.
- Generates a statistics dashboard from saved raw memories.
- Keeps deterministic filesystem work in `scripts/memory_store.py`, while the AI handles summarization and knowledge extraction.

## Repository Structure

```text
save-conversation/
  SKILL.md
  scripts/
    memory_store.py
  references/
    workflow.md
    templates.md
```

## Installation

Clone this repository into your Codex skills directory.

Recommended:

```bash
git clone https://github.com/EthanShenjj/save-conservation.git ~/.codex/skills/save-conversation
```

If you clone it somewhere else, make sure the skill folder is available to Codex and contains `SKILL.md`.

## First-Time Configuration

Before using the skill, configure a storage root. This is the root directory where `raw/`, `wiki/`, `memory/`, and logs should live.

```bash
python scripts/memory_store.py config init --storage-root /path/to/your/knowledge-base
```

Show the current config:

```bash
python scripts/memory_store.py config show
```

Example config:

```json
{
  "storage_root": "/path/to/your/knowledge-base",
  "default_scope": "general",
  "created_at": "2026-07-13"
}
```

Do not commit your personal `config.json` if it contains local paths.

## Usage

### Save The Current Conversation

In Codex / Claude Code, type:

```text
save
```

The skill will:

1. Read the configured `storage_root`.
2. Decide whether the conversation is global or project-specific.
3. Ask `scripts/memory_store.py target` for the correct raw path.
4. Write a structured Markdown memory document.
5. Append same-project same-day updates when appropriate.
6. Run the target knowledge base ingest workflow if available.

### Generate A Statistics Dashboard

Type:

```text
统计看板
```

or:

```text
内容统计
记忆统计
项目统计
```

The skill will scan `{storage_root}/raw/` and report:

- Project count
- Memory document count
- Global document count
- Project distribution
- Most discussed project
- Same-day increment counts
- Recent updates
- Frequent topics
- Review suggestions

## Storage Layout

All raw memory files are stored under second-level directories:

```text
raw/
  project-name/
    2026-07-13-short-title.md
  general/
    2026-07-13-short-title.md
```

Global knowledge goes to:

```text
raw/general/
```

Project conversations go to:

```text
raw/{project-name}/
```

## Same-Day Increment Rule

If the same project already has a document for the same date, the skill appends a section like:

```markdown
---

## 增量更新：21:30 - 本轮主题

### 本轮概要
...
```

This keeps one project day together instead of creating many small raw files.

## Helper Script

`scripts/memory_store.py` provides deterministic helpers:

```bash
python scripts/memory_store.py config show
python scripts/memory_store.py config init --storage-root /path/to/kb
python scripts/memory_store.py target --storage-root /path/to/kb --scope project --project-name my-project --title "demo"
python scripts/memory_store.py append --target /path/to/raw.md --content-file /tmp/increment.md
python scripts/memory_store.py stats --storage-root /path/to/kb
```

The script does not summarize conversations. The AI is still responsible for:

- Understanding the conversation.
- Extracting topic, intent, actions, outputs, and feedback.
- Avoiding fabricated details.
- Running ingest steps according to the target knowledge base.

## Validation

Run the skill validator:

```bash
python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

Run Python syntax validation:

```bash
python -m py_compile scripts/memory_store.py
```

## Notes

- No default personal path is built in.
- Do not write raw files directly under `raw/`.
- Do not save project conversations into `raw/general/`.
- Do not create many same-project same-day raw files for incremental work.

