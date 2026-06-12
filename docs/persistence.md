# Choosing a persistence layer

An agent without memory starts from zero every session. The **persistence layer** is
where your agent keeps what it learns. This is one of the most important design choices
you'll make, so here are the three good options for a hackathon, with honest trade-offs.

This starter ships with **option 1 (local Markdown)** wired up and working. Switching to
another option means rewriting two skills (`capture-note` and `recall`) — that's the point
of putting persistence behind skills, so the rest of the agent doesn't care where notes go.

---

## Option 1 — Local Markdown vault (the default here)

Plain `.md` files in the `memory/` folder.

- **Free, offline, zero setup, fully open.** Nothing to log into, no API keys, no rate
  limits. Perfect for a hackathon where you want to be building in minute one.
- **It's also an Obsidian *and* a Logseq vault** — open the folder in either app and the
  agent's notes become a real, navigable knowledge base you can edit by hand.
- The agent reads/writes with normal file tools, which every model can do reliably — even
  the cheap ones. No flaky tool-calling.
- Trade-off: it's *local*. No syncing across machines unless you put the folder in a git
  repo, Dropbox, or iCloud yourself. Search is keyword-based until you build something
  smarter.

**Best for:** almost everyone starting out. Start here, change later if you need to.

### Pointing Obsidian or Logseq at it

- **Obsidian:** *Open folder as vault* → choose this repo's `memory/` folder. Done. The
  frontmatter, `[[links]]`, and `#tags` all render natively.
- **Logseq:** *Add a graph* → choose the `memory/` folder. Logseq prefers an outliner
  (bullet) style and keeps daily notes in a `journals/` subfolder. The notes here still
  open fine; if you want full Logseq-native journaling, have your `capture-note` skill
  write bullet-point bodies and date-named files into `memory/journals/`.

---

## Option 2 — Notion (via MCP)

A hosted database your agent reads and writes through the **Notion MCP server** (already
stubbed in `opencode.json`, just disabled).

- **Shareable and structured.** Great if your agent's output is for a *team*, or if you
  want proper databases (tasks, contacts, a content calendar) with views and filters.
- Accessible from anywhere, on any device, no file syncing to manage.
- Trade-off: needs a one-time browser login, depends on the network, and adds an
  external dependency that can rate-limit or go down. Tool-calling against an API is also
  a bit more for a cheap model to get right than reading a local file.

### Turning it on

1. In `opencode.json`, set the `notion` MCP server's `"enabled"` to `true`.
2. Start OpenCode and run `/mcp` (or follow the auth prompt) to do the one-time login.
3. Rewrite `capture-note` to *create a Notion page* and `recall` to *query Notion*
   instead of touching local files. The skill files already mark exactly where.

**Best for:** team-facing agents, or when structured databases beat freeform notes.

---

## Option 3 — Logseq as the primary store

Logseq is an open-source, local-first outliner. You *can* treat it as more than a viewer
for option 1 — make it the native home, with the agent writing Logseq-flavoured Markdown
(bulleted outlines, `[[page]]` references, daily journal pages).

- Local-first and open like option 1, but with a stronger graph/backlink model and a nice
  daily-journal workflow out of the box.
- Trade-off: the outliner format is fussier for an agent to emit perfectly, and Logseq's
  block-reference features are wasted unless your skills actually use them.

**Best for:** teams already living in Logseq, or agents whose whole job is journaling and
connecting ideas over time.

---

## How to choose (quick version)

| You want… | Pick |
|---|---|
| To start building *now*, free and offline | **Local Markdown** |
| A human to read/edit the agent's notes in a nice app | **Local Markdown** (+ Obsidian) |
| A team to share the agent's output, or real databases | **Notion** |
| Heavy journaling and idea-linking, local-first | **Logseq** |

When in doubt: ship on local Markdown, demo it, and only switch if you hit a real wall.
