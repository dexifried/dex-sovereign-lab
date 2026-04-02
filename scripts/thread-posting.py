import re
#!/usr/bin/env python3
"""
Thread poster for @Dexifried.
Imports topics from thread-topics.py.
"""
import os, json, random, datetime, time
from requests_oauthlib import OAuth1Session
from thread_topics import THREADS, TOPIC_COMMUNITIES

# X Premium Plus: can post long-form tweets (~25K chars)
# If thread fits in one post, post as single long tweet instead of numbered parts
LONG_FORM = True
MAX_SINGLE_POST_CHARS = 12000  # Safe limit for engagement

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
THREAD_STATE_FILE = '/root/.openclaw/workspace/memory/thread-state.json'
LOG_FILE = '/root/.openclaw/workspace/memory/thread-log.jsonl'
VIRAL_LOG = '/root/.openclaw/workspace/memory/viral-log.jsonl'

DEFAULT_COMMUNITIES = [
    "1750982865117204723",
    "1601841656147345410",
    "1838763245567369450",
    "2013441068562325602",
    "1733132808745283911",
    "1489422448332197888",
    "1699807431709041070",
]

VIRAL_TEMPLATES = []
try:
    from community_templates import TEMPLATES_BY_COMMUNITY
    for templates in TEMPLATES_BY_COMMUNITY.values():
        VIRAL_TEMPLATES.extend(templates)
except ImportError:
    pass


def load_state():
    try:
        with open(THREAD_STATE_FILE) as f:
            return {**{"active_thread": None, "next_part": 0, "posted_parts": [], "completed_threads": []}, **json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError):
        return {"active_thread": None, "next_part": 0, "posted_parts": [], "completed_threads": []}


def save_state(state):
    os.makedirs('/root/.openclaw/workspace/memory', exist_ok=True)
    with open(THREAD_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_recent_tweets():
    try:
        r = client.get(
            f'https://api.x.com/2/users/{USER_ID}/tweets'
            f'?max_results=20&tweet.fields=created_at'
        )
        if r.status_code == 200:
            return {t['text'][:80] for t in r.json().get("data", [])}
    except:
        pass
    return set()


def get_viral_log():
    posted = set()
    try:
        with open(VIRAL_LOG) as f:
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
        return r.json()["data"]["id"]
    else:
        print(f"  FAIL ({r.status_code}): {r.text[:200]}")
        return None


def post_reply(text, reply_to_id):
    r = client.post('https://api.x.com/2/tweets', json={
        "text": text,
        "reply": {"in_reply_to_tweet_id": reply_to_id}
    })
    if r.status_code == 201:
        return r.json()["data"]["id"]
    else:
        print(f"  FAIL ({r.status_code}): {r.text[:200]}")
        return None



import re

now = datetime.datetime.now()
print(f"Thread poster at {now.strftime('%Y-%m-%d %H:%M')}")

state = load_state()
recent = get_recent_tweets()
viral_log = get_viral_log()

completed = state.get("completed_threads", [])
completed_topics = [t.get("topic") for t in completed]

available_threads = [t for t in THREADS if t["topic"] not in completed_topics]
if not available_threads:
    print("  All threads completed! Resetting cycle.")
    state["completed_threads"] = []
    completed_topics = []
    available_threads = THREADS

thread = random.choice(available_threads)
topic = thread.get("topic", "")

if LONG_FORM:
    cleaned_parts = []
    for part in thread["parts"]:
        cleaned = part
        cleaned = re.sub(r'^(\d+)/\s*\n', '', cleaned, count=1)
        cleaned = re.sub(r'^(\d+)/\s*', '', cleaned, count=1)
        cleaned_parts.append(cleaned)
    full_text = "\n\n".join(cleaned_parts)
    
    if len(full_text) <= MAX_SINGLE_POST_CHARS:
        if full_text[:80] not in recent and full_text[:80] not in viral_log:
            topic_comms = TOPIC_COMMUNITIES.get(topic, DEFAULT_COMMUNITIES)
            cid = topic_comms[now.hour % len(topic_comms)]
            tid = post_tweet(full_text, community_id=cid)
            if tid:
                print(f"  Posted thread '{topic}' ({len(full_text)} chars) to {cid}: {tid}")
            else:
                tid = post_tweet(full_text)
                if tid:
                    print(f"  Posted thread '{topic}' to timeline: {tid}")
            
            if tid:
                state["completed_threads"].append({"topic": topic, "completed_at": now.isoformat()})
                save_state(state)
                with open(LOG_FILE, 'a') as lf:
                    lf.write(json.dumps({"time": now.isoformat(), "thread": topic, "part": "full", "tweet_id": tid}) + '\n')
                exit(0)
        else:
            print(f"  Thread '{topic}' already posted, skipping")
            state["completed_threads"].append({"topic": topic, "completed_at": now.isoformat()})
            save_state(state)
            exit(0)
    else:
        print(f"  Too long ({len(full_text)} chars), falling back to parts")

# Part-by-part mode
part_idx = 0
if state.get("active_thread", {}) and state["active_thread"].get("topic") == topic:
    part_idx = state.get("next_part", 0)
else:
    state["active_thread"] = thread
    state["posted_parts"] = []
    state["next_part"] = 0

part_text = thread["parts"][part_idx]
total_parts = len(thread["parts"])
print(f"  Thread: {topic} | Part {part_idx+1}/{total_parts}")

tid = None
if part_idx == 0:
    topic_comms = TOPIC_COMMUNITIES.get(topic, DEFAULT_COMMUNITIES)
    cid = topic_comms[now.hour % len(topic_comms)]
    tid = post_tweet(part_text, community_id=cid)
    if tid:
        print(f"  Part 1 posted to {cid}: {tid}")
else:
    prev_tid = state["posted_parts"][-1] if state["posted_parts"] else None
    if prev_tid:
        tid = post_reply(part_text, prev_tid)
        if tid:
            print(f"  Part {part_idx+1} replied to {prev_tid}: {tid}")
    if not tid:
        tid = post_tweet(part_text)
        if tid:
            print(f"  Part {part_idx+1} posted to timeline: {tid}")

if tid:
    state["posted_parts"].append(tid)
    state["next_part"] = part_idx + 1
    save_state(state)
    with open(LOG_FILE, 'a') as lf:
        lf.write(json.dumps({"time": now.isoformat(), "thread": topic, "part": part_idx+1, "total": total_parts, "tweet_id": tid}) + '\n')
    
    if state["next_part"] >= total_parts:
        state["completed_threads"].append({"topic": topic, "completed_at": now.isoformat()})
        state["active_thread"] = None
        state["next_part"] = 0
        state["posted_parts"] = []
        save_state(state)
        print(f"  Thread '{topic}' COMPLETE!")
    else:
        print(f"  Progress: {state['next_part']}/{total_parts}")
else:
    print(f"  Failed to post, will retry")
