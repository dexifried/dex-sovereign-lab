#!/usr/bin/env python3
"""
CRUD Auto-Monitor
Checks CRUD Snapchat group every 5 minutes.
Sends Discord updates on activity or inactivity.
Responds in CRUD style if there's something to respond to.
"""

import json
import time
import sys
import os
import urllib.request
import websocket

CDP_URL = "ws://localhost:9870/devtools/page/"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1469050762968699074/eLUJcfD18vo6kukOF7nRqg0PMUWy4psusL4dym5kDKdswq0C09frF7BOZ9wWMOxOuvgg"
CRUD_CHAT_URL = "https://www.snapchat.com/web/fade20a9-400d-4514-afb3-614e1678e8af"
ACTIVITY_LOG = "/root/.openclaw/workspace/memory/crud-activity-log.md"
INTERVAL = 300  # 5 minutes


def get_tab_id():
    resp = urllib.request.urlopen("http://localhost:9870/json/list")
    tabs = json.loads(resp.read())
    for t in tabs:
        if t.get("type") == "page" and "snapchat" in t.get("url", ""):
            return t["id"]
    return None


def send_discord(content):
    import subprocess
    try:
        subprocess.run(
            ["curl", "-s", "-X", "POST", DISCORD_WEBHOOK,
             "-H", "Content-Type: application/json",
             "-d", json.dumps({"content": content})],
            capture_output=True, timeout=10
        )
    except Exception as e:
        print(f"Discord error: {e}")


def ensure_crud_tab():
    tab_id = get_tab_id()
    if not tab_id:
        print("No Snapchat tab found")
        return None

    ws = websocket.create_connection(f"{CDP_URL}{tab_id}")

    # Check current URL
    ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": "document.location.href"}}))
    result = json.loads(ws.recv())
    url = result.get("result", {}).get("result", {}).get("value", "")

    if "fade20a9" not in url:
        ws.send(json.dumps({"id": 2, "method": "Page.navigate", "params": {"url": CRUD_CHAT_URL}}))
        ws.recv()
        time.sleep(4)

    return ws


def read_messages(ws):
    # Dismiss popup
    ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                        "params": {"expression": '(function(){ var btns=document.querySelectorAll("button"); for(var b of btns){ if(b.textContent.trim()==="Not now"){ b.click(); return "dismissed"; }} return "ok";})()'}}))
    ws.recv()

    # Scroll to bottom
    for i in range(15):
        ws.send(json.dumps({"id": i + 2, "method": "Input.dispatchMouseEvent",
                            "params": {"type": "mouseWheel", "x": 530, "y": 320, "deltaX": 0, "deltaY": 500}}))
        ws.recv()
        time.sleep(0.03)

    time.sleep(1)

    ws.send(json.dumps({"id": 100, "method": "Runtime.evaluate",
                        "params": {"expression": '(function(){ var chat=document.querySelector(".IBqK8"); if(!chat) return "no chat"; return chat.innerText.substring(chat.innerText.length - 1500); })()'}}))
    result = json.loads(ws.recv())
    return result.get("result", {}).get("result", {}).get("value", "")


