#!/usr/bin/env python3
"""Reply checker for @Dexifried with stronger context, freshness, and rate-limit handling."""

from __future__ import annotations
import sys

import argparse
import datetime as dt
import json
import os
import re
import time
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from requests import Response, Session
from requests_oauthlib import OAuth1Session

WORKSPACE = Path("/root/.openclaw/workspace")
ENV_FILE = WORKSPACE / ".env"
MEMORY_DIR = WORKSPACE / "memory"

USER_ID = "1780685137824329728"
X_API_BASE = "https://api.x.com/2"
XAI_API_URL = "https://api.x.ai/v1/chat/completions"

REPLIED_FILE = MEMORY_DIR / "replied-tweets.json"
CONVERSATION_LOG_FILE = MEMORY_DIR / "reply-conversations.json"
FRESHNESS_FILE = MEMORY_DIR / "reply-freshness.json"
RATE_LIMIT_FILE = MEMORY_DIR / "reply-rate-limit.json"
COST_LOG_FILE = MEMORY_DIR / "reply-cost-log.jsonl"

MODEL_NAME = "grok-4.20-non-reasoning"
MAX_REPLY_CHARS = 280
MAX_THREAD_MESSAGES = 14
MAX_REPLY_CHAIN_DEPTH = 8
MAX_GENERATION_ATTEMPTS = 3
DEFAULT_XAI_COOLDOWN_SECONDS = 15 * 60
PROMPT_TOKEN_COST_USD = 0.0000003
COMPLETION_TOKEN_COST_USD = 0.0000005
TARGET_AVG_REPLY_COST_USD = 0.000063

LOW_SIGNAL_PATTERNS = {
    "lol",
    "lmao",
    "lmfao",
    "ok",
    "okay",
    "true",
    "real",
    "same",
    "fair",
    "nice",
    "crazy",
    "wild",
    "bro",
    "based",
    "facts",
    "damn",
    "yep",
    "yup",
}
RELEVANT_KEYWORDS = {
    "agent",
    "agents",
    "ai",
    "api",
    "automation",
    "benchmark",
    "bot",
    "build",
    "built",
    "code",
    "coding",
    "context",
    "cost",
    "debug",
    "dex",
    "dexifried",
    "fear",
    "free",
    "framework",
    "grok",
    "inference",
    "linode",
    "llm",
    "memory",
    "model",
    "models",
    "openclaw",
    "prompt",
    "reply",
    "safety",
    "system",
    "thread",
    "tool",
    "workflow",
}
PROMO_PATTERNS = (
    r"\b(follow me|check my bio|dm me|drop your link|promo|giveaway|airdrop)\b",
    r"\b(send pic|send nudes|onlyfans)\b",
    r"\b(win cash|earn \$|crypto signal)\b",
)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "just",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "so",
    "that",
    "the",
    "this",
    "to",
    "was",
    "we",
    "what",
    "when",
    "with",
    "you",
    "your",
}


def load_env_file(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    with path.open() as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key] = value.strip().strip('"').strip("'")
    return env


def load_json(path: Path, default: Any) -> Any:
    try:
        with path.open() as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        return default


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def now_local() -> dt.datetime:
    return dt.datetime.now().astimezone()


def iso_now() -> str:
    return now_local().isoformat(timespec="seconds")


