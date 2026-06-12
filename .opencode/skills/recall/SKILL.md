---
name: recall
description: Use when the user asks what they saved earlier, what the agent knows about a topic, or to find / look up / remember a past note. Searches the memory/ vault and answers from what it finds.
metadata:
  difficulty: beginner
---

# Recall

Answer questions using the agent's long-term memory — the notes in the `memory/` folder.

## When to use this

The user asks "what did I save about…", "what do you know about…", "did I note anything
on…", "remind me about…", or asks a question that an earlier note might answer. Also use
this *before* `capture-note` writes, to avoid creating a duplicate note.

## Procedure

1. **Search the vault.** Grep the `memory/` folder for the topic. Search both filenames
   and contents — a good first pass is the user's keywords plus obvious synonyms. For
   example, for "coffee" also try "roaster", "espresso", "supplier".
2. **Open the matches.** Read the files that look relevant (don't answer from the
   filename alone). Follow any `[[links]]` to related notes if they add context.
3. **Answer from what you found.** Quote or paraphrase the note, and **always say which
   note(s) it came from** (the filename). If the notes disagree or are out of date, say so.
4. **Be honest about gaps.** If nothing in `memory/` covers it, say "I don't have a note
   on that" — don't fill the gap by inventing an answer. Offer to capture one.

## Notes for whoever iterates on this skill

- This does keyword search. The obvious upgrade is *semantic* search (embeddings) so
  "how do we pick vendors" finds the "supplier shortlist" note even without shared words.
- Another good iteration: rank results by the `created` date so recent notes win, or
  summarise across several notes instead of quoting one.
- If you move to Notion (see `docs/persistence.md`), this is where you'd query the Notion
  API / MCP instead of grepping local files.
