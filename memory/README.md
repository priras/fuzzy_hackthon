# memory/ — your agent's long-term memory

Everything in this folder is your agent's persistent brain. Each `.md` file is one note.
The agent writes here with the `capture-note` skill and reads here with `recall`.

**This folder is also an Obsidian / Logseq vault.** Open it in either app and you'll see
the agent's notes as a normal, linkable knowledge base — and anything *you* add by hand,
the agent can read back. One shared brain for you and the agent.

- Notes use YAML frontmatter (`title`, `created`, `tags`) plus a plain-language body.
- `[[double-bracket]]` links connect notes; `#hashtags` group them by topic.
- One idea per file. Filenames are short kebab-case slugs.

See `welcome.md` for an example, and `docs/persistence.md` for how to point Obsidian or
Logseq at this folder (or swap the whole layer out for Notion).
