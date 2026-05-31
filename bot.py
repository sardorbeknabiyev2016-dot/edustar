# ============================================================
#  O'RNATISH:
#  pip install "python-telegram-bot[job-queue]==21.5"
#
#  DOIM ISHLASHI UCHUN:
#  pythonw keep_alive.pyw   (yoki Windows Task Scheduler)
# ============================================================

import asyncio
import logging
import json
import os
from datetime import datetime, time as dtime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          ContextTypes, ConversationHandler, MessageHandler, filters)

# ===== SOZLAMALAR =====
BOT_TOKEN = "8749059584:AAFPsKW8HoEQ2h6sVDdAL_X9AhRDn2JXJHw"
ADMIN_ID  = 8587976365      # Sizning ID
USTOZ_ID  = 8114467851      # Ustozning ID
# ======================

ALLOWED = {ADMIN_ID, USTOZ_ID}

# To'lov ma'lumotlari saqlanadigan fayl
DATA_FILE = "tolov_data.json"

GROUPS = [
    {"id":"g1","name":"1-guruh","days":[0,2,4],"time":dtime(18,0),
     "students":["Xamidov Xojiakbar","Xamidov Ibrohim","Shaxboz","Imron",
                 "Xushvaqt","Robiya","Ziyoda","Fozilaxon"]},
    {"id":"g2","name":"2-guruh","days":[1,3,5],"time":dtime(10,0),
     "students":["Mustafo","Mubina","Abdufattoh","Hadicha","Said Kamol","Said Jalol"]},
    {"id":"g3","name":"3-guruh","days":[1,3,5],"time":dtime(17,30),
     "students":["Ibrohim","Ismoil","Shaxzod","Abdilaziz","Ruxsora","Mastura","Mubina"]},
    {"id":"g4","name":"4-guruh","days":[1,3,5],"time":dtime(16,0),
     "students":["Soliha","Ziyovuddin","Zahro","Zebo","Farzona","Soliha (2)","Iymona"]},
]
LESSON_MIN = 90
DAYS = ["Dushanba","Seshanba","Chorshanba","Payshanba","Juma","Shanba","Yakshanba"]
MONTHS = ["Yanvar","Fevral","Mart","Aprel","May","Iyun",
          "Iyul","Avgust","Sentabr","Oktabr","Noyabr","Dekabr"]

SELECT_GROUP, SELECT_STUDENT, TOLOV_MENU = range(3)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== MA'LUMOT SAQLASH ====================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"payments": {}}  # {"2025-06": {"g1": ["Imron", "Shaxboz"]}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def current_month_key():
    now = datetime.now()
    return f"{now.year}-{now.month:02d}"

def get_paid_list(gid):
    data = load_data()
    key = current_month_key()
    return data["payments"].get(key, {}).get(gid, [])

def mark_paid(gid, name):
    data = load_data()
    key = current_month_key()
    if key not in data["payments"]:
        data["payments"][key] = {}
    if gid not in data["payments"][key]:
        data["payments"][key][gid] = []
    if name not in data["payments"][key][gid]:
        data["payments"][key][gid].append(name)
    save_data(data)

def mark_unpaid(gid, name):
    data = load_data()
    key = current_month_key()
    try:
        data["payments"][key][gid].remove(name)
        save_data(data)
    except Exception:
        pass

# ==================== RUXSAT ====================
def allowed(update): return update.effective_user.id in ALLOWED

async def blocked(update):
    user = update.effective_user
    logger.warning(f"Taqiqlangan: {user.full_name} ({user.id})")
    try:
        await update.get_bot().send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ <b>Begona urinish!</b>\n\n"
                 f"👤 {user.full_name}\n"
                 f"🆔 <code>{user.id}</code>\n"
                 f"🕐 {datetime.now().strftime('%H:%M, %d.%m.%Y')}",
            parse_mode="HTML")
    except Exception: pass
    await update.message.reply_text(
        "🚫 <b>Kirishingiz taqiqlangan!</b>\n\n"
        "Bu bot faqat EduStar to'garak ustozi uchun.",
        parse_mode="HTML")

