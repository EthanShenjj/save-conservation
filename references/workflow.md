# Save Conversation Workflow

Use this reference for the LLM-owned parts of the workflow: reconstructing the conversation, deciding scope, and running ingest after the raw file is written.

## Save Mode

1. Read config with `scripts/memory_store.py config show`.
2. If config is missing, ask the user for a fixed knowledge-base root path and initialize it with `scripts/memory_store.py config init --storage-root <path>`.
3. Decide scope:
   - Use `general` for global preferences, reusable work style, cross-project knowledge, or conversations with no reliable project context.
   - Use `project` when the conversation is about a repo, workspace, product, feature, debugging session, deployment, document, or named project.
4. Determine project name for project scope:
   - User-provided project name.
   - Current Git repo root name.
   - Current workspace root name.
   - Current directory name.
5. Ask the helper for the target:
   ```bash
   python scripts/memory_store.py target \
     --storage-root <root> \
     --scope project \
     --project-name <name> \
     --title <short-title> \
     --date YYYY-MM-DD
   ```
6. Reconstruct the current conversation into the raw template from `references/templates.md`.
7. If helper returns `mode=create`, write a new raw file at `target_path`.
8. If helper returns `mode=append`, write an increment block to a temporary file and append it with:
   ```bash
   python scripts/memory_store.py append --target <target_path> --content-file <tmp-md>
   ```
9. Run the target knowledge base ingest workflow described in its own `CLAUDE.md`, if present.
10. Report storage classification, raw path, ingest updates, and persistent memory changes.

## Statistics Mode

When the user asks for `统计看板`, `内容统计`, `记忆统计`, or `项目统计`:

1. Read config.
2. If config is missing, ask for `storage_root` first.
3. Run:
   ```bash
   python scripts/memory_store.py stats --storage-root <root>
   ```
4. Return the generated Markdown. Do not save the current conversation and do not run ingest.

## LLM Responsibilities

The helper does not summarize conversations or infer user intent. The LLM must still:

- Extract the topic, tags, user intent, key actions, key outputs, and user feedback.
- Avoid fabricating content that did not occur.
- Preserve important file paths, commands, decisions, errors, and corrections.
- Decide whether a same-day project conversation is genuinely a different topic that deserves a new document. The default should be append.
- Execute ingest judgment: entities, concepts, insights, index/log updates, and persistent memory.

## Guardrails

- Never write raw files directly under `raw/`.
- Never assume a default storage root. Use only the configured `storage_root`.
- Do not run stats as a write operation.
- Do not create many same-project same-day raw files for continuous incremental work.
- If the target knowledge base lacks `CLAUDE.md`, write the raw file and report that ingest instructions were unavailable.
