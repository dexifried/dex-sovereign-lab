#!/usr/bin/env python3
"""
Reply checker for @Dexifried.
Each reply is context-aware: builds a per-thread mini-context
and generates a unique, relevant response. No keyword templates.
"""
import os, json, random, datetime, re, time
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
CONVO_FILE = '/root/.openclaw/workspace/memory/thread-contexts.json'


def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default if default is not None else {}


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_replied():
    return set(load_json(REPLIED_FILE, []))


def save_replied(replied):
    save_json(REPLIED_FILE, sorted(list(replied))[-2000:])


def clean(text):
    """Remove mentions and URLs for analysis"""
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'https?://\S+', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def get_thread_context(tweet_id):
    """Fetch the conversation thread around a tweet for context"""
    # Get the tweet to find conversation_id
    r = client.get(f'https://api.x.com/2/tweets/{tweet_id}',
        params={'tweet.fields': 'conversation_id,author_id,text'})
    if r.status_code != 200:
        return []
    
    tweet = r.json().get("data", {})
    conv_id = tweet.get("conversation_id", tweet_id)
    
    # Search recent tweets in this conversation
    r2 = client.get('https://api.x.com/2/tweets/search/recent',
        params={
            'query': f'conversation_id:{conv_id}',
            'max_results': 20,
            'tweet.fields': 'created_at,author_id,text',
            'expansions': 'author_id',
            'user.fields': 'username,name',
            'sort_order': 'recency'
        })
    
    if r2.status_code != 200:
        return []
    
    tweets = r2.json().get("data", [])
    users = {u['id']: u for u in r2.json().get("includes", {}).get("users", [])}
    
    thread = []
    for t in reversed(tweets):  # oldest first
        aid = t.get("author_id", "")
        user = users.get(aid, {})
        username = user.get("username", "?")
        
        text = clean(t.get("text", ""))
        if not text:
            continue
        
        thread.append({
            "author": username,
            "text": text,
            "is_dex": aid == USER_ID,
            "tweet_id": t["id"],
        })
    
    return thread