async def blocked_cb(query):
    await query.answer("🚫 Kirishingiz taqiqlangan!", show_alert=True)

# ==================== DARS NAZORATI ====================
async def check_lessons(ctx: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    wd  = now.weekday()
    cur = now.hour * 60 + now.minute
    for g in GROUPS:
        if wd not in g["days"]: continue
        st = g["time"].hour*60 + g["time"].minute
        en = st + LESSON_MIN
        eh, em = en//60, en%60
        if abs(cur - st) <= 1:
            msg = (f"🔔 <b>DARS BOSHLANDI!</b>\n\n"
                   f"📚 <b>{g['name']}</b>\n"
                   f"📅 {DAYS[wd]}, {now.strftime('%d.%m.%Y')}\n"
                   f"🕐 {g['time'].hour:02d}:{g['time'].minute:02d} → {eh:02d}:{em:02d}\n\n"
                   f"✅ Davomatni belgilang!")
            for uid in ALLOWED:
                try: await ctx.bot.send_message(uid, msg, parse_mode="HTML")
                except Exception: pass
        elif abs(cur - en) <= 1:
            msg = (f"⭐ <b>DARS TUGADI!</b>\n\n"
                   f"📚 <b>{g['name']}</b>\n"
                   f"📅 {DAYS[wd]}, {now.strftime('%d.%m.%Y')}\n\n"
                   f"📝 Baho qo'ying!\n📚 Uy vazifasini belgilang!")
            for uid in ALLOWED:
                try: await ctx.bot.send_message(uid, msg, parse_mode="HTML")
                except Exception: pass

# ==================== TO'LOV BOSH MENYU ====================
async def tolov_start(update, ctx):
    if not allowed(update):
        await blocked(update); return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("💳 Eslatma yuborish",    callback_data="t_send")],
        [InlineKeyboardButton("✅ To'ladi deb belgilash", callback_data="t_mark")],
        [InlineKeyboardButton("📊 To'lov holati",        callback_data="t_status")],
        [InlineKeyboardButton("⚠️ To'lamaganlar eslatmasi", callback_data="t_unpaid")],
        [InlineKeyboardButton("❌ Bekor",                callback_data="cancel")],
    ]
    now = datetime.now()
    await update.message.reply_text(
        f"💳 <b>To'lov Tizimi</b>\n"
        f"📅 {MONTHS[now.month-1]} {now.year}\n\n"
        f"Nima qilmoqchisiz?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard))
    return TOLOV_MENU

async def tolov_menu(update, ctx):
    query = update.callback_query
    if not allowed(update):
        await blocked_cb(query); return ConversationHandler.END
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Bekor qilindi.")
        return ConversationHandler.END

    ctx.user_data["tolov_action"] = query.data

    # Guruh tanlash
    keyboard = []
    for g in GROUPS:
        paid = get_paid_list(g["id"])
        total = len(g["students"])
        keyboard.append([InlineKeyboardButton(
            f"📚 {g['name']} — {len(paid)}/{total} to'lagan",
            callback_data=f"grp_{g['id']}")])
    keyboard.append([InlineKeyboardButton("❌ Bekor", callback_data="cancel")])

    action_names = {
        "t_send":   "💳 Eslatma yuborish",
        "t_mark":   "✅ To'ladi belgilash",
        "t_status": "📊 To'lov holati",
        "t_unpaid": "⚠️ To'lamaganlar eslatmasi",
    }
    action = action_names.get(query.data, "")

    if query.data == "t_status":
        # Bevosita holat ko'rsat
        now = datetime.now()
        txt = f"📊 <b>To'lov Holati — {MONTHS[now.month-1]} {now.year}</b>\n\n"
        for g in GROUPS:
            paid = get_paid_list(g["id"])
            unpaid = [s for s in g["students"] if s not in paid]
            txt += f"📚 <b>{g['name']}</b> ({len(paid)}/{len(g['students'])} to'lagan)\n"
            if paid:
                txt += f"  ✅ To'lagan: {', '.join(paid)}\n"
            if unpaid:
                txt += f"  ❌ To'lamagan: {', '.join(unpaid)}\n"
            txt += "\n"
        await query.edit_message_text(txt, parse_mode="HTML")
        return ConversationHandler.END

    if query.data == "t_unpaid":
        # To'lamaganlar uchun guruh tanlash
        await query.edit_message_text(
            f"⚠️ <b>To'lamaganlar Eslatmasi</b>\n\nQaysi guruh?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_GROUP

    await query.edit_message_text(
        f"<b>{action}</b>\n\nQaysi guruh?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_GROUP

async def select_group(update, ctx):
    query = update.callback_query
    if not allowed(update):
        await blocked_cb(query); return ConversationHandler.END
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Bekor qilindi.")
        return ConversationHandler.END

    gid = query.data.replace("grp_", "")
    g = next((x for x in GROUPS if x["id"] == gid), None)
    if not g:
        await query.edit_message_text("❌ Guruh topilmadi.")
        return ConversationHandler.END

    ctx.user_data["sel_grp"] = g
    action = ctx.user_data.get("tolov_action", "")

    paid   = get_paid_list(gid)
    unpaid = [s for s in g["students"] if s not in paid]

    # To'lamaganlar eslatmasi — to'g'ridan to'g'ri yuborish
    if action == "t_unpaid":
        if not unpaid:
            await query.edit_message_text(
                f"✅ <b>{g['name']}</b>\n\nHamma to'lovni amalga oshirgan! 🎉",
                parse_mode="HTML")
            return ConversationHandler.END

        now = datetime.now()
        names_str = "\n".join(f"  ❌ {s}" for s in unpaid)
        msg = (f"⚠️ <b>OYLIK TO'LOV ESLATMASI</b>\n\n"
               f"📚 Guruh: <b>{g['name']}</b>\n"
               f"📅 {MONTHS[now.month-1]} {now.year}\n\n"
               f"Quyidagilar hali to'lovni amalga oshirishmagan:\n\n"
               f"{names_str}\n\n"
               f"💰 Iltimos, to'lovni imkon qadar tezroq amalga oshiring!\n"
               f"📞 Savol bo'lsa ustozga murojaat qiling.")
        keyboard = [
            [InlineKeyboardButton("✅ Yuborish", callback_data="confirm_unpaid")],
            [InlineKeyboardButton("❌ Bekor",    callback_data="cancel")]
        ]
        ctx.user_data["pending_msg"] = msg
        ctx.user_data["sent_to"] = f"{g['name']} — to'lamaganlar ({len(unpaid)} kishi)"
        await query.edit_message_text(
            f"📋 <b>Ko'rib chiqing:</b>\n\n{msg}\n\n━━━━━━━━━\nYuborishni tasdiqlaysizmi?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_STUDENT

    # Boshqa amallar uchun o'quvchi tanlash
    keyboard = []
    if action in ("t_send",):
        keyboard.append([InlineKeyboardButton(
            f"👥 {g['name']} — HAMMASI", callback_data="stu_ALL")])
    for i, s in enumerate(g["students"]):
        if action == "t_mark":
            icon = "✅" if s in paid else "❌"
            keyboard.append([InlineKeyboardButton(
                f"{icon} {s}", callback_data=f"stu_{i}")])
        else:
            keyboard.append([InlineKeyboardButton(
                f"👤 {s}", callback_data=f"stu_{i}")])
    keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="back"),
                     InlineKeyboardButton("❌ Bekor",  callback_data="cancel")])

    hint = ""
    if action == "t_mark":
        hint = "\n✅ = to'lagan  ❌ = to'lamagan\nBosish bilan o'zgartiring"

    await query.edit_message_text(
        f"📚 <b>{g['name']}</b>\n{hint}\n\nKimni tanlaysiz?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_STUDENT

async def select_student(update, ctx):
    query = update.callback_query
    if not allowed(update):
        await blocked_cb(query); return ConversationHandler.END
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Bekor qilindi.")
        return ConversationHandler.END

    if query.data == "confirm_unpaid":
        msg     = ctx.user_data.get("pending_msg","")
        sent_to = ctx.user_data.get("sent_to","")
        now = datetime.now()
        await query.edit_message_text(
            f"✅ <b>Xabar yuborildi!</b>\n\n"
            f"📤 {sent_to}\n"
            f"🕐 {now.strftime('%H:%M, %d.%m.%Y')}\n\n"
            f"━━━━━━━━━\n{msg}",
            parse_mode="HTML")
        return ConversationHandler.END

    if query.data == "back":
        keyboard = []
        for g in GROUPS:
            paid = get_paid_list(g["id"])
            keyboard.append([InlineKeyboardButton(
                f"📚 {g['name']} — {len(paid)}/{len(g['students'])} to'lagan",
                callback_data=f"grp_{g['id']}")])
        keyboard.append([InlineKeyboardButton("❌ Bekor", callback_data="cancel")])
        await query.edit_message_text("Qaysi guruh?",
            reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_GROUP

    g      = ctx.user_data.get("sel_grp")
    action = ctx.user_data.get("tolov_action","")
    if not g:
        await query.edit_message_text("❌ Xato. /tolov dan qayta boshlang.")
        return ConversationHandler.END

    now = datetime.now()
    month_str = f"{MONTHS[now.month-1]} {now.year}"

    # To'ladi belgilash
    if action == "t_mark":
        idx  = int(query.data.replace("stu_",""))
        name = g["students"][idx]
        paid = get_paid_list(g["id"])
        if name in paid:
            mark_unpaid(g["id"], name)
            status = "❌ To'lamagan deb belgilandi"
        else:
            mark_paid(g["id"], name)
            status = "✅ To'lagan deb belgilandi"

        # Yangilangan ro'yxat bilan qaytish
        paid_new = get_paid_list(g["id"])
        keyboard = []
        for i, s in enumerate(g["students"]):
            icon = "✅" if s in paid_new else "❌"
            keyboard.append([InlineKeyboardButton(
                f"{icon} {s}", callback_data=f"stu_{i}")])
        keyboard.append([InlineKeyboardButton("◀️ Orqaga", callback_data="back"),
                         InlineKeyboardButton("❌ Yopish",  callback_data="cancel")])
        await query.edit_message_text(
            f"📚 <b>{g['name']}</b>\n"
            f"<i>{status}: {name}</i>\n\n"
            f"✅ = to'lagan  ❌ = to'lamagan",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_STUDENT

    # Eslatma yuborish
    if query.data == "stu_ALL":
        unpaid = [s for s in g["students"] if s not in get_paid_list(g["id"])]
        if unpaid:
            names = "\n".join(f"  ❌ {s}" for s in unpaid)
            note = f"\n⚠️ Hali to'lamaganlar:\n{names}\n"
        else:
            note = "\n✅ Hammasi to'lagan!\n"
        msg = (f"💳 <b>OYLIK TO'LOV ESLATMASI</b>\n\n"
               f"📚 Guruh: <b>{g['name']}</b>\n"
               f"📅 {month_str}\n{note}\n"
               f"💰 To'lovni o'z vaqtida amalga oshiring!\n"
               f"📞 Savol bo'lsa ustozga murojaat qiling.")
        label = f"Barcha — {g['name']}"
    else:
        idx  = int(query.data.replace("stu_",""))
        name = g["students"][idx]
        msg = (f"💳 <b>OYLIK TO'LOV ESLATMASI</b>\n\n"
               f"👤 O'quvchi: <b>{name}</b>\n"
               f"📚 Guruh: <b>{g['name']}</b>\n"
               f"📅 {month_str}\n\n"
               f"⚠️ <b>{name}</b>, oylik to'lovni amalga oshiring!\n\n"
               f"💰 To'lovni o'z vaqtida amalga oshiring!\n"
               f"📞 Savol bo'lsa ustozga murojaat qiling.")
        label = f"{name} ({g['name']})"

    ctx.user_data["pending_msg"] = msg
    ctx.user_data["sent_to"]     = label
    keyboard = [
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm")],
        [InlineKeyboardButton("❌ Bekor",      callback_data="cancel")]
    ]
    await query.edit_message_text(
        f"📋 <b>Ko'rib chiqing:</b>\n\n{msg}\n\n━━━━━━━━━\nYuborishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_STUDENT

async def confirm_send(update, ctx):
    query = update.callback_query
    if not allowed(update):
        await blocked_cb(query); return ConversationHandler.END
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("❌ Bekor qilindi.")
        return ConversationHandler.END
    msg     = ctx.user_data.get("pending_msg","")
    sent_to = ctx.user_data.get("sent_to","")
    now     = datetime.now()
    await query.edit_message_text(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"📤 {sent_to}\n"
        f"🕐 {now.strftime('%H:%M, %d.%m.%Y')}\n\n"
        f"━━━━━━━━━\n{msg}",
        parse_mode="HTML")
    return ConversationHandler.END

# ==================== BUYRUQLAR ====================
async def cmd_start(update, ctx):
    if not allowed(update): await blocked(update); return
    cid = update.effective_chat.id
    await update.message.reply_text(
        f"👋 Salom!\n\n🎓 <b>EduStar To'garak Boti</b>\n\n"
        f"✅ Kirish huquqi bor.\n📌 ID: <code>{cid}</code>\n\n"
        f"📋 <b>Buyruqlar:</b>\n"
        f"/jadval — Dars jadvali\n"
        f"/status — Hozirgi holat\n"
        f"/tolov — To'lov tizimi\n"
        f"/oquvchilar — Ro'yxat",
        parse_mode="HTML")

async def cmd_jadval(update, ctx):
    if not allowed(update): await blocked(update); return
    txt = "📅 <b>Dars Jadvali</b>\n\n"
    for g in GROUPS:
        days = ", ".join(DAYS[d] for d in g["days"])
        en = g["time"].hour*60 + g["time"].minute + LESSON_MIN
        txt += (f"📚 <b>{g['name']}</b>\n"
                f"   👥 {len(g['students'])} o'q  |  {days}\n"
                f"   🕐 {g['time'].hour:02d}:{g['time'].minute:02d} → {en//60:02d}:{en%60:02d}\n\n")
    await update.message.reply_text(txt, parse_mode="HTML")

async def cmd_status(update, ctx):
    if not allowed(update): await blocked(update); return
    now = datetime.now()
    cur = now.hour*60 + now.minute; wd = now.weekday()
    txt = f"🟢 Bot ishlayapti — {now.strftime('%H:%M, %d.%m.%Y')}\n\n"
    found = False
    for g in GROUPS:
        if wd not in g["days"]: continue
        st = g["time"].hour*60 + g["time"].minute
        if st <= cur <= st+LESSON_MIN:
            txt += f"📚 <b>{g['name']}</b> — dars davom etmoqda!\n"; found=True
    if not found: txt += "😴 Hozir hech qaysi guruhda dars yo'q"
    await update.message.reply_text(txt, parse_mode="HTML")

async def cmd_oquvchilar(update, ctx):
    if not allowed(update): await blocked(update); return
    txt = "👥 <b>Barcha O'quvchilar</b>\n\n"
    for g in GROUPS:
        txt += f"📚 <b>{g['name']}</b>:\n"
        for i,s in enumerate(g["students"],1): txt += f"  {i}. {s}\n"
        txt += "\n"
    await update.message.reply_text(txt, parse_mode="HTML")

async def unknown(update, ctx):
    if not allowed(update): await blocked(update)

# ==================== MAIN ====================
async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("tolov", tolov_start)],
        states={
            TOLOV_MENU:     [CallbackQueryHandler(tolov_menu)],
            SELECT_GROUP:   [CallbackQueryHandler(select_group)],
            SELECT_STUDENT: [
                CallbackQueryHandler(confirm_send,  pattern="^confirm$"),
                CallbackQueryHandler(select_student),
            ],
        },
        fallbacks=[], per_user=True, per_chat=True,
    )
    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("jadval",     cmd_jadval))
    app.add_handler(CommandHandler("status",     cmd_status))
    app.add_handler(CommandHandler("oquvchilar", cmd_oquvchilar))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.ALL, unknown))
    app.job_queue.run_repeating(check_lessons, interval=60, first=5)
    print("✅ EduStar bot ishga tushdi!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=["message","callback_query"])
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())