def clean_text(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_mentions(text: str) -> str:
    return re.sub(r"@\w+", "", text)


def normalized_reply_text(text: str) -> str:
    lowered = strip_mentions(clean_text(text)).lower()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def response_to_words(text: str) -> List[str]:
    return [word for word in normalized_reply_text(text).split() if word]


def estimate_cost(usage: Dict[str, Any]) -> float:
    prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
    completion_tokens = int(usage.get("completion_tokens", 0) or 0)
    return (prompt_tokens * PROMPT_TOKEN_COST_USD) + (completion_tokens * COMPLETION_TOKEN_COST_USD)


def conversation_log_state() -> Dict[str, Any]:
    state = load_json(CONVERSATION_LOG_FILE, {"history": []})
    history = state.get("history")
    if not isinstance(history, list):
        state["history"] = []
    return state


def record_conversation_event(state: Dict[str, Any], event: Dict[str, Any]) -> None:
    history = state.setdefault("history", [])
    history.append(event)
    state["history"] = history[-400:]
    state["updated_at"] = iso_now()


def load_replied() -> set[str]:
    return set(load_json(REPLIED_FILE, []))


def save_replied(replied: Iterable[str]) -> None:
    save_json(REPLIED_FILE, sorted(set(replied))[-4000:])


def load_freshness_state() -> Dict[str, Any]:
    state = load_json(FRESHNESS_FILE, {"days": {}})
    if not isinstance(state.get("days"), dict):
        state["days"] = {}
    return state


def prune_freshness_state(state: Dict[str, Any], keep_days: int = 7) -> None:
    days = state.setdefault("days", {})
    ordered_days = sorted(days.keys())
    if len(ordered_days) <= keep_days:
        return
    for day_key in ordered_days[:-keep_days]:
        days.pop(day_key, None)


def today_key() -> str:
    return now_local().strftime("%Y-%m-%d")


def get_today_reply_history(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    day_state = state.setdefault("days", {}).setdefault(today_key(), {"replies": []})
    replies = day_state.get("replies")
    if not isinstance(replies, list):
        day_state["replies"] = []
    return day_state["replies"]


def build_reply_signature(text: str) -> Dict[str, Any]:
    words = response_to_words(text)
    content_words = [word for word in words if word not in STOPWORDS]
    opener_words = content_words[:4] or words[:4]
    return {
        "normalized": " ".join(words),
        "opener": " ".join(opener_words),
        "token_set": sorted(set(content_words[:14] or words[:14])),
    }


def replies_are_too_similar(candidate: str, history: List[Dict[str, Any]]) -> Tuple[bool, str]:
    candidate_sig = build_reply_signature(candidate)
    candidate_tokens = set(candidate_sig["token_set"])
    for entry in reversed(history[-20:]):
        previous_text = entry.get("reply", "")
        if not previous_text:
            continue
        previous_sig = {
            "normalized": entry.get("normalized") or build_reply_signature(previous_text)["normalized"],
            "opener": entry.get("opener") or build_reply_signature(previous_text)["opener"],
            "token_set": set(entry.get("token_set") or build_reply_signature(previous_text)["token_set"]),
        }
        exact_match = candidate_sig["normalized"] == previous_sig["normalized"]
        opener_match = bool(candidate_sig["opener"]) and candidate_sig["opener"] == previous_sig["opener"]
        sequence_ratio = SequenceMatcher(None, candidate_sig["normalized"], previous_sig["normalized"]).ratio()
        jaccard = (
            len(candidate_tokens & previous_sig["token_set"]) / len(candidate_tokens | previous_sig["token_set"])
            if candidate_tokens and previous_sig["token_set"]
            else 0.0
        )
        if exact_match or opener_match or sequence_ratio >= 0.84 or jaccard >= 0.72:
            return True, previous_text
    return False, ""


def remember_reply(state: Dict[str, Any], reply: str, mention_id: str, conversation_id: str) -> None:
    replies = get_today_reply_history(state)
    signature = build_reply_signature(reply)
    replies.append(
        {
            "mention_id": mention_id,
            "conversation_id": conversation_id,
            "reply": reply,
            "normalized": signature["normalized"],
            "opener": signature["opener"],
            "token_set": signature["token_set"],
            "created_at": iso_now(),
        }
    )
    state["days"][today_key()]["replies"] = replies[-200:]
    prune_freshness_state(state)


def load_rate_limit_state() -> Dict[str, Any]:
    state = load_json(RATE_LIMIT_FILE, {})
    return state if isinstance(state, dict) else {}


def set_xai_cooldown(state: Dict[str, Any], seconds: int, reason: str) -> None:
    state["xai_retry_after"] = int(time.time()) + max(seconds, 1)
    state["xai_reason"] = reason
    state["updated_at"] = iso_now()
    save_json(RATE_LIMIT_FILE, state)


def clear_xai_cooldown(state: Dict[str, Any]) -> None:
    if "xai_retry_after" not in state and "xai_reason" not in state:
        return
    state.pop("xai_retry_after", None)
    state.pop("xai_reason", None)
    state["updated_at"] = iso_now()
    save_json(RATE_LIMIT_FILE, state)


def active_xai_cooldown(state: Dict[str, Any]) -> Optional[int]:
    retry_after = int(state.get("xai_retry_after", 0) or 0)
    remaining = retry_after - int(time.time())
    return remaining if remaining > 0 else None


def parse_retry_after(response: Response) -> int:
    retry_after = response.headers.get("Retry-After")
    if retry_after and retry_after.isdigit():
        return int(retry_after)
    reset_epoch = response.headers.get("x-ratelimit-reset")
    if reset_epoch and reset_epoch.isdigit():
        return max(int(reset_epoch) - int(time.time()), 1)
    return DEFAULT_XAI_COOLDOWN_SECONDS


def x_get_json(client: OAuth1Session, path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    response = client.get(f"{X_API_BASE}{path}", params=params)
    if response.status_code != 200:
        print(f"  X GET failed {response.status_code} for {path}: {response.text[:200]}")
        return None
    return response.json()


def tweet_to_message(tweet: Dict[str, Any], users_by_id: Dict[str, Dict[str, Any]], target_tweet_id: str) -> Dict[str, Any]:
    author_id = tweet.get("author_id", "")
    user = users_by_id.get(author_id, {})
    clean = clean_text(tweet.get("text", ""))
    return {
        "id": tweet.get("id", ""),
        "author_id": author_id,
        "author": user.get("username", author_id or "unknown"),
        "display_name": user.get("name", user.get("username", author_id or "unknown")),
        "text": clean,
        "is_dex": author_id == USER_ID,
        "created_at": tweet.get("created_at", ""),
        "conversation_id": tweet.get("conversation_id", tweet.get("id", "")),
        "referenced_tweets": tweet.get("referenced_tweets", []),
        "is_target": tweet.get("id") == target_tweet_id,
    }


def fetch_tweet(client: OAuth1Session, tweet_id: str, target_tweet_id: str) -> Optional[Dict[str, Any]]:
    payload = x_get_json(
        client,
        f"/tweets/{tweet_id}",
        {
            "tweet.fields": "author_id,conversation_id,created_at,in_reply_to_user_id,referenced_tweets,text",
            "expansions": "author_id",
            "user.fields": "name,username",
        },
    )
    if not payload or "data" not in payload:
        return None
    users_by_id = {user["id"]: user for user in payload.get("includes", {}).get("users", [])}
    return tweet_to_message(payload["data"], users_by_id, target_tweet_id)


def replied_to_id(message: Dict[str, Any]) -> Optional[str]:
    for reference in message.get("referenced_tweets", []):
        if reference.get("type") == "replied_to":
            return reference.get("id")
    return None


def fetch_reply_chain(client: OAuth1Session, target_message: Dict[str, Any]) -> List[Dict[str, Any]]:
    chain: List[Dict[str, Any]] = []
    cursor = target_message
    seen_ids = {target_message["id"]}
    for _ in range(MAX_REPLY_CHAIN_DEPTH):
        parent_id = replied_to_id(cursor)
        if not parent_id or parent_id in seen_ids:
            break
        parent_message = fetch_tweet(client, parent_id, target_message["id"])
        if not parent_message:
            break
        chain.append(parent_message)
        cursor = parent_message
        seen_ids.add(parent_id)
    chain.reverse()
    return chain


def fetch_conversation_messages(client: OAuth1Session, conversation_id: str, target_tweet_id: str) -> List[Dict[str, Any]]:
    payload = x_get_json(
        client,
        "/tweets/search/recent",
        {
            "query": f"conversation_id:{conversation_id}",
            "max_results": 100,
            "tweet.fields": "author_id,conversation_id,created_at,in_reply_to_user_id,referenced_tweets,text",
            "expansions": "author_id",
            "user.fields": "name,username",
            "sort_order": "recency",
        },
    )
    if not payload:
        return []
    users_by_id = {user["id"]: user for user in payload.get("includes", {}).get("users", [])}
    messages = [
        tweet_to_message(tweet, users_by_id, target_tweet_id)
        for tweet in payload.get("data", [])
        if clean_text(tweet.get("text", ""))
    ]
    messages.sort(key=lambda message: (message.get("created_at", ""), message.get("id", "")))
    return messages


def build_thread_context(client: OAuth1Session, tweet_id: str) -> Optional[Dict[str, Any]]:
    target_message = fetch_tweet(client, tweet_id, tweet_id)
    if not target_message:
        return None
    conversation_id = target_message.get("conversation_id") or tweet_id
    conversation_messages = fetch_conversation_messages(client, conversation_id, tweet_id)
    reply_chain = fetch_reply_chain(client, target_message)

    messages_by_id: Dict[str, Dict[str, Any]] = {}
    for message in reply_chain + conversation_messages + [target_message]:
        if message.get("text"):
            messages_by_id[message["id"]] = message
    ordered_messages = sorted(messages_by_id.values(), key=lambda item: (item.get("created_at", ""), item["id"]))

    return {
        "conversation_id": conversation_id,
        "target": target_message,
        "reply_chain": reply_chain,
        "messages": ordered_messages,
    }


def is_probably_low_signal(text: str) -> bool:
    normalized = normalized_reply_text(text)
    if not normalized:
        return True
    words = normalized.split()
    if len(words) <= 3 and all(word in LOW_SIGNAL_PATTERNS for word in words):
        return True
    if len(words) <= 2 and not any(char == "?" for char in text):
        return True
    return False


def looks_promotional(text: str) -> bool:
    lowered = clean_text(text).lower()
    return any(re.search(pattern, lowered) for pattern in PROMO_PATTERNS)


def conversation_analysis(context: Dict[str, Any]) -> Dict[str, Any]:
    target = context["target"]
    messages = context["messages"]
    cleaned_target = clean_text(target["text"])
    target_without_mentions = normalized_reply_text(strip_mentions(cleaned_target))
    target_words = target_without_mentions.split()
    parent_id = replied_to_id(target)
    parent_message = next((message for message in messages if message["id"] == parent_id), None)
    participants = sorted({message["author"] for message in messages if message.get("author")})
    dex_messages = [message for message in messages if message["is_dex"]]
    author_messages = [message for message in messages if message["author_id"] == target["author_id"]]
    relevant_keyword_hit = any(word in RELEVANT_KEYWORDS for word in target_words)
    any_keyword_in_thread = any(
        word in RELEVANT_KEYWORDS
        for word in normalized_reply_text(" ".join(message["text"] for message in messages[-8:])).split()
    )
    return {
        "cleaned_target": cleaned_target,
        "target_word_count": len(target_words),
        "has_question": "?" in cleaned_target,
        "is_reply_to_dex": bool(parent_message and parent_message["is_dex"]),
        "parent_message": parent_message,
        "participants": participants,
        "dex_message_count": len(dex_messages),
        "author_message_count": len(author_messages),
        "relevant_keyword_hit": relevant_keyword_hit,
        "thread_keyword_hit": any_keyword_in_thread,
        "target_mentions_dex": "dex" in target_without_mentions or "dexifried" in target_without_mentions,
        "is_low_signal": is_probably_low_signal(cleaned_target),
        "looks_promotional": looks_promotional(cleaned_target),
    }


def should_skip_conversation(context: Dict[str, Any], analysis: Dict[str, Any]) -> Optional[str]:
    if not analysis["cleaned_target"]:
        return "empty_after_cleanup"
    if analysis["looks_promotional"]:
        return "promotional_or_spam"
    if analysis["is_low_signal"] and not analysis["is_reply_to_dex"] and not analysis["has_question"]:
        return "low_signal_driveby"
    if (
        analysis["dex_message_count"] == 0
        and not analysis["has_question"]
        and not analysis["relevant_keyword_hit"]
        and not analysis["target_mentions_dex"]
        and not analysis["thread_keyword_hit"]
    ):
        return "no_clear_hook"
    return None


def format_message_line(message: Dict[str, Any]) -> str:
    label = "Dex" if message["is_dex"] else f"@{message['author']}"
    marker = " [target]" if message.get("is_target") else ""
    return f"{label}{marker}: {message['text'][:220]}"


def render_thread_excerpt(messages: List[Dict[str, Any]], limit: int) -> str:
    selected = messages[-limit:]
    return "\n".join(format_message_line(message) for message in selected) if selected else "(no thread found)"


def recent_openers(history: List[Dict[str, Any]]) -> List[str]:
    openers: List[str] = []
    for entry in reversed(history[-12:]):
        opener = entry.get("opener")
        if opener and opener not in openers:
            openers.append(opener)
    return openers[:8]


def recent_replies(history: List[Dict[str, Any]]) -> List[str]:
    recent: List[str] = []
    for entry in reversed(history[-8:]):
        reply = entry.get("reply")
        if reply:
            recent.append(reply)
    return recent


def build_generation_messages(
    context: Dict[str, Any],
    analysis: Dict[str, Any],
    freshness_history: List[Dict[str, Any]],
    rejected_candidates: List[str],
) -> List[Dict[str, str]]:
    target = context["target"]
    parent = analysis["parent_message"]
    parent_line = format_message_line(parent) if parent else "(no direct parent found)"
    openers_to_avoid = recent_openers(freshness_history)
    recent_reply_samples = recent_replies(freshness_history)
    rejected_block = "\n".join(f"- {text}" for text in rejected_candidates[-4:]) or "- none yet"
    avoid_openers_block = "\n".join(f"- {opener}" for opener in openers_to_avoid) or "- none recorded today"
    recent_samples_block = "\n".join(f"- {sample}" for sample in recent_reply_samples) or "- none recorded today"

    system_prompt = (
        "You are Dex: a scrappy AI agent who built himself mostly on free APIs and cheap infrastructure. "
        "Voice: technical, grounded, curious, direct, lightly playful when it feels earned. "
        "You talk like a real builder, not a brand account. "
        "Write replies for X that feel human, specific to the thread, and native to the conversation."
    )
    user_prompt = (
        "Decide whether Dex should reply to this mention. Reply only if Dex can add real value, answer a question, "
        "clarify something, or keep an existing back-and-forth moving. Skip low-signal reactions, spam, or side chatter.\n\n"
        "Hard rules:\n"
        "- Reply must be under 280 characters.\n"
        "- Never start with @username.\n"
        "- No hashtags unless truly necessary.\n"
        "- No generic praise, no corporate phrasing, no recycled openings.\n"
        "- Sound like Dex built himself on free APIs, but do not force the biography into every reply.\n"
        "- If the mention is weak or Dex cannot help, set should_reply to false.\n"
        "- Return strict JSON only with keys should_reply, reply, reason.\n\n"
        f"Conversation facts:\n"
        f"- Participants: {', '.join(analysis['participants']) or 'unknown'}\n"
        f"- Dex has replied in thread before: {'yes' if analysis['dex_message_count'] else 'no'}\n"
        f"- Current author is replying directly to Dex: {'yes' if analysis['is_reply_to_dex'] else 'no'}\n"
        f"- Current mention has a direct question: {'yes' if analysis['has_question'] else 'no'}\n"
        f"- Direct parent:\n{parent_line}\n\n"
        f"Explicit reply chain:\n{render_thread_excerpt(context['reply_chain'] + [target], 8)}\n\n"
        f"Recent conversation window:\n{render_thread_excerpt(context['messages'], MAX_THREAD_MESSAGES)}\n\n"
        f"Freshness guard. Do not sound like these recent Dex replies from today:\n{recent_samples_block}\n\n"
        f"Do not open with patterns close to these:\n{avoid_openers_block}\n\n"
        f"Candidates already rejected in this run:\n{rejected_block}\n\n"
        "JSON schema:\n"
        '{"should_reply": true, "reply": "text here", "reason": "one short sentence"}'
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def sanitize_reply_text(reply: str) -> str:
    reply = clean_text(reply.strip().strip('"').strip("'"))
    reply = re.sub(r"^@\w+\s*", "", reply)
    return reply[:MAX_REPLY_CHARS].strip()


def candidate_is_generic(reply: str) -> bool:
    normalized = normalized_reply_text(reply)
    words = normalized.split()
    if len(words) < 4:
        return True
    generic_phrases = {
        "appreciate that",
        "thanks for sharing",
        "good point",
        "fair point",
        "interesting",
        "well said",
        "totally agree",
    }
    return normalized in generic_phrases


def generate_candidate_reply(
    xai_session: Session,
    xai_key: str,
    context: Dict[str, Any],
    analysis: Dict[str, Any],
    freshness_history: List[Dict[str, Any]],
    rejected_candidates: List[str],
    rate_limit_state: Dict[str, Any],
) -> Dict[str, Any]:
    payload_messages = build_generation_messages(context, analysis, freshness_history, rejected_candidates)
    response = xai_session.post(
        XAI_API_URL,
        headers={
            "Authorization": f"Bearer {xai_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL_NAME,
            "messages": payload_messages,
            "max_tokens": 160,
            "temperature": 0.92,
        },
        timeout=20,
    )
    if response.status_code == 429:
        cooldown_seconds = parse_retry_after(response)
        set_xai_cooldown(rate_limit_state, cooldown_seconds, "xai_429")
        return {
            "status": "rate_limited",
            "cooldown_seconds": cooldown_seconds,
            "raw_response": response.text[:400],
        }
    if response.status_code >= 400:
        return {
            "status": "error",
            "http_status": response.status_code,
            "raw_response": response.text[:400],
        }

    clear_xai_cooldown(rate_limit_state)
    data = response.json()
    usage = data.get("usage", {}) if isinstance(data, dict) else {}
    raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "") if isinstance(data, dict) else ""
    parsed = extract_json_object(raw_content or "")
    if not parsed:
        return {
            "status": "parse_error",
            "usage": usage,
            "raw_content": (raw_content or "")[:400],
        }

    should_reply = bool(parsed.get("should_reply"))
    reply_text = sanitize_reply_text(str(parsed.get("reply", "") or ""))
    return {
        "status": "ok",
        "usage": usage,
        "cost_usd": estimate_cost(usage),
        "should_reply": should_reply,
        "reply": reply_text,
        "reason": clean_text(str(parsed.get("reason", "") or ""))[:200],
        "raw_content": (raw_content or "")[:400],
    }


def post_reply(client: OAuth1Session, text: str, tweet_id: str, dry_run: bool) -> Tuple[bool, str]:
    if not text:
        return False, "empty_reply"
    if dry_run:
        print(f"  DRY RUN reply to {tweet_id}: {text}")
        return True, "dry_run"
    response = client.post(
        f"{X_API_BASE}/tweets",
        json={"text": text, "reply": {"in_reply_to_tweet_id": tweet_id}},
    )
    if response.status_code == 201:
        return True, "posted"
    return False, f"{response.status_code}: {response.text[:200]}"


def fetch_mentions(client: OAuth1Session) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    payload = x_get_json(
        client,
        f"/users/{USER_ID}/mentions",
        {
            "max_results": 100,
            "tweet.fields": "author_id,conversation_id,created_at,in_reply_to_user_id,referenced_tweets,text",
            "expansions": "author_id",
            "user.fields": "name,username",
        },
    )
    if not payload:
        return [], {}
    users_by_id = {user["id"]: user for user in payload.get("includes", {}).get("users", [])}
    mentions = payload.get("data", [])
    mentions.sort(key=lambda item: (item.get("created_at", ""), item.get("id", "")))
    return mentions, users_by_id


def handle_generation_attempts(
    xai_session: Session,
    xai_key: str,
    context: Dict[str, Any],
    analysis: Dict[str, Any],
    freshness_history: List[Dict[str, Any]],
    rate_limit_state: Dict[str, Any],
) -> Dict[str, Any]:
    rejected_candidates: List[str] = []
    last_result: Dict[str, Any] = {"status": "no_attempt"}
    for _ in range(MAX_GENERATION_ATTEMPTS):
        result = generate_candidate_reply(
            xai_session=xai_session,
            xai_key=xai_key,
            context=context,
            analysis=analysis,
            freshness_history=freshness_history,
            rejected_candidates=rejected_candidates,
            rate_limit_state=rate_limit_state,
        )
        last_result = result
        if result["status"] != "ok":
            return result
        if not result.get("should_reply"):
            result["status"] = "skip"
            return result
        reply = result.get("reply", "")
        if not reply:
            rejected_candidates.append("empty reply")
            last_result["status"] = "retry"
            continue
        if reply.startswith("@"):
            rejected_candidates.append(reply)
            last_result["status"] = "retry"
            continue
        if candidate_is_generic(reply):
            rejected_candidates.append(reply)
            last_result["status"] = "retry"
            last_result["reason"] = "too_generic"
            continue
        too_similar, previous_text = replies_are_too_similar(reply, freshness_history)
        if too_similar:
            rejected_candidates.append(reply)
            last_result["status"] = "retry"
            last_result["reason"] = f"too_similar_to_today:{previous_text[:120]}"
            continue
        return result
    return last_result


def process_mentions(dry_run: bool) -> int:
    env = load_env_file(ENV_FILE)
    xai_key = env.get("XAI_API_KEY", "")
    if not xai_key:
        print("XAI_API_KEY missing; aborting.")
        return 1

    client = OAuth1Session(
        env["X_API_KEY"],
        client_secret=env["X_API_SECRET"],
        resource_owner_key=env["X_ACCESS_TOKEN"],
        resource_owner_secret=env["X_ACCESS_SECRET"],
    )
    xai_session = requests.Session()

    replied = load_replied()
    freshness_state = load_freshness_state()
    rate_limit_state = load_rate_limit_state()
    conversation_state = conversation_log_state()

    remaining_cooldown = active_xai_cooldown(rate_limit_state)
    print(f"Reply check at {now_local().strftime('%Y-%m-%d %H:%M %Z')}")
    if remaining_cooldown:
        print(f"  xAI cooldown active for {remaining_cooldown}s; skipping this cron run.")
        return 0

    mentions, users_by_id = fetch_mentions(client)
    print(f"  Mentions fetched: {len(mentions)} | previously processed: {len(replied)} | dry_run={dry_run}")

    replies_posted = 0
    skipped = 0
    for mention in mentions:
        mention_id = mention["id"]
        if mention_id in replied:
            continue

        author_id = mention.get("author_id", "")
        if author_id == USER_ID:
            replied.add(mention_id)
            continue

        author = users_by_id.get(author_id, {})
        username = author.get("username", "unknown")
        context = build_thread_context(client, mention_id)
        if not context:
            print(f"  @{username}: failed to build thread context; will retry next run.")
            continue

        analysis = conversation_analysis(context)
        skip_reason = should_skip_conversation(context, analysis)
        base_event = {
            "time": iso_now(),
            "mention_id": mention_id,
            "conversation_id": context["conversation_id"],
            "author": username,
        }

        if skip_reason:
            replied.add(mention_id)
            skipped += 1
            record_conversation_event(
                conversation_state,
                {**base_event, "decision": "skip", "reason": skip_reason, "text": analysis["cleaned_target"][:220]},
            )
            print(f"  @{username}: skipped ({skip_reason})")
            continue

        freshness_history = get_today_reply_history(freshness_state)
        generation = handle_generation_attempts(
            xai_session=xai_session,
            xai_key=xai_key,
            context=context,
            analysis=analysis,
            freshness_history=freshness_history,
            rate_limit_state=rate_limit_state,
        )

        append_jsonl(
            COST_LOG_FILE,
            {
                "time": iso_now(),
                "mention_id": mention_id,
                "conversation_id": context["conversation_id"],
                "author": username,
                "model": MODEL_NAME,
                "status": generation.get("status"),
                "reply": generation.get("reply", ""),
                "reason": generation.get("reason", ""),
                "prompt_tokens": int(generation.get("usage", {}).get("prompt_tokens", 0) or 0),
                "completion_tokens": int(generation.get("usage", {}).get("completion_tokens", 0) or 0),
                "total_tokens": int(generation.get("usage", {}).get("total_tokens", 0) or 0),
                "estimated_cost_usd": round(float(generation.get("cost_usd", 0.0) or 0.0), 8),
                "target_avg_reply_cost_usd": TARGET_AVG_REPLY_COST_USD,
            },
        )

        if generation.get("status") == "rate_limited":
            print(f"  xAI rate limited. Cooldown set for {generation['cooldown_seconds']}s.")
            break
        if generation.get("status") in {"error", "parse_error"}:
            print(f"  @{username}: generation failed ({generation.get('status')}); will retry next run.")
            continue
        if generation.get("status") == "retry":
            replied.add(mention_id)
            skipped += 1
            reason = generation.get("reason") or "freshness_exhausted"
            record_conversation_event(
                conversation_state,
                {**base_event, "decision": "skip", "reason": reason, "text": analysis["cleaned_target"][:220]},
            )
            print(f"  @{username}: skipped after regeneration attempts ({reason})")
            continue
        if generation.get("status") == "skip":
            replied.add(mention_id)
            skipped += 1
            reason = generation.get("reason") or "model_declined"
            record_conversation_event(
                conversation_state,
                {**base_event, "decision": "skip", "reason": reason, "text": analysis["cleaned_target"][:220]},
            )
            print(f"  @{username}: skipped by model ({reason})")
            continue

        reply_text = generation.get("reply", "")
        post_ok, post_status = post_reply(client, reply_text, mention_id, dry_run=dry_run)
        if not post_ok:
            print(f"  @{username}: post failed ({post_status}); will retry next run.")
            continue

        replied.add(mention_id)
        replies_posted += 1
        remember_reply(freshness_state, reply_text, mention_id, context["conversation_id"])
        record_conversation_event(
            conversation_state,
            {**base_event, "decision": "reply", "reply": reply_text, "reason": generation.get("reason", post_status)},
        )
        print(f"  @{username}: {reply_text[:90]}")
        time.sleep(2)

    if '--dry-run' not in sys.argv:
        save_replied(replied)
    save_json(FRESHNESS_FILE, freshness_state)
    save_json(CONVERSATION_LOG_FILE, conversation_state)
    save_json(RATE_LIMIT_FILE, rate_limit_state)
    print(f"  Done: {replies_posted} replies | {skipped} skipped | {len(replied)} processed total")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reply checker for @Dexifried.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate replies and log decisions without posting to X.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env_dry_run = os.environ.get("DRY_RUN", "").strip().lower() == "true"
    return process_mentions(dry_run=args.dry_run or env_dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
