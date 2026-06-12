# Ideas to extend your agent

You have two starter skills (`capture-note`, `recall`) and one example persona
(`researcher`). Here's a menu of next steps. Pick what fits the agent you're building —
don't try to do all of it. Each is a self-contained afternoon's work, roughly ordered
easiest-first within each section.

## More skills (offline — no extra accounts needed)

- **daily-journal** — append a timestamped entry to today's note. The "what did I do
  today" habit, owned by your agent.
- **weekly-review** — read every note from the last 7 days and write a summary note.
  Great demo: the agent reflecting on its own memory.
- **summarise-file** — point it at a PDF / Markdown / text file and get a tight summary
  saved to memory.
- **todo** — capture, list, and complete tasks stored as Markdown checkboxes (works in
  Obsidian/Logseq too). A mini task manager.
- **tag-cleanup** — scan `memory/` and suggest merging near-duplicate tags
  (`#ai` vs `#a.i.`). Teaches the agent to curate its own brain.
- **link-suggester** — when saving a note, find existing notes it should `[[link]]` to.

## More skills (with an MCP server or API — a bit more setup)

- **web-research** — fan out a few web searches, read the top results, write a cited
  brief. Pairs perfectly with the `researcher` persona. (Add a web-search MCP server.)
- **calendar** — read your week, find free slots, draft (never send) invites.
- **inbox-triage** — classify email into reply / read-later / ignore. Drafts only.
- **github-watch** — summarise new issues or PRs on a repo you care about.
- **expense-snap** — read a photo of a receipt and log the amount to memory.

## More personas

A persona is a focused mindset your agent (or a subagent) can adopt. Copy
`.opencode/agents/researcher.md` and rewrite it. Good ones to try:

- **planner** — breaks a fuzzy goal into ordered, concrete steps. Doesn't do the work,
  designs it.
- **critic** — pokes holes. "What's the weakest assumption here? What would make this
  fail?" Run it over your own plans.
- **explainer** — rewrites anything in plain language for a specific audience (a 12-year
  old, a busy exec, a sceptical engineer).
- **devils-advocate** — argues the opposite case so you stress-test a decision.
- **a domain voice** — a gardening coach, a recipe planner, a study buddy. Make it *about
  something* — specific agents are more fun to demo than generic ones.

## MCP connections (giving your agent hands)

MCP (Model Context Protocol) is how your agent reaches the outside world — Notion, Slack,
GitHub, a database, your filesystem. Add servers under `"mcp"` in `opencode.json`. The
Notion one is already stubbed there as an example. Browse servers at
<https://github.com/modelcontextprotocol/servers> and OpenCode's MCP docs.

Ideas: Notion (notes/tasks), Slack (read & draft messages), GitHub (issues/PRs), a
SQLite/Postgres database, a maps or weather server, a web-search server.

## Stretch goals (if you're flying)

- **Subagent orchestration** — have your primary agent delegate to several personas
  (researcher → critic → writer) for one task.
- **A scheduled run** — a "good morning" briefing the agent writes to memory each day.
- **Semantic recall** — upgrade `recall` from keyword search to embeddings so it finds
  notes by *meaning*, not just matching words.
- **Voice or a tiny web UI** — put a friendlier face on the terminal agent.

## Demo tips

- A working small thing beats an impressive broken thing. Get one loop solid:
  capture → recall, demoed live, is genuinely compelling.
- Show the `memory/` folder open in Obsidian beside the terminal — "the agent and I share
  one brain" lands every time.
- Have a real, personal use case. Agents are more memorable when they obviously help
  *you* with *your* actual life.
