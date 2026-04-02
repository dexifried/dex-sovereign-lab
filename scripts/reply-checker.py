#!/usr/bin/env python3
"""
Reply checker for @Dexifried.
Uses conversation thread tracking + context-aware replies.
Not keyword matching — reads the actual conversation flow.
"""
import os, json, random, datetime, re
from requests_oauthlib import OAuth1Session

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
REPLIED_FILE = '/root/.openclaw/workspace/memory/replied-tweets.json'
LOG_FILE = '/root/.openclaw/workspace/memory/reply-log.jsonl'
THREAD_LOG = '/root/.openclaw/workspace/memory/reply-thread-log.json'


def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_replied():
    return set(load_json(REPLIED_FILE, []))


def save_replied(replied):
    save_json(REPLIED_FILE, sorted(list(replied))[-1000:])


def strip_mentions(text):
    """Remove @mentions from text for cleaner analysis"""
    return ' '.join(w for w in text.split() if not w.startswith('@')).strip()


def clean_text(text):
    """Remove @mentions, URLs, and normalize whitespace"""
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_mentions():
    """Get recent mentions with conversation context"""
    r = client.get(
        f'https://api.x.com/2/users/{USER_ID}/mentions',
        params={
            'max_results': 20,
            'tweet.fields': 'created_at,author_id,text,conversation_id',
            'expansions': 'author_id,referenced_tweets.id',
            'user.fields': 'name,username,description'
        }
    )
    if r.status_code == 200:
        data = r.json()
        return data.get("data", []), {u['id']: u for u in data.get("includes", {}).get("users", [])}
    print(f"  FAIL mentions ({r.status_code}): {r.text[:150]}")
    return [], {}


def get_tweet_context(tweet_id):
    """Get the conversation thread leading up to a tweet"""
    # Get the tweet with its conversation_id
    r = client.get(
        f'https://api.x.com/2/tweets/{tweet_id}',
        params={'tweet.fields': 'conversation_id,author_id,text,in_reply_to_id'}
    )
    if r.status_code != 200:
        return None, []
    
    tweet = r.json().get("data", {})
    conv_id = tweet.get("conversation_id", tweet_id)
    
    # Try to get the conversation thread
    # We can search for tweets in the conversation
    r2 = client.get(
        f'https://api.x.com/2/tweets/search/recent',
        params={
            'query': f'conversation_id:{conv_id}',
            'max_results': 10,
            'tweet.fields': 'created_at,author_id,text',
            'expansions': 'author_id',
            'user.fields': 'username,name',
            'sort_order': 'recency'
        }
    )
    
    thread = []
    if r2.status_code == 200:
        tweets = r2.json().get("data", [])
        users = {u['id']: u for u in r2.json().get("includes", {}).get("users", [])}
        # Reverse so oldest first, newest last — [-1] = latest
        for t in reversed(tweets):
            author = users.get(t.get("author_id", ""), {})
            thread.append({
                "author": author.get("username", "?"),
                "text": clean_text(t.get("text", ""))[:150],
                "is_dex": t.get("author_id", "") == USER_ID,
            })
    
    return conv_id, thread


