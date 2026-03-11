import os
from dotenv import load_dotenv
load_dotenv()
import asyncio
import httpx
import os
import csv
import time
import logging
import html
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    MessageHandler, 
    CommandHandler, 
    CallbackQueryHandler,
    filters
)
from telegram.error import BadRequest, RetryAfter

# ==========================================
# 📊 TELEMETRY & LOGGING INFRASTRUCTURE
# ==========================================
logging.basicConfig(
    format='%(asctime)s - 🛰️ DEX-BRIDGE - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger("SovereignUX")

# ==========================================
# 🔐 CONFIGURATION & NETWORK DNA
# ==========================================
TOKEN = os.getenv("TELEGRAM_TOKEN", "")

GATEKEEPER_URL = "http://localhost:8000/execute"
ARCHIVER_URL = "http://localhost:8000/archive"
CSV_PATH = os.path.expanduser("~/dex-local/intent_dataset.csv")

# 🧬 THE 7-INTENT MATRIX (V2.1)
INTENT_MATRIX = [
    "MEDICAL_SUPPORT", "AIDER_SURGERY", "STRATEGIC_PLANNER",
    "CODE_REVIEW", "IMAGE_GEN", "LOCAL_CMD", "SWARM_BROKER"
]

# ==========================================
# 🧠 PERSISTENT STATE & EPISODIC BUFFER
# ==========================================
last_user_prompt: Dict[int, str] = {}
last_bot_intent: Dict[int, str] = {}
chat_buffer: Dict[int, List[str]] = {}
BUFFER_LIMIT = 6 

# ==========================================
# 🎨 UI / UX RENDERER ENGINE
# ==========================================
class LiveStreamUI:
    """
    Advanced React-style state manager for Telegram messages.
    Buffers incoming tokens and throttles UI updates to 0.85s.
    Features an armor-plated fallback renderer to prevent HTML crashes.
    """
    def __init__(self, message, chat_id, context):
        self.msg = message
        self.chat_id = chat_id
        self.context = context
        self.intent = "ROUTING"
        self.raw_buffer = ""
        self.display_buffer = ""
        self.last_edit_time = time.time()
        self.start_time = time.time()
        self.update_interval = 0.85 
        self.part_counter = 1

    async def initialize(self):
        await self._render(force=True, initializing=True)
        await self.context.bot.send_chat_action(chat_id=self.chat_id, action=ChatAction.TYPING)

    def set_intent(self, intent_str: str):
        self.intent = intent_str

    async def ingest_chunk(self, chunk: str):
        self.raw_buffer += chunk
        self.display_buffer += chunk
        
        # 🦾 Terminal Clear Handling (For Aider 3060 feed)
        if "[CLEAR]" in self.display_buffer:
            self.display_buffer = self.display_buffer.split("[CLEAR]")[-1]

        now = time.time()
        if now - self.last_edit_time > self.update_interval:
            await self._render()
            self.last_edit_time = now

    async def finalize(self):
        elapsed = round(time.time() - self.start_time, 2)
        await self._render(force=True, final=True, elapsed=elapsed)

    async def _render(self, force=False, initializing=False, final=False, elapsed=0.0):
        if initializing:
            text = f"🧬 <b>[ MATRIX UPLINK ESTABLISHED ]</b>\n\n<i>Routing query through 7-Intent Architecture...</i> █"
            try:
                await self.msg.edit_text(text, parse_mode=ParseMode.HTML)
            except Exception: pass
            return

        cursor = "" if final else " █"
        header = f"🧠 <b>[ {self.intent} ]</b>"
        if self.part_counter > 1:
            header += f" <i>(Vol {self.part_counter})</i>"
            
        footer = f"\n\n<i>⏱️ Executed in {elapsed}s | Dex Sovereign Lab</i>" if final else ""

        # Telegram Hard Limit Defense (4096 chars)
        if len(self.display_buffer) > 3800:
            frozen_text = header + "\n\n" + html.escape(self.display_buffer) + "\n\n<b>[CONTINUED BELOW ⬇️]</b>"
            try:
                await self.msg.edit_text(frozen_text, parse_mode=ParseMode.HTML)
            except: pass
            
            self.display_buffer = ""
            self.part_counter += 1
            self.msg = await self.context.bot.send_message(
                chat_id=self.chat_id, 
                text=f"🧠 <b>[ {self.intent} ]</b> <i>(Vol {self.part_counter})</i>\n\n<i>Synchronizing...</i>", 
                parse_mode=ParseMode.HTML
            )
            return

        # Escape the body so python snippets with `<` or `>` don't break the HTML parser
        import re
        clean_display = re.sub(r"<think>.*?(?:</think>|$)", "", self.display_buffer, flags=re.DOTALL).strip()
        safe_body = html.escape(clean_display)
        final_text = f"{header}\n\n{safe_body}{cursor}{footer}"

        try:
            # Attempt highly formatted UI
            await self.msg.edit_text(final_text, parse_mode=ParseMode.HTML)
        except RetryAfter as e:
            logger.warning(f"Flood control: Pausing {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
        except BadRequest as e:
            # If the text didn't actually change, ignore it
            if "Message is not modified" in str(e):
                return
            
            logger.error(f"Render Fault (HTML Rejected): {e}")
            # 🛡️ ARMOR PLATED FALLBACK: If HTML breaks, instantly switch to Raw Text
            raw_text = final_text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
            try:
                await self.msg.edit_text(raw_text, parse_mode=None)
            except Exception as e2:
                logger.error(f"Render Fault (Raw Fallback Failed): {e2}")

# ==========================================
# 🗄️ BACKGROUND MEMORY FUSION
# ==========================================
async def flush_buffer_to_vault(uid: int, transcript_list: List[str]):
    transcript = "\n".join(transcript_list)
    try:
        async with httpx.AsyncClient() as client:
            await client.post(ARCHIVER_URL, json={"transcript": transcript}, timeout=15.0)
        logger.info(f"[+] Episodic buffer fused into Vault for UID {uid}.")
    except Exception as e:
        logger.error(f"[-] Vault Fusion Error: {e}")

# ==========================================
# ⚡ CORE MESSAGE HANDLER
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    if not text: return
    
    last_user_prompt[uid] = text
    if uid not in chat_buffer: chat_buffer[uid] = []
    chat_buffer[uid].append(f"User: {text}")
    
    initial_msg = await update.message.reply_text("🧬 Synchronizing...")
    ui = LiveStreamUI(initial_msg, update.effective_chat.id, context)
    await ui.initialize()
    
    try:
        # True Asynchronous Network Stream via httpx
        async with httpx.AsyncClient(timeout=900.0) as client:
            async with client.stream("POST", GATEKEEPER_URL, json={"prompt": text, "history": "\n".join(chat_buffer[uid][:-1])[-1500:]}) as response:
                
                async for chunk in response.aiter_text():
                    if not chunk: continue
                    
                    if chunk.startswith("AGENT:"):
                        parts = chunk.split("\n", 1)
                        detected_intent = parts[0].replace("AGENT:", "").strip()
                        last_bot_intent[uid] = detected_intent
                        ui.set_intent(detected_intent)
                        if len(parts) > 1 and parts[1]:
                            await ui.ingest_chunk(parts[1])
                        continue
                    
                    await ui.ingest_chunk(chunk)
        
        await ui.finalize()
        
        chat_buffer[uid].append(f"Dex ({ui.intent}): {ui.raw_buffer.strip()}")
        if len(chat_buffer[uid]) >= BUFFER_LIMIT:
            logger.info(f"[*] Memory Threshold Reached. Fusing buffer for {uid}...")
            asyncio.create_task(flush_buffer_to_vault(uid, chat_buffer[uid].copy()))
            chat_buffer[uid].clear()

    except httpx.ReadTimeout:
        await initial_msg.edit_text("❌ <b>[ TIMEOUT ]</b>\n\nThe Neural Network failed to respond in time.", parse_mode=ParseMode.HTML)
    except Exception as e: 
        logger.error(f"Core Link Failed: {e}")
        await initial_msg.edit_text(f"❌ <b>[ FATAL BRIDGE ERROR ]</b>\n\n<code>{str(e)[:200]}</code>", parse_mode=ParseMode.HTML)

# ==========================================
# 🧬 INTERACTIVE RLHF CORTEX (RICH UX)
# ==========================================
async def process_dna_mutation(message_obj, prompt_text: str, correct_intent: str, original_intent: str):
    """Core logic for appending to the CSV and generating the rich success readout."""
    try:
        def write_csv_and_count():
            # Append new DNA
            with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([prompt_text, correct_intent])
            # Calculate vault size
            with open(CSV_PATH, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
                
        vault_size = await asyncio.to_thread(write_csv_and_count)
        
        success_msg = (
            f"✅ <b>[ RLHF MATRIX UPDATED ]</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Target Query:</b> <i>\"{prompt_text}\"</i>\n"
            f"<b>Neural Shift:</b> {original_intent} ➡️ <b>{correct_intent}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧬 <b>Training Vault Size:</b> <code>{vault_size} Gold Samples</code>\n"
            f"<i>Awaiting scheduled Neural Bake.</i> 🦾"
        )
        await message_obj.edit_text(success_msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message_obj.edit_text(f"❌ <b>DNA Mutation Error:</b> <code>{e}</code>", parse_mode=ParseMode.HTML)

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    prompt_text = last_user_prompt.get(uid)
    original_intent = last_bot_intent.get(uid, "UNKNOWN")

    if not prompt_text:
        await update.message.reply_text("[-] <b>No volatile memory found.</b> Send a prompt first before attempting curation.", parse_mode=ParseMode.HTML)
        return

    # Fallback: If you type `/feedback MEDICAL_SUPPORT`, it does it instantly without the menu
    if context.args:
        correct_intent = context.args[0].upper()
        # Create a temporary message to edit
        tmp_msg = await update.message.reply_text("<i>Processing mutation...</i>", parse_mode=ParseMode.HTML)
        await process_dna_mutation(tmp_msg, prompt_text, correct_intent, original_intent)
        return

    # --- 🎛️ GENERATE THE TACTICAL TILE UI ---
    keyboard = []
    row = []
    # Build a 2-column mobile-friendly layout
    for i, intent in enumerate(INTENT_MATRIX):
        row.append(InlineKeyboardButton(intent, callback_data=f"RLHF_{intent}"))
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    if row: # Catch any odd remaining buttons
        keyboard.append(row)
        
    # Add a distinct cancel button at the bottom
    keyboard.append([InlineKeyboardButton("❌ Abort Curation", callback_data="RLHF_CANCEL")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    header_msg = (
        f"🧬 <b>TACTICAL DNA CURATION</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Query:</b> <i>\"{prompt_text}\"</i>\n"
        f"<b>Current Path:</b> <code>{original_intent}</code>\n\n"
        f"Select the true neural pathway to force-align the matrix:"
    )
    
    await update.message.reply_text(header_msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Catches the button presses from the Tactical Tile UI."""
    query = update.callback_query
    await query.answer() # Prevent the button from 'loading' forever
    
    data = query.data
    uid = update.effective_user.id
    
    if data == "RLHF_CANCEL":
        await query.edit_message_text("🛡️ <b>Curation Aborted.</b> Local DNA remains unchanged.", parse_mode=ParseMode.HTML)
        return

    correct_intent = data.replace("RLHF_", "")
    prompt_text = last_user_prompt.get(uid)
    original_intent = last_bot_intent.get(uid, "UNKNOWN")
    
    if not prompt_text:
        await query.edit_message_text("[-] <b>Session Expired.</b> Volatile memory flushed.", parse_mode=ParseMode.HTML)
        return
        
    # Execute the mutation using the unified function
    await process_dna_mutation(query.message, prompt_text, correct_intent, original_intent)

if __name__ == '__main__':
    logger.info("=========================================")
    logger.info("🛰️ DEX SOVEREIGN TELEGRAM BRIDGE ONLINE")
    logger.info("=========================================")
    
    app = ApplicationBuilder().token(TOKEN).connect_timeout(30.0).read_timeout(30.0).get_updates_read_timeout(42.0).build()
    
    # 🔗 Hooking up the handlers
    app.add_handler(CommandHandler("feedback", feedback_command))
    app.add_handler(CallbackQueryHandler(feedback_callback, pattern='^RLHF_'))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app.run_polling(drop_pending_updates=True)


