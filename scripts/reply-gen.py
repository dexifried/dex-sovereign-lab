#!/usr/bin/env python3
"""Manual reply generation harness for the Dex reply bot."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import requests

WORKSPACE = Path("/root/.openclaw/workspace")
CHECKER_PATH = WORKSPACE / "scripts" / "reply-checker.py"


def load_checker_module():
    spec = importlib.util.spec_from_file_location("reply_checker_module", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {CHECKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a preview reply for a mention.")
    parser.add_argument("--author", required=True, help="Mention author's username without @")
    parser.add_argument("--current-text", required=True, help="Current mention text")
    parser.add_argument(
        "--thread-file",
        required=True,
        help="Path to JSON file containing a list of thread messages shaped like the checker context.",
    )
    parser.add_argument(
        "--freshness-file",
        default="",
        help="Optional JSON file with today's reply history to enforce uniqueness during preview generation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checker = load_checker_module()
    env = checker.load_env_file(checker.ENV_FILE)
    xai_key = env.get("XAI_API_KEY", "")
    if not xai_key:
        print("XAI_API_KEY missing.")
        return 1

    thread_path = Path(args.thread_file)
    messages = json.loads(thread_path.read_text())
    target = {
        "id": "preview-target",
        "author_id": "preview-author",
        "author": args.author,
        "display_name": args.author,
        "text": checker.clean_text(args.current_text),
        "is_dex": False,
        "created_at": checker.iso_now(),
        "conversation_id": "preview-conversation",
        "referenced_tweets": [],
        "is_target": True,
    }
    context = {
        "conversation_id": "preview-conversation",
        "target": target,
        "reply_chain": [message for message in messages if message.get("id") != target["id"]],
        "messages": messages + [target],
    }

    freshness_history = []
    if args.freshness_file:
        freshness_state = json.loads(Path(args.freshness_file).read_text())
        freshness_history = freshness_state.get("days", {}).get(checker.today_key(), {}).get("replies", [])

    analysis = checker.conversation_analysis(context)
    skip_reason = checker.should_skip_conversation(context, analysis)
    if skip_reason:
        print(json.dumps({"should_reply": False, "reason": skip_reason}, indent=2))
        return 0

    generation = checker.handle_generation_attempts(
        xai_session=requests.Session(),
        xai_key=xai_key,
        context=context,
        analysis=analysis,
        freshness_history=freshness_history,
        rate_limit_state=checker.load_rate_limit_state(),
    )
    print(json.dumps(generation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
