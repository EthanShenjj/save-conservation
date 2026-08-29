---
name: save-conversation
description: 将当前对话保存到用户配置的个人记忆知识库，或生成记忆统计看板；用户明确要求时可完整保留对话原文。使用场景包括用户输入 "save"、"保存对话"、"存进记忆库"、"记录这次对话"、"完整保留对话"、"save conversation"、"remember this"、"统计看板"、"内容统计"、"记忆统计"、"项目统计"。
---

# Save Conversation

把当前 Codex / Claude Code 对话保存到用户配置的个人记忆知识库，并可按需生成统计看板。

## Modes

- **Save mode**：用户输入 `save`、`保存对话`、`记录这次对话`、`存进记忆库`、`save conversation`、`remember this` 时触发。保存当前对话并执行目标知识库 ingest。
- **Stats mode**：用户输入 `统计看板`、`内容统计`、`记忆统计`、`项目统计` 时触发。只读取已有 raw 内容并输出统计，不保存当前对话，不执行 ingest。

用户明确要求“完整保留”“保留全部对话内容”“逐字保存”或等效表达时，Save mode 必须保存可获得的完整对话原文，而不是只写摘要。原文应包含所有用户消息与助手回复，并保留可获得的工具调用、工具结果、文件路径与错误信息；不要省略、改写或压缩对话内容。仍可在原文前保留简短元数据和摘要，便于检索。

用户只输入 `save` 时，直接执行快捷存储；不要为了标题、目录或分类追问。只有配置缺失、固定路径缺失或目标路径无法访问时才提问。

## First-Run Config

首次使用必须配置 `storage_root`。不要内置任何默认本机路径。

配置文件建议放在已安装 skill 目录下：

`{已安装 skill 目录}/save-conversation/config.json`

如果无法写入该目录，则写入当前 skill 目录的 `config.json` 并在回复里说明。

用脚本初始化配置：

```bash
python scripts/memory_store.py config init --storage-root <用户提供的知识库根路径>
```

查看配置：

```bash
python scripts/memory_store.py config show
```

配置后的约定：

- `storage_root` 是 raw/wiki/memory/log 的知识库根目录。
- `default_scope` 默认是 `general`。
- 未明确属于某个项目的对话保存到 `{storage_root}/raw/general/`。

## Script Helpers

使用 `scripts/memory_store.py` 处理确定性文件系统逻辑：

- `config show|init`：读取或初始化配置。
- `target`：创建 raw 目录、规范化项目名、判断新建或同日追加；使用 `--force-new` 可为同日不同主题创建独立记录。
- `append`：把准备好的增量 Markdown 追加到已有 raw 文档。
- `stats`：扫描 `{storage_root}/raw/` 并输出统计看板 Markdown。

示例：

```bash
python scripts/memory_store.py target \
  --storage-root <root> \
  --scope project \
  --project-name <项目名> \
  --title <简短标题> \
  --date YYYY-MM-DD
```

当同一项目当天的话题明显独立，调用 `target` 时加 `--force-new`。脚本会生成不覆盖已有文件的路径。

脚本只负责机械逻辑；对话摘要、意图判断、实体/概念/洞察提取仍由 Codex 完成。

## Storage Rules

所有 raw 文件必须写入二级目录：

```text
raw/
  项目名称/
    2026-07-01-标题.md
  general/
    2026-07-01-标题.md
```

全局对话保存到 `raw/general/`。项目对话保存到 `raw/{项目名称}/`。

项目名优先级：

1. 用户明确给出的项目名。
2. 当前 Git 仓库根目录名称。
3. 当前工作区根目录名称。
4. 当前所在目录名称。

同一项目同一天已有 raw 文档时，默认追加为 `## 增量更新：HH:mm - {本轮主题}`。只有当前对话明显是同一项目内完全不同主题、追加会让文档混乱时，才通过 `target --force-new` 新建独立文档。

## Workflow

完整保存流程见 `references/workflow.md`。写 raw 文档、增量块和汇报时使用 `references/templates.md`。

快速流程：

1. 读取配置；缺失时先配置 `storage_root`。
2. 判断 save mode 或 stats mode。
3. Stats mode：运行 `python scripts/memory_store.py stats --storage-root <root>`，返回 Markdown。
4. Save mode：判断 `general` 或 `project`，并确定项目名。
5. 运行 `target` 获取 `mode` 和 `target_path`；同日独立主题加 `--force-new`。
6. 按模板重建对话记录；`mode=create` 时新建 raw，`mode=append` 时追加相应的摘要或完整原文增量块。
7. 写入前检查明显的密钥、令牌、密码、Cookie、身份证件号等敏感值；默认脱敏。只有用户在风险提示后明确要求原样保存时，才保留这些值。
8. 写入后按目标知识库 `CLAUDE.md` 执行 ingest：sources、entities、concepts、insights、index、log、memory。raw 写入成功即视为保存成功；ingest 失败时保留 raw、说明失败项与错误，并提供重试入口。
9. 汇报 raw 路径、ingest 更新、失败项（如有）和持久化记忆。

## Required Writing Behavior

- 全中文输出元数据、注释、摘要和标签；对话原文可以保留原语言。
- 默认不要逐字抄整段聊天，但必须保留工具调用、文件路径、错误、决策、用户纠正和关键产出。
- 用户明确要求完整保留时，完整原文优先于默认摘要规则；在 `## 完整对话原文` 下按实际消息顺序写入全部可获得内容。
- 完整保留不等于静默保存敏感信息：先脱敏；用户确认原样保存后才保留敏感值。
- 用户反馈很重要：记录用户纠正了什么、肯定了什么、补充了什么。
- 不要编造对话中没发生的内容。

## Do Not

- 不要在配置缺失时保存或统计。
- 不要把 raw 文件直接写到 `raw/` 根目录。
- 不要把明显属于项目的对话保存到 `raw/general/`。
- 不要在同一项目同一天为连续增量内容新建很多 raw 文档。
- 不要跳过目标知识库已有的 ingest 流程。
- 不要忘记更新 `wiki/index.md` 和 `wiki/log.md`，除非目标知识库没有对应 ingest 指令。
