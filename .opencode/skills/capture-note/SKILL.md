---
name: capture-note
description: Use when the user wants to save, remember, jot down, or capture a thought, fact, link, or decision. Writes a structured Markdown note into the memory/ vault (Obsidian/Logseq compatible) so it survives between sessions.
metadata:
  difficulty: beginner
---

# Capture Note

Save a durable note to the agent's long-term memory.

## When to use this

The user says things like "remember that…", "save this", "note that…", "jot down",
"keep this for later", or hands you a fact/link/decision worth keeping. If they're just
chatting, don't capture — only persist things with future value.

## What a memory note looks like

Every note is one Markdown file in the `memory/` folder. Keep the format exactly like
this so the vault stays consistent and Obsidian/Logseq can read it:

```markdown
---
title: Coffee suppliers shortlist
created: 2026-06-01
tags: [procurement, coffee]
---

We narrowed it to three roasters: Allpress, Climpson, and Square Mile. Square Mile
quoted the lowest per-kg for our volume. Decision still open — revisit after the tasting.

Related: [[office-fit-out]]  #procurement
```

## Procedure

1. **Decide the slug.** Turn the topic into a short kebab-case filename, e.g.
   `coffee-suppliers.md`. Lowercase, hyphens, no spaces.
2. **Check for an existing note** on the same topic with the `recall` skill (or a quick
   search of `memory/`). If one exists, **update it** rather than creating a duplicate —
   append the new information under the existing body.
3. **Get today's date** with the `date +%Y-%m-%d` command — don't guess it.
4. **Write the file** to `memory/<slug>.md` using the format above:
   - `title`: a human-readable one-liner.
   - `created`: today's date (only set on creation; leave as-is when updating).
   - `tags`: 1–4 lowercase tags.
   - Body: the actual content, in plain language. Add `[[links]]` to related notes and
     `#hashtags` for topics where it helps future recall.
5. **Confirm** to the user: name the file you wrote and one line on what's in it.

## Notes for whoever iterates on this skill

- This is deliberately simple. Good next steps: auto-suggest tags from existing notes,
  detect near-duplicate notes before writing, or add a `source:` field for links.
- If you switch your persistence layer to Notion (see `docs/persistence.md`), this is the
  skill you rewrite — swap the "write a file" step for a "create a Notion page" step.
