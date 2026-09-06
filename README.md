# Save Conversation

一个用于 Codex / Claude Code 的 Skill：将有价值的 AI 对话保存为可检索的个人知识库记录。

## 能做什么

- 输入 `save`、`保存对话` 等，保存当前对话。
- 默认生成结构化摘要；说“完整保留对话”或“逐字保存”时，按顺序保留可获得的原文、工具调用和结果。
- 全局内容保存到 `raw/general/`，项目内容保存到 `raw/{project}/`。
- 同一项目同日默认追加；明确是独立主题时使用 `--force-new` 创建不覆盖已有文件的新记录。
- 输入 `统计看板`、`内容统计`、`记忆统计` 或 `项目统计`，查看已有记录的项目分布、更新情况和主题统计。
<img width="1672" height="941" alt="image" src="https://github.com/user-attachments/assets/babdc1ff-ce46-46c0-91fc-072ddeab3342" />
<img width="1691" height="930" alt="image" src="https://github.com/user-attachments/assets/60780a45-ea10-4cd8-bc19-fff536aee1c8" />


## 快速开始

安装：

```bash
git clone https://github.com/EthanShenjj/save-conservation.git ~/.codex/skills/save-conversation
```

配置知识库根目录：

```bash
cd ~/.codex/skills/save-conversation
python scripts/memory_store.py config init --storage-root /path/to/knowledge-base
```

随后直接在 Codex / Claude Code 中输入：

```text
save
```

## 保存规则

```text
raw/
  general/
    YYYY-MM-DD-title.md
  project-name/
    YYYY-MM-DD-title.md
```

- 默认保存结构化摘要，保留关键决策、路径、错误、产出和用户反馈。
- 完整原文模式在同日追加时会使用专用的“完整对话原文增量”区块。
- 明显的密钥、令牌、密码、Cookie 与证件号默认脱敏；只有在风险提示后用户明确确认，才原样保存。
- raw 文件写入成功即代表保存成功；后续 ingest 失败不会丢失 raw，并应报告失败步骤与重试方式。

## 命令行助手

```bash
# 查看或初始化配置
python scripts/memory_store.py config show
python scripts/memory_store.py config init --storage-root /path/to/kb

# 计算写入目标；独立同日主题加 --force-new
python scripts/memory_store.py target --storage-root /path/to/kb --scope project --project-name my-project --title "demo"
python scripts/memory_store.py target --storage-root /path/to/kb --scope project --project-name my-project --title "new-topic" --force-new

# 追加准备好的 Markdown，或生成统计看板
python scripts/memory_store.py append --target /path/to/raw.md --content-file /tmp/increment.md
python scripts/memory_store.py stats --storage-root /path/to/kb
```

脚本只处理路径、追加和统计；对话理解、摘要、原文整理以及知识库 ingest 由 AI 按 [SKILL.md](SKILL.md) 和 [工作流](references/workflow.md) 执行。
