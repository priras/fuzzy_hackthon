from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st


APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
MEMORY_FILE = APP_DIR / "money_memory.json"
SAMPLE_FILE = DATA_DIR / "sample_student_transactions.csv"


CATEGORIES = [
    "Groceries",
    "Takeaway / eating out",
    "Cafes / drinks",
    "Transport",
    "Subscriptions",
    "Shopping",
    "Social spending",
    "Sports / fitness",
    "Movies / entertainment",
    "Other",
]


CATEGORY_RULES = {
    "Groceries": [
        "tesco",
        "aldi",
        "lidl",
        "sainsbury",
        "asda",
        "morrisons",
        "coop",
        "co-op",
        "iceland",
        "waitrose",
    ],
    "Takeaway / eating out": [
        "uber eats",
        "deliveroo",
        "just eat",
        "mcdonald",
        "kfc",
        "nando",
        "pizza",
        "restaurant",
        "wagamama",
        "itsu",
        "subway",
        "greggs",
        "meal deal",
        "lunch",
        "dinner",
    ],
    "Cafes / drinks": [
        "starbucks",
        "costa",
        "pret",
        "cafe",
        "coffee",
        "matcha",
        "nero",
        "bubble tea",
    ],
    "Transport": [
        "trainline",
        "uber",
        "bolt",
        "bus",
        "tube",
        "tfl",
        "rail",
        "tram",
        "taxi",
        "oyster",
    ],
    "Subscriptions": [
        "netflix",
        "spotify",
        "prime",
        "amazon prime",
        "disney",
        "notion",
        "icloud",
        "youtube premium",
        "subscription",
    ],
    "Shopping": [
        "asos",
        "zara",
        "hm",
        "h&m",
        "amazon",
        "boots",
        "superdrug",
        "primark",
        "urban outfitters",
    ],
    "Social spending": [
        "bar",
        "pub",
        "club",
        "night out",
        "drinks",
        "tickets",
        "bowling",
        "student union",
        "night out",
    ],
    "Sports / fitness": [
        "gym",
        "puregym",
        "the gym",
        "sports",
        "decathlon",
        "fitness",
        "yoga",
    ],
    "Movies / entertainment": [
        "cinema",
        "odeon",
        "vue",
        "cineworld",
        "movie",
        "theatre",
        "concert",
    ],
}


MOCK_STORE_PRICES = pd.DataFrame(
    [
        {"Item": "Milk", "Aldi": 1.45, "Lidl": 1.45, "Tesco": 1.65, "Sainsbury's": 1.70, "Asda": 1.60},
        {"Item": "Pasta", "Aldi": 0.79, "Lidl": 0.85, "Tesco": 0.95, "Sainsbury's": 1.00, "Asda": 0.90},
        {"Item": "Rice", "Aldi": 1.25, "Lidl": 1.29, "Tesco": 1.55, "Sainsbury's": 1.60, "Asda": 1.45},
        {"Item": "Eggs", "Aldi": 1.99, "Lidl": 2.05, "Tesco": 2.35, "Sainsbury's": 2.40, "Asda": 2.25},
        {"Item": "Snacks", "Aldi": 1.10, "Lidl": 1.15, "Tesco": 1.60, "Sainsbury's": 1.75, "Asda": 1.45},
    ]
)


STORE_ALIASES = {
    "Tesco": ["tesco"],
    "Aldi": ["aldi"],
    "Lidl": ["lidl"],
    "Sainsbury's": ["sainsbury", "sainsbury's"],
    "Asda": ["asda"],
}


GROCERY_COMPARISON_ITEMS = ["milk", "pasta", "rice", "eggs", "snacks"]


DEFAULT_MEMORY = {
    "profile": {
        "name": "Priyanshi",
        "goal": "Spend smarter on things I enjoy",
        "interests": "matcha, movies, restaurants, groceries, sports",
        "schedule": "Busy on Tuesday and Thursday",
        "tone": "supportive and practical",
        "watched_categories": "Cafes / drinks, Takeaway / eating out, Groceries, Subscriptions",
        "wants_reminders": True,
    },
    "plans": [],
}


EMPTY_MEMORY = {
    "profile": {
        "name": "",
        "goal": "",
        "interests": "",
        "schedule": "",
        "tone": "supportive and practical",
        "watched_categories": "",
        "wants_reminders": True,
    },
    "plans": [],
}


@dataclass
class AnalysisResult:
    transactions: pd.DataFrame
    category_totals: pd.DataFrame
    total_spending: float
    top_categories: list[str]
    goal: str
    goal_focus: str
    spending_personality: str
    personality_reason: str
    keep_reduce_review: dict[str, list[str]]
    savings_explanation: list[str]
    estimated_savings_low: float
    estimated_savings_high: float
    pattern: str
    recommendations: list[str]
    actions: list[str]
    draft_message: str


def load_memory() -> dict[str, Any]:
    if not MEMORY_FILE.exists():
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()

    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as file:
            memory = json.load(file)
    except json.JSONDecodeError:
        memory = DEFAULT_MEMORY.copy()

    memory.setdefault("profile", DEFAULT_MEMORY["profile"].copy())
    memory.setdefault("plans", [])
    return memory


def save_memory(memory: dict[str, Any]) -> None:
    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(memory, file, indent=2)


def currency(value: float) -> str:
    return f"£{value:,.2f}"


def format_price_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return "Not found"
    return currency(float(value))


def format_price_table(prices: pd.DataFrame) -> pd.DataFrame:
    display = prices.copy()
    for column in display.columns:
        if column != "Item":
            display[column] = display[column].apply(format_price_value)
    return display


