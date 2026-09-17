import os, json, time, uuid
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# --- YOUR CONFIGURATION ---
TOKEN = "8912481283:AAGQg8eH0e1EDFftYvJiLTC3uQZ2Xb5WLeM"
OWNER_ID = 8686609563
BOT_USERNAME = "kings_games_files_bot"

# Force Join Target Settings
CHANNELS = ["@dragochats", "@dragonetwork"]
DB_FILE = "db.json"
ADMIN_FILE = "admins.json"

# Temporary cache memory to handle link configuration steps
PENDING_CONFIGS = {}

# --- CORE DATABASE UTILITIES ---
def get_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, 'r') as f: 
        try: return json.load(f)
        except: return {}

def get_admins():
    if not os.path.exists(ADMIN_FILE): return []
    with open(ADMIN_FILE, 'r') as f:
        try: return json.load(f)
        except: return []

# --- MAIN MENU REPLY KEYBOARD ---
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("📝 File Sharing"), KeyboardButton("🔗 Link Management")],
        [KeyboardButton("ℹ️ Info"), KeyboardButton("❓ Help")],
        [KeyboardButton("🛠️ Support DM")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- FORCE JOIN VALIDATION SYSTEM ---
async def check(u, c):
    uid = u.effective_user.id
    # Owner and authorized Admins bypass force join checks completely
    if uid == OWNER_ID or uid in get_admins():
        return True
        
    for ch in CHANNELS:
        try:
            m = await c.bot.get_chat_member(ch, uid)
            if m.status in ['left', 'kicked']: return False
        except: return False
    return True

# --- /START ROUTE & DOWNLOAD VERIFICATION ---
async def start(u, c):
    db = get_db()
    if c.args and c.args[0] in db:
        # Enforce subscription validation if a regular user clicks a deep link
        if not await check(u, c):
            keyboard = [
                [InlineKeyboardButton("💬 Join DragoChats Group", url="https://t.me/dragochats")],
                [InlineKeyboardButton("📢 Join DragoNetwork Channel", url="https://t.me/dragonetwork")]
            ]
            await u.message.reply_text("⚠️ <b>Access Denied!</b>\nYou must join our network groups and channels to download files via this bot.", 
                reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
            return

        d = db[c.args[0]]
        user_id = u.effective_user.id
        
        # 1. OWNER BYPASS: Instantly bypass click/time constraints
        if user_id == OWNER_ID:
            await u.message.reply_document(d['id']) if d['type'] == 'doc' else await u.message.reply_video(d['id'])
            return
            
        # 2. TIME EXPRIATION CHECK
        if d.get('time_limit') is not None:
            elapsed = (time.time() - d['t']) / 60
            if elapsed > d['time_limit']:
                await u.message.reply_text("❌ This link has expired.")
                return

        # 3. CLICK LIMIT CHECK
        if d.get('user_limit') is not None:
            if d.get('clicks', 0) >= d['user_limit']:
                await u.message.reply_text("❌ Link limit reached! Maximum user capacity has been exhausted.")
                return

        # Update download tracking data logs
        d['clicks'] = d.get('clicks', 0) + 1
        db[c.args[0]] = d
        with open(DB_FILE, 'w') as f: json.dump(db, f)

        await u.message.reply_document(d['id']) if d['type'] == 'doc' else await u.message.reply_video(d['id'])
    else:
        await u.message.reply_text(
            "✨ <b>Welcome to ATP Network</b>\n\n"
            "Use the menu choices below or forward any file directly to start creating secure share links!\n\n"
            "© <b>Made by ATP Network</b>", 
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )

# --- TEXT BUTTON INTERACTION INTERCEPTOR ---
async def menu_text_handler(u, c):
    text = u.message.text
    
    if "file sharing" in text.lower():
        await u.message.reply_text(
            "📤 <b>File Sharing Mode:</b>\n"
            "Send or forward any <b>Document</b> or <b>Video</b> directly to this chat window. "
            "The bot will catch it and prompt you to establish your desired access configurations.",
            parse_mode="HTML"
        )
    elif "link management" in text.lower():
        await u.message.reply_text(
            "🔗 <b>Link Management:</b>\n"
            "Every uploaded asset converts into an cloud reference link. "
            "You can specify a max download limit (1-50 users) and custom expiration windows (5 mins to 1 day).",
            parse_mode="HTML"
        )
    elif "help" in text.lower():
        await u.message.reply_text(
            "❓ <b>How to Use:</b>\n\n"
            "1️⃣ Drop/Forward a file into this bot chat.\n"
            "2️⃣ Tap the custom access buttons to specify limits.\n"
            "3️⃣ Tap the time window parameter setup next.\n"
            "4️⃣ Your custom encrypted start link is ready!",
            parse_mode="HTML"
        )
    elif "info" in text.lower():
        await u.message.reply_text(
            "ℹ️ <b>System Status:</b>\n"
            "• Network Environment: <b>ATP Network</b>\n"
            "• Storage footprint: <b>0-byte Local Drive Utilization</b>\n"
            "• Performance architecture: Parallel network cloud streams.",
            parse_mode="HTML"
        )
    elif "support dm" in text.lower():
        await u.message.reply_text(
            "🛠️ <b>Support & Assistance:</b>\n"
            "If you hit any unexpected issues, contact support here: @atp_network",
            parse_mode="HTML"
        )

# --- FILE DETECTION (TRIGGERS INLINE CONFIGURATION KEYBOARDS) ---
async def file_h(u, c):
    if not await check(u, c):
        keyboard = [
            [InlineKeyboardButton("💬 Join DragoChats Group", url="https://t.me/dragochats")],
            [InlineKeyboardButton("📢 Join DragoNetwork Channel", url="https://t.me/dragonetwork")]
        ]
        await u.message.reply_text("⚠️ <b>Access Denied!</b>\nYou must subscribe to our channel layout to generate custom sharing assets.", 
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        return
    
    uid = u.effective_user.id
    file_id = (u.message.document or u.message.video).file_id
    file_type = 'doc' if u.message.document else 'vid'
    
    PENDING_CONFIGS[uid] = {'id': file_id, 'type': file_type}
    
    keyboard = [
        [InlineKeyboardButton("1 Person (Lowest)", callback_data="ulim_1"), InlineKeyboardButton("5 People", callback_data="ulim_5")],
        [InlineKeyboardButton("10 People", callback_data="ulim_10"), InlineKeyboardButton("50 People", callback_data="ulim_50")],
        [InlineKeyboardButton("♾ Unlimited", callback_data="ulim_0")]
    ]
    await u.message.reply_text(
        "<b>👥 Step 1/2: Download Accessibility Limits</b>\nHow many distinct users should be allowed to download this file?", 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode="HTML"
    )

# --- INLINE INTERACTIVE KEYBOARD PROCESSING ENGINE ---
async def button_callback(u, c):
    q = u.callback_query
    await q.answer()
    uid = u.effective_user.id
    data = q.data
    
    if uid not in PENDING_CONFIGS:
        await q.message.reply_text("❌ Session expired. Please upload your file again.")
        return
        
    if data.startswith("ulim_"):
        val = data.split("_")[1]
        PENDING_CONFIGS[uid]['user_limit'] = None if val == "0" else int(val)
        
        keyboard = [
            [InlineKeyboardButton("5 Mins (Lowest)", callback_data="tlim_5"), InlineKeyboardButton("15 Mins", callback_data="tlim_15")],
            [InlineKeyboardButton("1 Hour", callback_data="tlim_60"), InlineKeyboardButton("1 Day", callback_data="tlim_1440")],
            [InlineKeyboardButton("♾ Unlimited", callback_data="tlim_0")]
        ]
        await q.message.edit_text(
            "<b>⏰ Step 2/2: Lifespan Expiration Window</b>\nHow long should this generated download link remain active?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    elif data.startswith("tlim_"):
        val = data.split("_")[1]
        time_limit = None if val == "0" else int(val)
        
        # Structured file tracking identification code matching requested schema
        file_key = f"id_{uid}_{uuid.uuid4().hex[:4]}"
        db = get_db()
        
        db[file_key] = {
            'id': PENDING_CONFIGS[uid]['id'],
            'type': PENDING_CONFIGS[uid]['type'],
            't': time.time(),
            'user_limit': PENDING_CONFIGS[uid]['user_limit'],
            'time_limit': time_limit,
            'clicks': 0
        }
        
        with open(DB_FILE, 'w') as f: json.dump(db, f)
        del PENDING_CONFIGS[uid]
        
        await q.message.edit_text(
            f"✅ <b>Link successfully configured!</b>\n\n"
            f"🔗 <code>https://t.me/{BOT_USERNAME}?start={file_key}</code>", 
            parse_mode="HTML"
        )

# --- ADVANCED ADMINISTRATIVE MODULES ---

# [Owner Only] Add administrative user ids
async def add_admin(u, c):
    if u.effective_user.id != OWNER_ID: return
    if not c.args:
        await u.message.reply_text("❌ <b>Usage error:</b> Provide id parameter:\n<code>/addadmin USER_ID</code>", parse_mode="HTML")
        return
    try:
        aid = int(c.args[0])
        admins = get_admins()
        if aid not in admins:
            admins.append(aid)
            with open(ADMIN_FILE, 'w') as f: json.dump(admins, f)
        await u.message.reply_text(f"✅ User <code>{aid}</code> has been promoted to <b>Admin</b> status (Force-Join Bypassed).", parse_mode="HTML")
    except ValueError:
        await u.message.reply_text("❌ Provide numerical User ID only.")

# [Owner Only] Strip administrative credentials
async def del_admin(u, c):
    if u.effective_user.id != OWNER_ID: return
    if not c.args:
        await u.message.reply_text("❌ <b>Usage error:</b> Provide id parameter:\n<code>/deladmin USER_ID</code>", parse_mode="HTML")
        return
    try:
        aid = int(c.args[0])
        admins = get_admins()
        if aid in admins:
            admins.remove(aid)
            with open(ADMIN_FILE, 'w') as f: json.dump(admins, f)
        await u.message.reply_text(f"🗑️ User <code>{aid}</code> stripped from the admin registry successfully.", parse_mode="HTML")
    except ValueError:
        await u.message.reply_text("❌ Provide numerical User ID only.")

# [Owner Only] View active admins registry list
async def list_admins(u, c):
    if u.effective_user.id != OWNER_ID: return
    admins = get_admins()
    if not admins:
        await u.message.reply_text("ℹ️ No users registered inside the secondary admin registry database layer.")
        return
    res = "👥 <b>Registered Authorized Admins:</b>\n\n"
    for idx, adm in enumerate(admins, 1):
        res += f"{idx}. <code>{adm}</code>\n"
    await u.message.reply_text(res, parse_mode="HTML")

# [Owner & Admins] Monitor Bot Analytics
async def view_stats(u, c):
    uid = u.effective_user.id
    if uid != OWNER_ID and uid not in get_admins(): return
    
    db = get_db()
    total_links = len(db)
    total_downloads = sum(d.get('clicks', 0) for d in db.values())
    
    await u.message.reply_text(
        f"📊 <b>ATP Network Bot Analytics Dashboard</b>\n\n"
        f"• Total Active Sharing Keys: <b>{total_links}</b>\n"
        f"• Total Cumulative Download Hits: <b>{total_downloads}</b>\n"
        f"• Force Join Active Rules: <b>{len(CHANNELS)} environments monitored</b>",
        parse_mode="HTML"
    )

# [Owner Only] Instantly crash polling script on server engine
async def stop_bot(u, c):
    if u.effective_user.id == OWNER_ID:
        await u.message.reply_text("🛑 <b>Bot Server Terminated:</b> Disconnect polling processes...", parse_mode="HTML")
        os._exit(0)

# [Owner Only] Clean clear entire keys storage log array 
async def reset_db(u, c):
    if u.effective_user.id == OWNER_ID:
        with open(DB_FILE, 'w') as f: json.dump({}, f)
        await u.message.reply_text("🗑️ <b>Database Reset:</b> Every configured temporary link has been completely purged.", parse_mode="HTML")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).concurrent_updates(100).build()
    
    # Base Routes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO, file_h))
    
    # Advanced Admin System Handlers
    app.add_handler(CommandHandler("stop", stop_bot))
    app.add_handler(CommandHandler("reset", reset_db))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("deladmin", del_admin))
    app.add_handler(CommandHandler("admins", list_admins))
    app.add_handler(CommandHandler("stats", view_stats))
    
    # Text Interface Menu Handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_text_handler))
    
    print(f"ATP Network Advanced Management Bot Online as {BOT_USERNAME}")
    app.run_polling()
