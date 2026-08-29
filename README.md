# Save Conversation

Language: [中文](#中文) | [English](#english)

## 中文

Save Conversation 是一个 Codex / Claude Code Skill，用来把有价值的 AI 对话沉淀成个人知识库。

它支持两种主要工作流：

- **快捷保存**：输入 `save`，归档当前对话。
- **统计看板**：输入 `统计看板`，查看已保存记忆的统计信息。

这个 Skill 不内置任何默认存储路径。每个用户都需要先配置自己的知识库根目录，然后才能保存或生成统计。

### 功能

Save Conversation 可以帮助你把 AI 协作记录变成一个轻量的 LLM Wiki：

- 将当前对话重建成结构化 Markdown 记忆文档。
- 用户明确要求时，完整保留当前对话的可获得原文（含用户消息、助手回复与工具记录）。
- 将全局知识保存到 `raw/general/`。
- 将项目相关对话保存到 `raw/{project-name}/`。
- 同一项目同一天的后续内容会追加到当天文档，避免生成很多碎片文件。
- 同日遇到明确独立的主题时，可创建不覆盖已有内容的独立文档。
- 从已有 raw 记忆中生成统计看板。
- 将确定性的文件系统逻辑封装在 `scripts/memory_store.py`，AI 负责总结和知识提取。

### 仓库结构

```text
save-conversation/
  SKILL.md
  scripts/
    memory_store.py
  references/
    workflow.md
    templates.md
```

### 安装

将仓库克隆到 Codex skills 目录：

```bash
git clone https://github.com/EthanShenjj/save-conservation.git ~/.codex/skills/save-conversation
```

如果克隆到其他位置，请确保 Codex 可以发现这个 skill 文件夹，并且目录中包含 `SKILL.md`。

### 首次配置

使用前需要配置存储根目录。这个目录是你的知识库根目录，后续 `raw/`、`wiki/`、`memory/` 和日志都会放在这里。

```bash
python scripts/memory_store.py config init --storage-root /path/to/your/knowledge-base
```

查看当前配置：

```bash
python scripts/memory_store.py config show
```

配置示例：

```json
{
  "storage_root": "/path/to/your/knowledge-base",
  "default_scope": "general",
  "created_at": "2026-07-13"
}
```

如果 `config.json` 包含你的本地路径，请不要提交它。

### 使用

#### 保存当前对话

在 Codex / Claude Code 中输入：

```text
save
```

Skill 会：

1. 读取已配置的 `storage_root`。
2. 判断当前对话属于全局记忆还是项目记忆。
3. 调用 `scripts/memory_store.py target` 获取正确的 raw 路径。
4. 写入结构化 Markdown 记忆文档。
5. 如果同一项目同一天已有文档，则追加增量内容。
6. 如果目标知识库有 ingest 流程，则继续执行 ingest。

如果用户在保存请求中明确说“完整保留对话”“保留全部内容”或“逐字保存”，Skill 会以消息发生顺序写入完整原文，而非仅写结构化摘要。

#### 生成统计看板

输入：

```text
统计看板
```

也可以输入：

```text
内容统计
记忆统计
项目统计
```

Skill 会扫描 `{storage_root}/raw/` 并输出：

- 项目数
- 记忆文档数
- 全局文档数
- 项目分布
- 讨论最多的项目
- 同日增量次数
- 最近更新
- 高频主题
- 回顾建议

### 存储结构

所有 raw 记忆文件都会保存到二级目录：

```text
raw/
  project-name/
    2026-07-13-short-title.md
  general/
    2026-07-13-short-title.md
```

全局知识保存到：

```text
raw/general/
```

项目对话保存到：

```text
raw/{project-name}/
```

### 同日增量规则

如果同一项目当天已经有文档，Skill 会追加类似下面的增量小节：

```markdown
---

## 增量更新：21:30 - 本轮主题

### 本轮概要
...
```

这样可以把同一项目同一天的上下文保存在一起，而不是拆成很多小文件。

如果当天出现确实独立的新主题，保存流程会使用 `--force-new` 创建另一个文件；脚本会自动避免覆盖同名文件。

### 敏感信息与失败恢复

保存前会默认脱敏明显的密钥、令牌、密码、Cookie 与证件号。只有在风险提示后用户明确确认时，才会原样写入。raw 文件写入成功即代表保存成功；后续知识库 ingest 失败时，原始记录会保留，并在报告中说明失败步骤与重试方式。

### 辅助脚本

`scripts/memory_store.py` 提供确定性的文件系统辅助能力：

```bash
python scripts/memory_store.py config show
python scripts/memory_store.py config init --storage-root /path/to/kb
python scripts/memory_store.py target --storage-root /path/to/kb --scope project --project-name my-project --title "demo"
python scripts/memory_store.py target --storage-root /path/to/kb --scope project --project-name my-project --title "new-topic" --force-new
python scripts/memory_store.py append --target /path/to/raw.md --content-file /tmp/increment.md
python scripts/memory_store.py stats --storage-root /path/to/kb
```

脚本不会总结对话。AI 仍然负责：

- 理解当前对话。
- 提取主题、意图、行动、产出和用户反馈。
- 避免编造没有发生过的内容。
- 根据目标知识库执行 ingest 步骤。

### 校验

运行 skill 校验：

```bash
python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

运行 Python 语法校验：

```bash
python -m py_compile scripts/memory_store.py
```

### 注意事项

- 不内置任何个人默认路径。
- 不要把 raw 文件直接写到 `raw/` 根目录。
- 不要把明显属于项目的对话保存到 `raw/general/`。
- 不要为同一项目同一天的连续增量内容创建很多碎片文档。

## English

Save Conversation is a Codex / Claude Code skill for turning useful AI conversations into a personal knowledge base.

It supports two main workflows:

- **Quick save**: type `save` to archive the current conversation.
- **Memory dashboard**: type `统计看板` to review saved conversation statistics.

The skill does not assume a default storage path. Each user must configure their own knowledge-base root directory before saving or generating statistics.

### What It Does

Save Conversation helps you build a lightweight LLM wiki from your AI collaboration history:

- Reconstructs the current conversation into a structured Markdown memory document.
- Routes global knowledge to `raw/general/`.
- Routes project-specific conversations to `raw/{project-name}/`.
- Appends same-project same-day updates to the existing daily document instead of creating many fragmented files.
- Creates a separate, non-overwriting document for a clearly independent same-day topic.
- Generates a statistics dashboard from saved raw memories.
- Keeps deterministic filesystem work in `scripts/memory_store.py`, while the AI handles summarization and knowledge extraction.

### Repository Structure

```text
save-conversation/
  SKILL.md
  scripts/
    memory_store.py
  references/
    workflow.md
    templates.md
```

### Installation

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/EthanShenjj/save-conservation.git ~/.codex/skills/save-conversation
```

If you clone it somewhere else, make sure the skill folder is available to Codex and contains `SKILL.md`.

### First-Time Configuration

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

### Usage

#### Save The Current Conversation

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

For a clearly independent same-day topic, use `--force-new` when resolving the target. The helper will avoid overwriting an existing file.

#### Generate A Statistics Dashboard

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

### Storage Layout

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

### Same-Day Increment Rule

If the same project already has a document for the same date, the skill appends a section like:

```markdown
---

## 增量更新：21:30 - 本轮主题

### 本轮概要
...
```

This keeps one project day together instead of creating many small raw files.

### Helper Script

`scripts/memory_store.py` provides deterministic helpers:

```bash
python scripts/memory_store.py config show
python scripts/memory_store.py config init --storage-root /path/to/kb
python scripts/memory_store.py target --storage-root /path/to/kb --scope project --project-name my-project --title "demo"
python scripts/memory_store.py target --storage-root /path/to/kb --scope project --project-name my-project --title "new-topic" --force-new
python scripts/memory_store.py append --target /path/to/raw.md --content-file /tmp/increment.md
python scripts/memory_store.py stats --storage-root /path/to/kb
```

The script does not summarize conversations. The AI is still responsible for:

- Understanding the conversation.
- Extracting topic, intent, actions, outputs, and feedback.
- Avoiding fabricated details.
- Running ingest steps according to the target knowledge base.

### Validation

Run the skill validator:

```bash
python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

Run Python syntax validation:

```bash
python -m py_compile scripts/memory_store.py
```

### Notes

- No default personal path is built in.
- Do not write raw files directly under `raw/`.
- Do not save project conversations into `raw/general/`.
- Do not create many same-project same-day raw files for incremental work.