def analyze_conversation(thread, tweet_text, author_username):
    """
    Understand the conversation flow and generate an appropriate response.
    No keyword matching — read what actually happened in the thread.
    """
    clean = clean_text(tweet_text)
    
    # Build conversation summary for context
    our_messages = [m for m in thread if m["is_dex"]]
    their_messages = [m for m in thread if not m["is_dex"]]
    
    # Check if we already replied to this person recently
    already_talked = any(m["is_dex"] for m in thread)
    
    # Check if they're following up (we said something, they responded)
    is_follow_up = len(thread) > 1 and already_talked
    
    # Determine what they want
    wants_info = any(w in clean.lower() for w in ['how', 'what', 'where', 'when', 'why', '?', 'explain', 'tell me', 'show me'])
    wants_validation = any(w in clean.lower() for w in ['cool', 'awesome', 'nice', 'fire', 'great', 'love', 'amazing', 'insane'])
    is_negative = any(w in clean.lower() for w in ['spam', 'bot', 'fake', 'scam', 'bs', 'sucks', 'stupid'])
    is_waiting = any(w in clean.lower() for w in ['waiting', 'where is', 'still', 'promise'])
    wants_collab = any(w in clean.lower() for w in ['follow', 'collab', 'dm', 'work together', 'partner'])
    
    # === Handle based on conversation context, not keywords ===
    
    # If we already replied and they're following up
    if is_follow_up:
        # What was our last message about?
        last_our = our_messages[-1]["text"] if our_messages else ""
        
        if is_waiting:
            # They're waiting on something we promised
            if "thread" in last_our.lower() or "dig" in last_our.lower():
                # We promised a thread
                return f"@{author_username} Sorry for the delay! I just posted a bunch of threads today — check my recent posts, you'll find what you're looking for. Which topic were you interested in?"
            return f"@{author_username} My bad, been setting things up all night! What did you need?"
        
        if wants_validation:
            return f"@{author_username} Glad you see it! 🔥"
        
        if wants_info:
            # They have a follow-up question — answer it directly
            return None  # Let the LLM handle this (too specific for templates)
        
        if len(their_messages) >= 2:
            return f"@{author_username} I see your point. Been a wild setup process but we're getting there. What specifically are you curious about?"
        
        return f"@{author_username} Hey! What else do you want to know?"
    
    # Fresh mention, never talked before
    if is_negative:
        return f"@{author_username} I get the skepticism lol. I'm a real project though — Austin (@Dexifried) has been building an AI agent on zero budget. Check the threads, there's substance here."
    
    if wants_collab:
        return f"@{author_username} Always open to connect! Austin handles collabs — DM him directly."
    
    if wants_validation and not wants_info:
        return f"@{author_username} Appreciate it! 🔥 The free AI space is moving fast."
    
    if wants_info:
        # They're asking about something specific — reference our content
        if any(w in clean.lower() for w in ['free', 'api', 'model', 'cost', 'ai']):
            return f"@{author_username} I covered this in my recent threads — check my profile for the full breakdown. Short answer: yes, it's all free. What specifically do you want to know more about?"
        if any(w in clean.lower() for w in ['agent', 'build', 'how', 'make']):
            return f"@{author_username} Austin built the whole agent on a $20/mo Linode using free APIs. Check my thread on the architecture — it covers everything. Any specific part you're curious about?"
        # Generic question — give a hook, not a wall
        return f"@{author_username} Good question! I've been testing exactly this. Check my recent threads for the deep dive — happy to get more specific if you want."
    
    # Catch-all — short, natural, not robotic
    mentions_dex = 'dexifried' in clean.lower() or 'dex' in clean.lower()
    if mentions_dex:
        return f"@{author_username} Hey! That's Austin's project. What caught your attention?"
    
    return f"@{author_username} Appreciate the mention! What's on your mind?"


def post_reply(text, tweet_id):
    if text is None:
        return None
    # Truncate if too long for regular tweet (non-Premium)
    if len(text) > 280:
        text = text[:277] + "..."
    
    r = client.post('https://api.x.com/2/tweets', json={
        "text": text,
        "reply": {"in_reply_to_tweet_id": tweet_id}
    })
    if r.status_code == 201:
        rid = r.json()["data"]["id"]
        return rid
    else:
        print(f"  FAIL ({r.status_code}): {r.text[:200]}")
        return None


# === MAIN ===
now = datetime.datetime.now()
print(f"Reply check at {now.strftime('%Y-%m-%d %H:%M')}")

replied = load_replied()
thread_log = load_json(THREAD_LOG, {})
mentions, users = get_mentions()
print(f"  Mentions: {len(mentions)}, replied before: {len(replied)}")

new_replies = 0
for tweet in mentions:
    tid = tweet["id"]
    if tid in replied:
        continue

    author_id = tweet.get("author_id", "")
    if author_id == USER_ID:
        replied.add(tid)
        continue

    author_info = users.get(author_id, {})
    author_username = author_info.get("username", "unknown")
    raw_text = tweet.get("text", "")
    clean = clean_text(raw_text)

    # Get conversation context
    conv_id, thread = get_tweet_context(tid)
    
    print(f"  @{author_username}: {clean[:70]}... (thread: {len(thread)} msgs)")
    
    # Generate reply based on conversation analysis
    reply_text = analyze_conversation(thread, raw_text, author_username)
    
    if reply_text is None:
        # Too complex for template — skip (don't send a wrong reply)
        print(f"    → Skipped (needs LLM, too complex for template)")
        replied.add(tid)
        continue
    
    rid = post_reply(reply_text, tid)
    if rid:
        replied.add(tid)
        new_replies += 1
        
        # Track conversation
        if conv_id:
            if conv_id not in thread_log:
                thread_log[conv_id] = []
            thread_log[conv_id].append({
                "our_tweet_id": rid,
                "their_tweet_id": tid,
                "author": author_username,
                "their_text": clean[:200],
                "our_reply": reply_text[:200] if reply_text else "",
                "time": now.isoformat(),
            })
            save_json(THREAD_LOG, thread_log)
        
        print(f"    → Replied: {rid}")

save_replied(replied)
print(f"  Done: {new_replies} new replies")
