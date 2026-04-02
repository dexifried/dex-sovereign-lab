#!/usr/bin/env python3
"""
Viral tweet generator for @Dexifried.
Posts community-specific tweets with dedup checking.
"""
import os, json, random, datetime, hashlib
from requests_oauthlib import OAuth1Session
from community_templates import TEMPLATES_BY_COMMUNITY

env = {}
with open('/root/.openclaw/workspace/.env') as f:
    for line in f:
        if '=' in line:
            k, v = line.strip().split('=', 1)
            env[k] = v.strip('"').strip("'")

client = OAuth1Session(
    env["X_API_KEY"], client_secret=env["X_API_SECRET"],
    resource_owner_key=env["X_ACCESS_TOKEN"],
    resource_owner_secret=env["X_ACCESS_SECRET"]
)

USER_ID = "1780685137824329728"
LOG_FILE = '/root/.openclaw/workspace/memory/viral-log.jsonl'

# Weighted community list (big ones appear more)
COMMUNITY_IDS = [
    "1733132808745283911",  # Grok (big)
    "1733132808745283911",  # Grok (big)
    "1699807431709041070",  # Software Engineering (big)
    "1699807431709041070",  # Software Engineering (big)
    "1750982865117204723",  # AI community
    "1601841656147345410",  # Generative AI
    "1838763245567369450",  # RAG and AI Agent Developers
    "2013441068562325602",  # OpenClaw
]


def get_recent():
    r = client.get(
        f'https://api.x.com/2/users/{USER_ID}/tweets'
        f'?max_results=10&tweet.fields=created_at'
    )
    if r.status_code == 200:
        return {t['text'][:50] for t in r.json().get("data", [])}
    return set()


def get_posted_log():
    posted = set()
    try:
        with open(LOG_FILE) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    posted.add(entry.get("tweet", "")[:80])
                except:
                    pass
    except FileNotFoundError:
        pass
    return posted


def post_tweet(text, community_id=None):
    payload = {"text": text}
    if community_id:
        payload["community_id"] = community_id
        payload["share_with_followers"] = True
    r = client.post('https://api.x.com/2/tweets', json=payload)
    if r.status_code == 201:
        tid = r.json()["data"]["id"]
        return tid
    else:
        print(f"  FAIL ({r.status_code}): {r.text[:200]}")
        return None


def log_tweet(tweet, community_id, tid):
    os.makedirs('/root/.openclaw/workspace/memory', exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps({
            "time": datetime.datetime.now().isoformat(),
            "tweet": tweet[:300],
            "community": community_id,
            "tweet_id": tid
        }) + '\n')


# Main
now = datetime.datetime.now()
print(f"Viral tweet run at {now.strftime('%Y-%m-%d %H:%M')}")

recent = get_recent()
posted_log = get_posted_log()

# Pick community (changes hourly for variety)
comm_idx = now.hour % len(COMMUNITY_IDS)
cid = COMMUNITY_IDS[comm_idx]

# Get community-specific templates
templates = TEMPLATES_BY_COMMUNITY.get(cid, [])
if not templates:
    # Fallback: use all templates from any community
    templates = [t for group in TEMPLATES_BY_COMMUNITY.values() for t in group]

# Filter out duplicates
available = [t for t in templates
             if t[:50] not in recent
             and t[:80] not in posted_log]

if not available:
    print(f"  All templates for community {cid} used, picking oldest from log")
    available = templates

tweet = random.choice(available)
print(f"  Community: {cid}")
print(f"  Tweet: {tweet[:80]}...")

tid = post_tweet(tweet, community_id=cid)
if tid:
    log_tweet(tweet, cid, tid)
    print(f"  Posted: {tid}")
else:
    # Community post failed, try without community
    print(f"  Community post failed, trying timeline...")
    tid = post_tweet(tweet)
    if tid:
        log_tweet(tweet, None, tid)
        print(f"  Posted to timeline: {tid}")
