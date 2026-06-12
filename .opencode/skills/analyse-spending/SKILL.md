---
name: analyse-spending
description: Use when the user wants to understand where their money is going from transactions, bank exports, pasted statements, receipts, or rough spending notes.
metadata:
  difficulty: beginner
---

# Analyse Spending

Turn messy spending data into a calm, useful money insight summary.

## When to use this

Use this skill when the user asks things like:

- "Where is my money going?"
- "Analyse my spending"
- "What am I spending too much on?"
- "Here are my transactions"
- "Can you categorise this bank statement?"
- "Help me understand my money"

## Procedure

1. Identify the input format: CSV, pasted table, plain text list, or rough notes.
2. Extract transactions into this simple structure:
   - date
   - merchant or description
   - amount
   - category
   - confidence: high, medium, or low
3. Categorise each transaction using these default categories:
   - rent/housing
   - groceries
   - eating out/takeaway
   - coffee/snacks
   - transport
   - subscriptions
   - shopping
   - social/entertainment
   - health
   - education
   - bills
   - emergency/one-off
   - transfers/savings
   - unknown
4. If a transaction is income, refund, transfer, or savings movement, mark it
   separately so it does not distort spending totals.
5. Total spending by category.
6. Call out:
   - top 3 spending categories
   - repeated small purchases
   - likely subscriptions
   - one-off costs
   - categories with uncertain classification
7. Give 1-3 realistic next actions. Make them small and specific.

## Output format

Use this format:

```markdown
## Spending Snapshot

Analysed: <number> transactions
Period: <date range or "unknown">
Total outgoing spending: <amount>

## Category Breakdown

| Category | Total | What this means |
|---|---:|---|
| ... | ... | ... |

## What Stands Out

- ...

## Small Changes With The Biggest Impact

1. ...
2. ...
3. ...

## Unclear Items

- ...
```

## Guidance

- Be non-judgemental.
- Do not assume the user is overspending just because a category is high.
- Mention if rent, bills, or emergency costs explain most of the spending.
- If the dataset is tiny, say it is a first pass.
- If the user shares sensitive data, tell them to remove account numbers or
  card details before continuing.