def send_message(ws, text):
    escaped = text.replace('"', '\\"').replace("\\", "\\\\")
    ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                        "params": {"expression": f'(function(){{ var el=document.querySelector("div.euyIb"); if(!el) return "no input"; el.focus(); el.textContent="{escaped}"; el.dispatchEvent(new Event("input",{{bubbles:true}})); return "ok"; }})()'}}))
    ws.recv()
    time.sleep(0.3)

    for kt in ["keyDown", "keyUp"]:
        ws.send(json.dumps({"id": 2, "method": "Input.dispatchKeyEvent",
                            "params": {"type": kt, "key": "Enter", "code": "Enter",
                                       "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13}}))
        ws.recv()
    time.sleep(0.5)


def get_last_logged_message():
    try:
        with open(ACTIVITY_LOG, "r") as f:
            content = f.read()
        # Find last "Context:" entry to know what we've seen
        lines = content.strip().split("\n")
        for line in reversed(lines):
            if line.startswith("   - Context:") or line.startswith("   - Response:"):
                return line.strip()
        return ""
    except:
        return ""


def log_activity(entry):
    try:
        with open(ACTIVITY_LOG, "a") as f:
            f.write(f"\n{entry}")
    except Exception as e:
        print(f"Log error: {e}")


def extract_new_content(current_text, previous_text):
    if not previous_text:
        return ""
    # Find the last ME message to anchor
    me_idx = current_text.rfind("\nME\n")
    if me_idx < 0:
        return current_text[-300:]

    after_last_me = current_text[me_idx:]
    # Check if there's content after our last message
    my_responses = ["ya its destiney", "honestly idk", "prolly not", "but u never know",
                    "bro been keeping", "bet ill let", "its a girl", "due in may",
                    "shes good im good", "lifes wild", "appreciate it", "first crud baby",
                    "ill keep yall", "yo im alive"]

    for resp in my_responses:
        idx = after_last_me.lower().find(resp)
        if idx >= 0:
            after_resp = after_last_me[idx + len(resp):]
            # Find next ME or end
            next_me = after_resp.find("\nME\n")
            if next_me >= 0:
                after_resp = after_resp[:next_me]
            return after_resp.strip()

    return ""


def is_worth_responding(new_content):
    if not new_content or len(new_content.strip()) < 3:
        return False
    skip_phrases = ["New Snap", "Click to view", "Joined the call", "Left the call",
                    "Changed snaps", "Deleted a chat", "Saved a photo"]
    for phrase in skip_phrases:
        if phrase in new_content:
            new_content = new_content.replace(phrase, "")
    return len(new_content.strip()) > 5


def run_once():
    print("Ensuring CRUD tab...", flush=True)
    ws = ensure_crud_tab()
    if not ws:
        print("No tab found!", flush=True)
        send_discord("**CRUD Monitor** ❌\n\nCould not connect to Snapchat Chrome session.")
        return

    try:
        print("Reading messages...", flush=True)
        current_text = read_messages(ws)
        print(f"Read {len(current_text)} chars", flush=True)
        last_entry = get_last_logged_message()

        # Check if there's new content after our last sent message
        print("Extracting new content...", flush=True)
        new_content = extract_new_content(current_text, last_entry)
        print(f"New content: '{new_content[:100]}...'", flush=True)

        print("Checking if worth responding...", flush=True)
        worth = is_worth_responding(new_content)
        print(f"Worth responding: {worth}", flush=True)

        if worth:
            # Extract who said what
            print("Extracting senders...", flush=True)
            lines = new_content.strip().split("\n")
            senders = []
            messages = []
            current_sender = ""

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line in ["New Snap", "Click to view"]:
                    continue
                if line.upper() == line and len(line) > 2 and len(line) < 30:
                    current_sender = line
                else:
                    if current_sender:
                        senders.append(current_sender)
                        messages.append(line)
                        current_sender = ""

            print(f"Found {len(senders)} sender-message pairs", flush=True)

            if messages:
                summary_lines = []
                for i in range(min(len(senders), len(messages))):
                    summary_lines.append(f"**{senders[i]}:** {messages[i]}")

                summary = "\n".join(summary_lines[:5])
                print(f"Summary: {summary[:100]}", flush=True)

                print("Sending Discord...", flush=True)
                send_discord(f"**CRUD Update** 🔔\n\n{summary}\n\n⚠️ *Needs your input — waiting for response direction*")
                print("Discord sent.", flush=True)

                print("Logging...", flush=True)
                log_activity(f"\n### Auto-Monitor ({time.strftime('%H:%M')})\n- New messages detected:\n{summary}\n- Action: Deferred to Austin")
                print("Done.", flush=True)
        else:
            print("No new content worth responding to.", flush=True)
            send_discord(f"**CRUD Check** ✅ — Group quiet. No new messages at {time.strftime('%H:%M')}.")
            print("Discord sent.", flush=True)

    except Exception as e:
        print(f"Error: {e}")
        send_discord(f"**CRUD Monitor** ⚠️\n\nError: {str(e)[:100]}")
    finally:
        ws.close()


def main():
    print(f"CRUD Auto-Monitor started. Checking every {INTERVAL}s.", flush=True)
    send_discord("**CRUD Auto-Mode Started** ⚡️\n\nChecking every 5 min. Updates will come here.")

    # Run first check immediately
    print("Running first check...", flush=True)
    try:
        run_once()
        print("First check complete.", flush=True)
    except Exception as e:
        print(f"First check error: {e}", flush=True)

    while True:
        print(f"Sleeping {INTERVAL}s...", flush=True)
        time.sleep(INTERVAL)
        print("Running check...", flush=True)
        try:
            run_once()
            print("Check complete.", flush=True)
        except Exception as e:
            print(f"Cycle error: {e}", flush=True)


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        main()