@st.cache_data(ttl=60 * 60)
def fetch_live_store_prices(items: tuple[str, ...]) -> tuple[pd.DataFrame | None, str]:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return None, "No SERPAPI_API_KEY found, so Budget Lens is showing demo prices."

    rows = []
    for item in items:
        row: dict[str, Any] = {"Item": item.title()}
        for store in STORE_ALIASES:
            row[store] = None

        params = {
            "engine": "google_shopping",
            "q": f"{item} UK grocery Tesco Aldi Lidl Sainsbury's Asda",
            "gl": "uk",
            "hl": "en",
            "num": "30",
            "api_key": api_key,
        }

        try:
            response = requests.get("https://serpapi.com/search", params=params, timeout=12)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as error:
            return None, f"Live price lookup failed, so Budget Lens is showing demo prices. Reason: {error}"

        for result in data.get("shopping_results", []):
            price = result.get("extracted_price")
            if price is None:
                continue

            result_text = f"{result.get('source', '')} {result.get('title', '')}".lower()
            for store, aliases in STORE_ALIASES.items():
                if row[store] is None and any(alias in result_text for alias in aliases):
                    row[store] = float(price)

        rows.append(row)

    live_prices = pd.DataFrame(rows)
    found_prices = live_prices.drop(columns=["Item"]).notna().sum().sum()
    if found_prices == 0:
        return None, "The API returned shopping results, but no matching supermarket prices were found. Showing demo prices."

    return live_prices, "Live prices loaded from Google Shopping results via SerpApi. Treat them as indicative, not guaranteed shelf prices."