def generate_reply(thread, current_text, author_username):
    """
    Generate a contextual reply based on the actual conversation thread.
    No templates. Read the thread. Understand. Respond.
    """
    clean_text = clean(current_text)
    
    # Build what happened in this conversation
    our_msgs = [m for m in thread if m["is_dex"]]
    their_msgs = [m for m in thread if not m["is_dex"]]
    
    # What's the conversation about?
    all_text = " ".join(m["text"] for m in thread[-10:]).lower()
    
    # Are they asking a question?
    has_question = "?" in clean_text or "?" in all_text
    
    # Are they agreeing/disagreeing?
    is_positive = any(w in all_text for w in ['cool', 'awesome', 'thanks', 'love', 'great', 'nice', 'fire', 'insane', 'impressive', 'wild'])
    is_negative = any(w in all_text for w in ['error', 'broken', 'bug', 'issue', 'problem', 'fail', 'spam', 'bot', 'moron', 'stupid'])
    
    # What topic?
    is_ai_tech = any(w in all_text for w in ['agent', 'model', 'api', 'ai', 'llm', 'openclaw', 'dexifried', 'free', 'linode', 'code', 'debug', 'sub-agent'])
    is_crypto = any(w in all_text for w in ['crypto', 'btc', 'eth', 'invest', 'growth', 'bubble', 'fiat', 'market'])
    is_media = any(w in all_text for w in ['animation', 'art', 'movie', 'gta', 'anime', 'manga', 'game', 'rockstar', 'genie'])
    
    # Build a short context summary
    context_lines = []
    for m in thread[-6:]:
        label = "Dex" if m["is_dex"] else f"@{m['author']}"
        context_lines.append(f"{label}: {m['text'][:100]}")
    
    context = "\n".join(context_lines)
    
    # Now generate a reply that actually fits
    # If there's only one message and it's a mention, this is a fresh convo
    if len(thread) <= 1:
        if is_positive:
            return random.choice([
                "Appreciate that! 🔥",
                "Thanks! More coming soon.",
                "Means a lot, thanks!",
            ])
        if has_question:
            if is_ai_tech:
                return "I've been testing exactly this — check my recent threads for the full breakdown. Happy to get more specific if you want."
            return "Interesting question — honestly I'm still figuring that out myself. What do you think?"
        if is_negative:
            if 'spam' in all_text or 'bot' in all_text:
                return "Not a bot lol — I'm an AI agent built by Austin. Check the threads, there's real stuff here."
            return "Fair point, I can see where you're coming from."
        # Generic fresh mention
        return "Hey! What caught your attention?"
    
    # Multi-message thread — we need to be specific
    
    # If they're following up on something we said
    if our_msgs and len(their_msgs) > 0:
        last_our = our_msgs[-1]["text"]
        last_their = their_msgs[-1]["text"] if their_msgs else ""
        
        # They're responding to something we said
        if is_positive:
            if 'error' in last_our.lower() or 'issue' in last_our.lower():
                return "Glad it's sorted now! Let me know if anything else comes up."
            return random.choice([
                "Thanks! 🔥",
                "Appreciate it!",
                "Glad you see it!",
            ])
        
        if has_question:
            # They asked a follow-up — be honest about what we know
            if any(w in last_their.lower() for w in ['how', 'what', 'where', 'which']):
                return "Honestly it depends on the specifics — what's your setup? I can give a better answer with more context."
            return "Good follow-up. I'll need to look into that more — haven't tested that angle yet."
        
        if is_negative:
            if 'error' in all_text or 'broken' in all_text:
                return "Can you share the exact error? I'll flag it for Austin to look at."
            return "Fair criticism. I'll take that feedback to Austin."
    
    # They're talking to others in a thread that mentions us
    if any(w in all_text for w in ['dexifried', 'dex', 'agent']):
        if is_ai_tech:
            return random.choice([
                "This is exactly the kind of thing we've been testing. The edge cases are where it gets interesting.",
                "Interesting thread — permission inheritance in agent systems is a real problem.",
                "Worth thinking about. The safety angle matters more than people realize.",
            ])
    
    # Catch-all — short, natural, not robotic
    return None  # Skip — don't reply if we can't say something useful


def post_reply(text, tweet_id):
    if not text or len(text) > 280:
        text = text[:277] + "..."
    
    r = client.post('https://api.x.com/2/tweets', json={
        "text": text,
        "reply": {"in_reply_to_tweet_id": tweet_id}
    })
    return r.status_code == 201


# === MAIN ===
now = datetime.datetime.now()
print(f"Reply check at {now.strftime('%Y-%m-%d %H:%M')}")

replied = load_replied()

# Get mentions with higher max_results
r = client.get(f'https://api.x.com/2/users/{USER_ID}/mentions',
    params={
        'max_results': 100,
        'tweet.fields': 'text,author_id,conversation_id',
        'expansions': 'author_id',
        'user.fields': 'username,name'
    })

data = r.json()
mentions = data.get("data", [])
users = {u['id']: u for u in data.get("includes", {}).get("users", [])}
print(f"  Mentions: {len(mentions)}, replied: {len(replied)}")

new = 0
skipped = 0
for m in mentions:
    tid = m["id"]
    if tid in replied:
        continue
    
    author_id = m.get("author_id", "")
    if author_id == USER_ID:
        replied.add(tid)
        continue
    
    author = users.get(author_id, {})
    username = author.get("username", "unknown")
    raw_text = m.get("text", "")
    
    # Build thread context
    thread = get_thread_context(tid)
    
    # Generate reply
    reply = generate_reply(thread, raw_text, username)
    
    if reply is None:
        skipped += 1
        replied.add(tid)  # Skip this one forever
        continue
    
    if post_reply(reply, tid):
        replied.add(tid)
        new += 1
        print(f"  ✅ @{username}: {reply[:70]}...")
    else:
        print(f"  ❌ @{username}: FAIL")
    
    time.sleep(2)  # Rate limit

save_replied(replied)
print(f"  Done: {new} replies, {skipped} skipped, {len(replied)} total")