def normalise_amount(raw_amount: Any) -> float:
    text = str(raw_amount).strip()
    text = text.replace("£", "").replace(",", "")
    text = text.replace("(", "-").replace(")", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return abs(float(match.group())) if match else 0.0


def categorise(description: str) -> str:
    lowered = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "Other"


def parse_pasted_transactions(raw_text: str) -> pd.DataFrame:
    rows = []
    for line in raw_text.splitlines():
        clean_line = line.strip().lstrip("-*").strip()
        if not clean_line:
            continue

        parts = [part.strip() for part in clean_line.split(",")]
        if len(parts) >= 3:
            date = parts[0]
            description = ", ".join(parts[1:-1])
            amount = normalise_amount(parts[-1])
        else:
            amount_match = re.search(r"£?\s*-?\d+(?:\.\d+)?", clean_line)
            if not amount_match:
                continue
            amount = normalise_amount(amount_match.group())
            date = "Unknown"
            description = clean_line.replace(amount_match.group(), "").strip(" ,")

        rows.append(
            {
                "date": date,
                "description": description,
                "amount": amount,
                "category": categorise(description),
            }
        )

    return pd.DataFrame(rows)


def parse_uploaded_csv(uploaded_file: Any) -> pd.DataFrame:
    raw = pd.read_csv(uploaded_file)
    columns = {column.lower().strip(): column for column in raw.columns}

    date_col = columns.get("date")
    description_col = columns.get("description") or columns.get("merchant") or columns.get("name")
    amount_col = columns.get("amount") or columns.get("value") or columns.get("spend")

    if not description_col or not amount_col:
        st.warning("CSV needs at least description/merchant and amount columns.")
        return pd.DataFrame()

    parsed = pd.DataFrame(
        {
            "date": raw[date_col] if date_col else "Unknown",
            "description": raw[description_col].astype(str),
            "amount": raw[amount_col].apply(normalise_amount),
        }
    )
    parsed["category"] = parsed["description"].apply(categorise)
    return parsed


def category_breakdown(transactions: pd.DataFrame) -> pd.DataFrame:
    totals = (
        transactions.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )
    total_spending = totals["amount"].sum()
    totals["percentage"] = totals["amount"].apply(
        lambda amount: (amount / total_spending * 100) if total_spending else 0
    )
    return totals


def estimate_savings(
    category_totals: pd.DataFrame,
    goal: str,
    interests: str,
    schedule: str,
) -> tuple[float, float]:
    goal_lower = goal.lower()
    interest_text = interests.lower()
    schedule_lower = schedule.lower()

    saving_rates = {
        "Takeaway / eating out": (0.15, 0.30),
        "Cafes / drinks": (0.20, 0.35),
        "Subscriptions": (0.20, 0.50),
        "Shopping": (0.10, 0.20),
        "Movies / entertainment": (0.10, 0.20),
        "Groceries": (0.05, 0.12),
        "Transport": (0.05, 0.10),
    }

    if "save money" in goal_lower:
        saving_rates["Takeaway / eating out"] = (0.20, 0.35)
        saving_rates["Cafes / drinks"] = (0.25, 0.40)
        saving_rates["Shopping"] = (0.15, 0.30)
    elif "stress" in goal_lower:
        saving_rates["Takeaway / eating out"] = (0.18, 0.32)
        saving_rates["Cafes / drinks"] = (0.15, 0.25)
        saving_rates["Shopping"] = (0.12, 0.22)
    elif "grocery" in goal_lower:
        saving_rates["Groceries"] = (0.10, 0.20)
        saving_rates["Takeaway / eating out"] = (0.10, 0.18)
    elif "subscription" in goal_lower:
        saving_rates["Subscriptions"] = (0.35, 0.75)
    elif "smarter" in goal_lower or "enjoy" in goal_lower:
        saving_rates["Takeaway / eating out"] = (0.12, 0.22)
        saving_rates["Cafes / drinks"] = (0.10, 0.20)
        saving_rates["Movies / entertainment"] = (0.05, 0.12)
        saving_rates["Shopping"] = (0.12, 0.24)

    if any(day in schedule_lower for day in ["busy", "tuesday", "thursday", "work", "university", "uni"]):
        saving_rates["Takeaway / eating out"] = (
            saving_rates["Takeaway / eating out"][0] + 0.03,
            saving_rates["Takeaway / eating out"][1] + 0.05,
        )

    if any(word in interest_text for word in ["matcha", "coffee", "cafe", "cafes"]):
        saving_rates["Cafes / drinks"] = (
            max(0.08, saving_rates["Cafes / drinks"][0] - 0.04),
            max(0.15, saving_rates["Cafes / drinks"][1] - 0.05),
        )

    low = 0.0
    high = 0.0
    for _, row in category_totals.iterrows():
        rate_low, rate_high = saving_rates.get(row["category"], (0.0, 0.0))
        low += row["amount"] * rate_low
        high += row["amount"] * rate_high
    return low, high


def explain_savings(category_totals: pd.DataFrame, goal: str, interests: str, schedule: str) -> list[str]:
    explanations = []
    goal_lower = goal.lower()
    interest_text = interests.lower()
    schedule_lower = schedule.lower()
    explanation_rules = {
        "Takeaway / eating out": "reduce takeaway by planning around busy days",
        "Cafes / drinks": "set a weekly cafe or matcha limit",
        "Subscriptions": "pause, cancel, or switch one subscription to a student plan",
        "Shopping": "delay one non-urgent order for 24 hours",
        "Movies / entertainment": "use student cinema tickets or cheaper screening days",
        "Groceries": "move basics to Aldi or Lidl where possible",
        "Transport": "plan journeys earlier to avoid last-minute rides",
    }

    for _, row in category_totals.head(4).iterrows():
        category = row["category"]
        if category in explanation_rules:
            explanations.append(
                f"{category}: {explanation_rules[category]}."
            )

    if not explanations:
        explanations.append("The estimate is based on small reductions in flexible categories, not cutting essentials.")

    if "subscription" in goal_lower:
        explanations.insert(0, "Your goal prioritises subscription review, so subscription savings are weighted higher.")
    elif "grocery" in goal_lower:
        explanations.insert(0, "Your goal prioritises grocery comparison, so grocery savings are weighted higher.")
    elif "stress" in goal_lower:
        explanations.insert(0, "Your goal prioritises reducing stress-linked convenience spending.")
    elif "smarter" in goal_lower or "enjoy" in goal_lower:
        explanations.insert(0, "Your goal protects enjoyable spending and looks for lower-value swaps.")
    elif "save money" in goal_lower:
        explanations.insert(0, "Your goal prioritises the fastest flexible spending reductions this week.")

    if any(day in schedule_lower for day in ["busy", "tuesday", "thursday", "work", "university", "uni"]):
        explanations.append("Your schedule suggests busy days, so takeaway savings include a small planning benefit.")
    if any(word in interest_text for word in ["matcha", "coffee", "cafe", "cafes"]):
        explanations.append("Cafe savings are kept realistic because cafe/matcha spending is one of your stated interests.")
    return explanations


def goal_focus(goal: str, top_categories: list[str]) -> str:
    goal_lower = goal.lower()
    top = top_categories[0].lower() if top_categories else "your largest flexible category"

    if "save money" in goal_lower:
        return f"Fastest win: reduce {top} by a small fixed amount this week."
    if "stress" in goal_lower:
        return "Main focus: spot the moment before stress spending and prepare a cheaper fallback."
    if "grocery" in goal_lower:
        return "Main focus: compare weekly basics and separate planned groceries from convenience top-ups."
    if "subscription" in goal_lower:
        return "Main focus: review renewals, duplicates, and student plans before the next charge."
    if "spending habits" in goal_lower:
        return "Main focus: understand the trigger behind the spend before changing the budget."
    if "smarter" in goal_lower or "enjoy" in goal_lower:
        return "Main focus: protect spending you value and reduce lower-value convenience spending."
    return f"Main focus: understand why {top} is high and choose one realistic adjustment."


def spending_personality(
    top_categories: list[str],
    transactions: pd.DataFrame,
) -> tuple[str, str]:
    descriptions = " ".join(transactions["description"].astype(str)).lower()

    if "Takeaway / eating out" in top_categories and any(
        word in descriptions for word in ["after lecture", "late", "after work", "deliveroo", "uber eats"]
    ):
        return (
            "Convenience Spender",
            "Food spending appears around busy, late, or low-energy moments.",
        )
    if "Cafes / drinks" in top_categories:
        return (
            "Cafe Treat Spender",
            "Small cafe and drink purchases repeat often enough to become a visible pattern.",
        )
    if "Social spending" in top_categories or "Movies / entertainment" in top_categories:
        return (
            "Social Planner",
            "A noticeable part of spending is linked to going out, entertainment, and shared plans.",
        )
    if "Subscriptions" in top_categories:
        return (
            "Subscription Drifter",
            "Recurring charges are taking up space in the budget and are worth reviewing.",
        )
    if top_categories and top_categories[0] == "Groceries":
        return (
            "Essentials-Heavy Week",
            "Most spending is going toward basics, so savings should come from comparison rather than harsh cuts.",
        )
    return (
        "Balanced but Busy",
        "Spending is spread across several areas, so the best next step is one small weekly focus.",
    )


def keep_reduce_review(
    top_categories: list[str],
    interests: str,
) -> dict[str, list[str]]:
    interest_text = interests.lower()
    keep = []
    reduce = []
    review = []

    if "movies" in interest_text or "Movies / entertainment" in top_categories:
        keep.append("Keep one planned movie or entertainment treat if it genuinely matters to you.")
    if any(word in interest_text for word in ["matcha", "coffee", "cafes", "cafe"]):
        keep.append("Keep cafe spending that feels intentional, like a planned study break.")
    if any(word in interest_text for word in ["sports", "gym", "fitness"]):
        keep.append("Keep sports or gym spending if it supports routine, health, or social life.")
    if not keep:
        keep.append("Keep the spending that clearly supports your studies, wellbeing, or best social plans.")

    if "Takeaway / eating out" in top_categories:
        reduce.append("Reduce unplanned takeaway after busy days by preparing two easy fallback meals.")
    if "Cafes / drinks" in top_categories:
        reduce.append("Reduce automatic cafe stops by choosing a weekly limit before the week starts.")
    if "Shopping" in top_categories:
        reduce.append("Reduce impulse shopping by putting non-urgent orders on a 24-hour pause.")
    if not reduce:
        reduce.append("Reduce one flexible category by a small amount rather than cutting everything.")

    if "Subscriptions" in top_categories:
        review.append("Review subscriptions for renewals, duplicate services, and student-plan options.")
    if "Groceries" in top_categories:
        review.append("Review grocery basics across Aldi, Lidl, Tesco, Sainsbury's, and Asda.")
    if "Transport" in top_categories:
        review.append("Review whether travel can be planned earlier to avoid expensive last-minute rides.")
    if not review:
        review.append("Review the top category once more after next week to see if it repeats.")

    return {"Keep": keep[:2], "Reduce": reduce[:2], "Review": review[:2]}


def detect_pattern(
    transactions: pd.DataFrame,
    top_categories: list[str],
    schedule: str,
) -> str:
    descriptions = " ".join(transactions["description"].astype(str)).lower()
    schedule_lower = schedule.lower()

    if "Takeaway / eating out" in top_categories and any(
        day in schedule_lower for day in ["tuesday", "thursday", "busy", "work", "uni", "university"]
    ):
        return (
            "Takeaway spending may be linked to busy or tiring days. Planning two easy meals before "
            "those days could reduce last-minute food orders."
        )

    if "Cafes / drinks" in top_categories and any(word in descriptions for word in ["starbucks", "costa", "pret", "matcha"]):
        return (
            "Cafe and drink purchases look like a repeated small-cost pattern. The individual amounts are small, "
            "but together they become a noticeable flexible spend."
        )

    if "Subscriptions" in top_categories:
        return (
            "Subscriptions are one of the bigger recurring areas. A quick renewal check could find savings without "
            "changing day-to-day student life much."
        )

    if top_categories:
        return f"Most of the spending is concentrated in {top_categories[0].lower()}, so that is the best place to inspect first."

    return "There is not enough transaction data yet to detect a strong pattern."


def student_recommendations(
    interests: str,
    goal: str,
    top_categories: list[str],
    category_totals: pd.DataFrame,
) -> list[str]:
    interest_text = interests.lower()
    goal_lower = goal.lower()
    recs = []

    if "save money" in goal_lower:
        recs.append("Prioritise one quick saving this week: reduce the highest flexible category by a small fixed amount.")
    if "stress" in goal_lower:
        recs.append("Look for spending linked to tiredness or stress, then prepare a cheaper fallback before that moment happens.")
    if "grocery" in goal_lower:
        recs.append("Use Aldi or Lidl for basics, then reserve Tesco or Sainsbury's for specific items you cannot get cheaper.")
    if "subscription" in goal_lower:
        recs.append("Check each subscription for student pricing, duplicate services, and renewal dates before cancelling anything.")
    if "spending habits" in goal_lower:
        recs.append("Focus on the pattern behind the spend: when it happens, what triggers it, and whether it matches your priorities.")

    if "Cafes / drinks" in top_categories or any(word in interest_text for word in ["matcha", "coffee", "cafe", "cafes"]):
        recs.append("Check cafe loyalty apps and student offers, then set a small weekly matcha/coffee limit.")
    if "Takeaway / eating out" in top_categories or any(word in interest_text for word in ["restaurant", "restaurants", "food"]):
        recs.append("Use UNiDAYS or Student Beans before eating out, and look for lunch menus or group offers.")
    if "Movies / entertainment" in top_categories or "movies" in interest_text:
        recs.append("Compare student cinema tickets, cheaper screening days, and whether streaming subscriptions overlap.")
    if "Sports / fitness" in top_categories or any(word in interest_text for word in ["sports", "gym", "fitness"]):
        recs.append("Look at university sports sessions, student gym rates, and second-hand sports kit before buying new.")
    if "Groceries" in top_categories or "groceries" in interest_text:
        recs.append("Compare weekly basics across Aldi, Lidl, Tesco, Sainsbury's, and Asda before the main shop.")
    if "Subscriptions" in top_categories:
        recs.append("Review one subscription this week and cancel, pause, or switch to a student plan if it is not useful.")

    if not recs:
        recs.append("Start with UNiDAYS, Student Beans, TOTUM, and supermarket loyalty schemes for easy student savings.")

    return recs[:5]


def weekly_actions(top_categories: list[str], goal: str, schedule: str) -> list[str]:
    actions = []
    goal_lower = goal.lower()

    if "save money" in goal_lower:
        actions.append("Pick one flexible category and set a realistic weekly cap before spending starts.")
    if "stress" in goal_lower:
        actions.append("Choose one stress-spend trigger and prepare a cheaper fallback before that situation happens.")
    if "smarter" in goal_lower or "enjoy" in goal_lower:
        actions.append("Choose one thing you genuinely enjoy and protect it, then reduce one lower-value spend.")
    if "grocery" in goal_lower:
        actions.append("Make a short basics list and compare it across Aldi, Lidl, and Tesco before shopping.")
    if "subscription" in goal_lower:
        actions.append("Open your subscriptions list and mark each one as keep, pause, cancel, or student-plan check.")
    if "spending habits" in goal_lower:
        actions.append("Write down the moment behind your top flexible spend: tired, social, convenience, or planned.")

    if "Cafes / drinks" in top_categories:
        actions.append("Set a cafe or matcha limit for the week and choose which days are worth it.")
    if "Takeaway / eating out" in top_categories:
        actions.append("Plan two low-effort dinners before your busiest days to reduce last-minute takeaway.")
    if "Subscriptions" in top_categories:
        actions.append("Review one subscription before renewal and decide whether to cancel, pause, or keep it.")
    if "Groceries" in top_categories:
        actions.append("Pick five weekly basics and compare them at Aldi, Lidl, and Tesco before shopping.")
    if "stress" in goal_lower:
        actions.append("Choose one spending trigger to watch this week, such as tiredness after university.")
    if schedule and not any("busy" in action.lower() for action in actions):
        actions.append("Mark one high-risk day from your schedule and prepare a cheaper option in advance.")

    while len(actions) < 3:
        fallback = [
            "Check Student Beans, UNiDAYS, or TOTUM before one planned purchase.",
            "Move one flexible purchase into a 24-hour pause list before buying.",
            "Do a 10-minute money check-in at the end of the week.",
        ]
        for item in fallback:
            if item not in actions:
                actions.append(item)
                break

    return actions[:3]


def draft_support_message(message_type: str, name: str) -> str:
    greeting = f"Hi {name}," if name else "Hi,"

    if message_type == "Subscription cancellation":
        return (
            f"{greeting}\n\n"
            "I would like to cancel my subscription before the next renewal date. "
            "Please confirm when the cancellation has been processed and that no further payments will be taken.\n\n"
            "Thank you."
        )

    if message_type == "Refund request":
        return (
            f"{greeting}\n\n"
            "I am writing to ask whether a refund is possible for my recent purchase. "
            "Please let me know what information you need from me to review the request.\n\n"
            "Thank you."
        )

    if message_type == "Student discount enquiry":
        return (
            f"{greeting}\n\n"
            "I wanted to ask whether you offer a student discount or any student-friendly deals. "
            "I can provide student ID or verification if needed.\n\n"
            "Thank you."
        )

    return (
        "Dear future me,\n\n"
        "This week I am focusing on one small money habit, not perfection. "
        "I will check my spending once, plan around my busiest day, and make one intentional saving choice.\n\n"
        "You've got this."
    )


def chat_response(
    user_message: str,
    result: AnalysisResult | None,
    profile: dict[str, Any],
    plans: list[dict[str, Any]],
) -> str:
    message = user_message.lower()
    name = profile.get("name") or "there"

    if any(word in message for word in ["hi", "hello", "hey"]):
        return (
            f"Hi {name}. I can help you understand your spending, explain the latest analysis, "
            "suggest student savings, or turn your results into a small weekly plan."
        )

    if any(word in message for word in ["privacy", "store", "stored", "data", "memory"]):
        saved_count = len(plans)
        return (
            "Budget Lens does not save raw transactions by default. It stores low-risk preferences "
            f"and saved weekly plans locally only when you choose. You currently have {saved_count} saved plan(s)."
        )

    if result is None:
        return (
            "Run an analysis first by loading sample spending or pasting anonymised transactions. "
            "Then I can answer questions about your top categories, savings, patterns, and weekly actions."
        )

    if any(word in message for word in ["top", "category", "categories", "biggest"]):
        return (
            f"Your top categories are {', '.join(result.top_categories)}. "
            f"Total analysed spending is {currency(result.total_spending)}."
        )

    if any(word in message for word in ["pattern", "habit", "why", "behaviour", "behavior"]):
        return (
            f"Your spending personality is {result.spending_personality}. "
            f"{result.personality_reason} Pattern detected: {result.pattern}"
        )

    if any(word in message for word in ["plan", "action", "next week", "what should i do"]):
        actions = "\n".join(f"{index}. {action}" for index, action in enumerate(result.actions, start=1))
        return f"Here are your 3 actions for the week:\n\n{actions}"

    if any(word in message for word in ["discount", "student", "deal", "cheaper", "alternative"]):
        recs = "\n".join(f"- {rec}" for rec in result.recommendations)
        return f"Here are the most relevant student-saving ideas:\n\n{recs}"

    if any(word in message for word in ["keep", "cut", "reduce", "review"]):
        sections = []
        for section, items in result.keep_reduce_review.items():
            joined = "\n".join(f"- {item}" for item in items)
            sections.append(f"{section}:\n{joined}")
        return "\n\n".join(sections)

    if any(word in message for word in ["save", "saving", "savings"]):
        reasons = " ".join(result.savings_explanation[:2])
        return (
            f"Your possible weekly saving is {currency(result.estimated_savings_low)}-"
            f"{currency(result.estimated_savings_high)}. {reasons}"
        )

    if any(word in message for word in ["subscription", "cancel", "email", "message", "draft"]):
        return result.draft_message

    if any(word in message for word in ["goal", "focus"]):
        return f"Your current goal is '{result.goal}'. Your goal focus is: {result.goal_focus}"

    return (
        "I can help with questions like: 'What are my top categories?', 'How can I save more?', "
        "'What pattern do you see?', 'What should I do next week?', or 'Draft a cancellation message'."
    )


def analyse(
    transactions: pd.DataFrame,
    goal: str,
    interests: str,
    schedule: str,
    message_type: str,
    name: str,
) -> AnalysisResult:
    totals = category_breakdown(transactions)
    total_spending = float(totals["amount"].sum()) if not totals.empty else 0.0
    top_categories = totals.head(3)["category"].tolist()
    low, high = estimate_savings(totals, goal, interests, schedule)
    personality, personality_reason = spending_personality(top_categories, transactions)
    pattern = detect_pattern(transactions, top_categories, schedule)
    recs = student_recommendations(interests, goal, top_categories, totals)
    actions = weekly_actions(top_categories, goal, schedule)
    draft = draft_support_message(message_type, name)

    return AnalysisResult(
        transactions=transactions,
        category_totals=totals,
        total_spending=total_spending,
        top_categories=top_categories,
        goal=goal,
        goal_focus=goal_focus(goal, top_categories),
        spending_personality=personality,
        personality_reason=personality_reason,
        keep_reduce_review=keep_reduce_review(top_categories, interests),
        savings_explanation=explain_savings(totals, goal, interests, schedule),
        estimated_savings_low=low,
        estimated_savings_high=high,
        pattern=pattern,
        recommendations=recs,
        actions=actions,
        draft_message=draft,
    )


def render_metric_row(result: AnalysisResult) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total spending", currency(result.total_spending))
    col2.metric("Transactions", len(result.transactions))
    col3.metric(
        "Possible weekly saving",
        f"{currency(result.estimated_savings_low)}-{currency(result.estimated_savings_high)}",
    )


def render_card(title: str, body: str, tone: str = "blue") -> None:
    st.markdown(
        f"""
        <div class="mm-card mm-card-{tone}">
            <div class="mm-card-title">{title}</div>
            <div class="mm-card-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_breakdown(result: AnalysisResult) -> None:
    display = result.category_totals.copy()
    display["Total"] = display["amount"].apply(currency)
    display["Share"] = display["percentage"].apply(lambda value: f"{value:.1f}%")
    st.dataframe(display[["category", "Total", "Share"]], use_container_width=True, hide_index=True)

    if not display.empty:
        chart_data = display.set_index("category")["amount"]
        st.bar_chart(chart_data)


def build_saved_plan(result: AnalysisResult, profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "goal": profile.get("goal", ""),
        "top_categories": result.top_categories,
        "actions": result.actions,
        "estimated_savings": f"{currency(result.estimated_savings_low)}-{currency(result.estimated_savings_high)}",
        "interests": profile.get("interests", ""),
    }


def weekly_plan_text(result: AnalysisResult, profile: dict[str, Any]) -> str:
    name = profile.get("name") or "Student"
    lines = [
        "Budget Lens weekly plan",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Name: {name}",
        f"Goal: {result.goal}",
        "",
        "Spending snapshot",
        f"- Total spending: {currency(result.total_spending)}",
        f"- Top categories: {', '.join(result.top_categories) or 'Not clear yet'}",
        f"- Spending personality: {result.spending_personality}",
        f"- Why: {result.personality_reason}",
        f"- Estimated possible saving: {currency(result.estimated_savings_low)}-{currency(result.estimated_savings_high)}",
        "",
        "Goal focus",
        f"- {result.goal_focus}",
        "",
        "Keep / Reduce / Review",
    ]

    for section, items in result.keep_reduce_review.items():
        lines.append(f"{section}:")
        for item in items:
            lines.append(f"- {item}")

    lines.extend(["", "Savings estimate is based on:"])
    lines.extend(f"- {item}" for item in result.savings_explanation)
    lines.extend(["", "Actions for next week:"])
    lines.extend(f"{index}. {action}" for index, action in enumerate(result.actions, start=1))
    lines.extend(
        [
            "",
            "Privacy note",
            "Budget Lens does not save raw transaction data by default. This is budgeting support, not professional financial advice.",
        ]
    )
    return "\n".join(lines)


def load_sample_text() -> str:
    if not SAMPLE_FILE.exists():
        return ""
    sample = pd.read_csv(SAMPLE_FILE)
    return "\n".join(
        f"{row['date']}, {row['description']}, £{float(row['amount']):.2f}"
        for _, row in sample.iterrows()
    )


def main() -> None:
    st.set_page_config(page_title="Budget Lens", page_icon="BL", layout="wide")
    st.markdown(
        """
        <style>
        :root {
            --mm-blue: #2563eb;
            --mm-blue-dark: #1e3a8a;
            --mm-blue-soft: #dbeafe;
            --mm-slate: #334155;
            --mm-grey: #64748b;
            --mm-border: #d8dee9;
            --mm-bg: #f4f7fb;
            --mm-panel: #ffffff;
        }

        .stApp {
            background: linear-gradient(180deg, #eef4ff 0%, #f7f9fc 38%, #f4f7fb 100%);
            color: var(--mm-slate);
        }

        .block-container {
            padding-top: 1.5rem;
            max-width: 1180px;
        }

        .mm-hero {
            border: 1px solid #c7d7ef;
            border-radius: 12px;
            padding: 26px 28px;
            margin-bottom: 18px;
            background:
                radial-gradient(circle at top right, rgba(37, 99, 235, 0.22), transparent 32%),
                linear-gradient(135deg, #f8fbff 0%, #e9f1ff 56%, #dce9fb 100%);
            box-shadow: 0 18px 40px rgba(30, 58, 138, 0.10);
        }

        .mm-kicker {
            color: var(--mm-blue);
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .mm-hero h1 {
            margin: 0;
            color: #0f172a;
            font-size: clamp(2.2rem, 4vw, 4.2rem);
            line-height: 1;
        }

        .mm-hero p {
            max-width: 720px;
            margin: 12px 0 0 0;
            color: #475569;
            font-size: 1.05rem;
            line-height: 1.55;
        }

        .mm-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 18px;
        }

        .mm-pill {
            border: 1px solid #c8d6ea;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.72);
            color: #24405f;
            font-size: 0.86rem;
            font-weight: 650;
            padding: 7px 11px;
        }

        .mm-card {
            min-height: 132px;
            border-radius: 10px;
            padding: 18px;
            border: 1px solid var(--mm-border);
            background: #ffffff;
            box-shadow: 0 12px 28px rgba(30, 58, 138, 0.07);
            margin-bottom: 14px;
        }

        .mm-card-blue {
            border-color: #b8cef4;
            background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%);
        }

        .mm-card-grey {
            border-color: #d7dee8;
            background: linear-gradient(180deg, #ffffff 0%, #f3f6fa 100%);
        }

        .mm-card-title {
            color: #0f172a;
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .mm-card-body {
            color: #334155;
            font-size: 1rem;
            line-height: 1.5;
        }

        .mm-empty {
            border: 1px dashed #b7c7df;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.66);
            padding: 22px;
            color: #475569;
            text-align: center;
        }

        h1 {
            color: #0f172a;
            font-weight: 800;
            letter-spacing: 0;
        }

        h2, h3 {
            color: #111827;
            letter-spacing: 0;
        }

        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3,
        div[data-testid="stMarkdownContainer"] h4 {
            color: #111827;
        }

        .small-note {
            color: var(--mm-grey);
            font-size: 0.92rem;
        }

        section[data-testid="stSidebar"] {
            background: #e8eef7;
            border-right: 1px solid var(--mm-border);
        }

        div[data-testid="stAlert"] {
            border-radius: 8px;
            border: 1px solid #bfdbfe;
            background: #eff6ff;
            color: #1e3a8a;
        }

        div[data-testid="stMetric"] {
            border: 1px solid var(--mm-border);
            border-radius: 8px;
            padding: 12px 14px;
            background: var(--mm-panel);
            box-shadow: 0 8px 20px rgba(30, 58, 138, 0.06);
        }

        div[data-testid="stMetric"] label {
            color: var(--mm-grey);
        }

        div[data-testid="stMetricValue"] {
            color: var(--mm-blue-dark);
        }

        .stButton > button {
            border-radius: 8px;
            border: 1px solid #b7c7df;
            color: #1f3351;
            background: #ffffff;
            min-height: 2.65rem;
            font-weight: 650;
        }

        .stButton > button:hover {
            border-color: var(--mm-blue);
            color: var(--mm-blue-dark);
            background: #eff6ff;
        }

        .stButton > button[kind="primary"] {
            background: var(--mm-blue);
            border-color: var(--mm-blue);
            color: white;
            font-weight: 700;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            background: #e8eef7;
            color: #334155;
            padding: 8px 14px;
        }

        .stTabs [aria-selected="true"] {
            background: var(--mm-blue);
            color: #ffffff;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--mm-border);
            border-radius: 8px;
            overflow: hidden;
        }

        textarea, input, [data-baseweb="select"] {
            border-radius: 8px;
        }

        div[data-testid="stFileUploader"] {
            border: 1px solid var(--mm-border);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.72);
            padding: 8px;
        }

        div[data-testid="stChatMessage"] {
            border-radius: 10px;
            border: 1px solid #d8e2f0;
            background: #ffffff;
            padding: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    memory = load_memory()
    profile = memory["profile"]

    st.markdown(
        """
        <section class="mm-hero">
            <div class="mm-kicker">Student money coach</div>
            <h1>Budget Lens</h1>
            <p>
                Turn messy student spending into clear patterns, realistic savings,
                discount ideas, and one calm weekly action plan.
            </p>
            <div class="mm-pill-row">
                <span class="mm-pill">Spending breakdown</span>
                <span class="mm-pill">Goal-aware savings</span>
                <span class="mm-pill">Student discounts</span>
                <span class="mm-pill">Local memory</span>
                <span class="mm-pill">Chat coach</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "Use anonymised sample data only. Budget Lens does not store raw financial data by default. "
        "Preferences and plans are saved locally only if you choose. This is budgeting support, not professional financial advice."
    )

    with st.sidebar:
        st.header("Memory")
        profile["name"] = st.text_input("Display name", value=profile.get("name", ""))
        profile["goal"] = st.text_input("Savings goal", value=profile.get("goal", ""))
        profile["interests"] = st.text_area("Interests", value=profile.get("interests", ""), height=90)
        profile["schedule"] = st.text_area("Schedule notes", value=profile.get("schedule", ""), height=90)
        profile["tone"] = st.selectbox(
            "Preferred tone",
            ["supportive and practical", "direct", "detailed"],
            index=["supportive and practical", "direct", "detailed"].index(
                profile.get("tone", "supportive and practical")
            )
            if profile.get("tone", "supportive and practical") in ["supportive and practical", "direct", "detailed"]
            else 0,
        )
        profile["watched_categories"] = st.text_area(
            "Categories to watch",
            value=profile.get("watched_categories", ""),
            height=80,
        )
        profile["wants_reminders"] = st.checkbox(
            "Suggest reminders",
            value=bool(profile.get("wants_reminders", True)),
        )

        if st.button("Save preferences", use_container_width=True):
            memory["profile"] = profile
            save_memory(memory)
            st.success("Preferences saved locally.")

        if st.button("Clear all saved data", use_container_width=True):
            memory = EMPTY_MEMORY.copy()
            save_memory(memory)
            st.success("Local memory cleared.")
            st.rerun()

    left, right = st.columns([1.25, 0.75])

    with left:
        st.header("Input")
        if "transaction_text" not in st.session_state:
            st.session_state.transaction_text = ""

        if st.button("Load sample student spending"):
            st.session_state.transaction_text = load_sample_text()

        transaction_text = st.text_area(
            "Paste anonymised transactions",
            value=st.session_state.transaction_text,
            height=260,
            placeholder="12 Jun, Tesco, £18.40\n13 Jun, Uber Eats, £21.99\n13 Jun, Starbucks, £5.20",
        )
        st.session_state.transaction_text = transaction_text

        uploaded_file = st.file_uploader("Optional CSV upload", type=["csv"])

    with right:
        st.header("Personalisation")
        goal_options = [
            "Spend smarter on things I enjoy",
            "Save money this week",
            "Reduce stress spending",
            "Cut grocery costs",
            "Reduce subscriptions",
            "Understand my spending habits",
        ]
        selected_goal = st.selectbox(
            "Goal",
            goal_options,
            index=goal_options.index(profile.get("goal", goal_options[0]))
            if profile.get("goal") in goal_options
            else 0,
        )
        custom_goal = st.text_input("Or type a custom goal", value="")
        interests = st.text_area("Student interests", value=profile.get("interests", ""), height=100)
        schedule = st.text_area("Weekly schedule", value=profile.get("schedule", ""), height=100)
        message_type = st.selectbox(
            "Draft message helper",
            [
                "Subscription cancellation",
                "Refund request",
                "Student discount enquiry",
                "Budget accountability message",
            ],
        )
        save_current_session = st.checkbox("Save preferences from this session", value=False)

    goal = custom_goal.strip() or selected_goal

    if st.button("Analyse spending", type="primary", use_container_width=True):
        transactions = parse_uploaded_csv(uploaded_file) if uploaded_file else parse_pasted_transactions(transaction_text)

        if transactions.empty:
            st.error("Add pasted transactions or upload a CSV to analyse.")
            return

        if save_current_session:
            profile["goal"] = goal
            profile["interests"] = interests
            profile["schedule"] = schedule
            memory["profile"] = profile
            save_memory(memory)

        result = analyse(
            transactions=transactions,
            goal=goal,
            interests=interests,
            schedule=schedule,
            message_type=message_type,
            name=profile.get("name", ""),
        )
        st.session_state.result = result

    result = st.session_state.get("result")
    if not result:
        st.markdown(
            """
            <div class="mm-empty">
                Load the sample student spending or paste anonymised transactions,
                then click <strong>Analyse spending</strong> to generate your Budget Lens report.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.header("Results")
    st.caption(f"Analysis goal: {result.goal}")
    render_metric_row(result)

    insight_col1, insight_col2 = st.columns([0.9, 1.1])
    with insight_col1:
        render_card(
            "Spending personality",
            f"<strong>{result.spending_personality}</strong><br>{result.personality_reason}",
            "blue",
        )
    with insight_col2:
        render_card("Goal focus", result.goal_focus, "grey")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Spending breakdown",
            "Pattern and recommendations",
            "Weekly action plan",
            "Chat with Budget Lens",
            "Memory and previous plans",
        ]
    )

    with tab1:
        st.subheader("Category breakdown")
        render_breakdown(result)
        st.subheader("Parsed transactions")
        st.dataframe(result.transactions, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Pattern detected")
        st.write(result.pattern)

        st.subheader("Keep / Reduce / Review")
        krr_cols = st.columns(3)
        for column, section in zip(krr_cols, ["Keep", "Reduce", "Review"]):
            with column:
                body = "<br>".join(f"- {item}" for item in result.keep_reduce_review[section])
                render_card(section, body, "blue" if section == "Keep" else "grey")

        st.subheader("Student discounts and alternatives")
        for rec in result.recommendations:
            st.write(f"- {rec}")

        st.subheader("Store price comparison")
        st.write(
            "If groceries are one of your pressure areas, compare basics before the weekly shop."
        )
        use_live_prices = st.checkbox(
            "Try live grocery price lookup",
            value=False,
            help="Uses SerpApi Google Shopping results if SERPAPI_API_KEY is set. Falls back to demo prices.",
        )
        if use_live_prices:
            live_prices, price_note = fetch_live_store_prices(tuple(GROCERY_COMPARISON_ITEMS))
            if live_prices is not None:
                st.dataframe(format_price_table(live_prices), use_container_width=True, hide_index=True)
                st.caption(price_note)
            else:
                st.warning(price_note)
                st.dataframe(format_price_table(MOCK_STORE_PRICES), use_container_width=True, hide_index=True)
        else:
            st.caption("Demo prices shown. Enable live lookup and set SERPAPI_API_KEY to query online shopping results.")
            st.dataframe(format_price_table(MOCK_STORE_PRICES), use_container_width=True, hide_index=True)

        if "Groceries" in result.top_categories:
            st.success(
                "Groceries are in your top categories. Switching some basics between Aldi, Lidl, and Tesco "
                "could save around £5-£15 per week."
            )

    with tab3:
        st.subheader("This week's plan")
        st.write(
            f"Your biggest flexible spending areas are {', '.join(result.top_categories) or 'not clear yet'}. "
            f"Because your goal is '{result.goal}', the actions below are tailored toward that. "
            f"Estimated possible saving: {currency(result.estimated_savings_low)}-{currency(result.estimated_savings_high)} this week."
        )
        for index, action in enumerate(result.actions, start=1):
            st.write(f"{index}. {action}")

        st.subheader("Why this saving estimate")
        for item in result.savings_explanation:
            st.write(f"- {item}")

        if profile.get("wants_reminders", True):
            st.caption("Reminder idea: check your plan before your busiest day and again at the end of the week.")

        st.subheader("Draft message")
        st.text_area("Generated draft", value=result.draft_message, height=190)

        if st.button("Save this plan"):
            memory = load_memory()
            memory["plans"].insert(0, build_saved_plan(result, profile))
            save_memory(memory)
            st.success("Plan saved locally. Raw transactions were not saved.")

        st.download_button(
            "Download weekly plan",
            data=weekly_plan_text(result, profile),
            file_name="budget-lens-weekly-plan.txt",
            mime="text/plain",
        )

    with tab4:
        st.subheader("Chat with Budget Lens")
        st.caption("Ask about your latest analysis. The chat uses local app context and does not save raw transactions.")

        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = [
                {
                    "role": "assistant",
                    "content": "Hi, I am Budget Lens. Ask me what your top spending categories are, how to save this week, or what pattern I noticed.",
                }
            ]

        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        prompt = st.chat_input("Ask Budget Lens about your spending")
        if prompt:
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            response = chat_response(prompt, result, profile, load_memory().get("plans", []))
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()

        if st.button("Clear chat"):
            st.session_state.chat_messages = [
                {
                    "role": "assistant",
                    "content": "Chat cleared. Ask me about your latest Budget Lens analysis.",
                }
            ]
            st.rerun()

    with tab5:
        st.subheader("Saved preferences")
        st.json(load_memory()["profile"])

        st.subheader("Previous plans")
        plans = load_memory().get("plans", [])
        if not plans:
            st.write("No saved plans yet.")
        for plan in plans:
            with st.expander(f"{plan['created_at']} - {plan['goal']}"):
                st.write(f"Top categories: {', '.join(plan['top_categories'])}")
                st.write(f"Estimated savings: {plan['estimated_savings']}")
                st.write("Actions:")
                for action in plan["actions"]:
                    st.write(f"- {action}")


if __name__ == "__main__":
    main()
