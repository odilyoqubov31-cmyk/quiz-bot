import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from database import init_db, add_user, get_user, add_points, get_top_users

BOT_TOKEN = "8624524867:AAHIbYmTgvaFNrwM74UC7BU7IA-Tetw5YS4"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

waiting_queue = []
active_duels = {}

QUESTIONS = [
    {"category": "Tarix", "question": "Amir Temur qaysi yilda tavallud topgan?", "options": ["1336-yil", "1360-yil", "1299-yil", "1405-yil"], "correct": 0},
    {"category": "Texnologiya", "question": "Python dasturlash tili qaysi yilda taqdim etilgan?", "options": ["1991-yil", "1985-yil", "2000-yil", "1978-yil"], "correct": 0},
    {"category": "Geografiya", "question": "Yer yuzidagi eng chuqur botiq qaysi?", "options": ["Mariana botig'i", "Baykal ko'li", "Katta kanyon", "Everest cho'qqisi"], "correct": 0},
    {"category": "Mantiq", "question": "Shaxmat taxtasida jami nechta katak bor?", "options": ["32", "64", "48", "100"], "correct": 1}
]

def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Bot bilan o'ynash (Mashq)", callback_data="single_game")],
        [InlineKeyboardButton(text="🎲 Random raqib bilan duel", callback_data="random_duel")],
        [InlineKeyboardButton(text="👥 Do'st taklif qilish (⭐ Yulduzchalar)", callback_data="ref_link")],
        [InlineKeyboardButton(text="🏆 Peshqadamlar", callback_data="leaderboard"), InlineKeyboardButton(text="👤 Profil", callback_data="my_profile")]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    name = message.from_user.full_name

    referrer_id = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_candidate = int(args[1].replace("ref_", ""))
        if ref_candidate != user_id:
            referrer_id = ref_candidate

    is_new = add_user(user_id, name, referrer_id)

    if is_new and referrer_id:
        add_points(referrer_id, score_add=20, stars_add=5)
        try:
            await bot.send_message(referrer_id, "🎉 Siz taklif qilgan do'stingiz botga qo'shildi! Sizga **+5 yulduzcha** va **+20 ball** berildi! ⭐")
        except:
            pass

    await message.answer(f"Salom, **{name}**! 🧠\n\nSmartQuiz Duel botiga xush kelibsiz!", reply_markup=main_menu_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "single_game")
async def start_single_game(callback: CallbackQuery):
    q_index = random.randint(0, len(QUESTIONS) - 1)
    q = QUESTIONS[q_index]

    buttons = [[InlineKeyboardButton(text=opt, callback_data=f"s_ans_{q_index}_{idx}")] for idx, opt in enumerate(q["options"])]
    buttons.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")])

    await callback.message.edit_text(f"📂 Kategoriya: *{q['category']}*\n\n❓ **Savol:**\n{q['question']}", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("s_ans_"))
async def process_single_answer(callback: CallbackQuery):
    _, _, q_idx, opt_idx = callback.data.split("_")
    q_idx, opt_idx = int(q_idx), int(opt_idx)
    user_id = callback.from_user.id

    correct_opt = QUESTIONS[q_idx]["correct"]
    if opt_idx == correct_opt:
        add_points(user_id, score_add=10)
        text = "✅ **To'g'ri javob!** (+10 ball)"
    else:
        text = f"❌ **Noto'g'ri!** To'g'ri javob: **{QUESTIONS[q_idx]['options'][correct_opt]}**"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Keyingi savol", callback_data="single_game")],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "random_duel")
async def find_random_opponent(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in waiting_queue:
        await callback.answer("Raqib qidirilmoqda...", show_alert=True)
        return

    if waiting_queue:
        opponent_id = waiting_queue.pop(0)
        if opponent_id == user_id:
            waiting_queue.append(user_id)
            return

        duel_id = f"duel_{user_id}_{opponent_id}"
        q_idx = random.randint(0, len(QUESTIONS) - 1)
        active_duels[duel_id] = {"p1": opponent_id, "p2": user_id, "q_idx": q_idx, "p1_score": 0, "p2_score": 0}

        q = QUESTIONS[q_idx]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"duelin_{duel_id}_{idx}")] for idx, opt in enumerate(q["options"])
        ])

        await bot.send_message(opponent_id, f"⚔️ Raqib topildi! Duel boshlandi!\n\n❓ {q['question']}", reply_markup=kb)
        await callback.message.edit_text(f"⚔️ Raqib topildi! Duel boshlandi!\n\n❓ {q['question']}", reply_markup=kb)
    else:
        waiting_queue.append(user_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_queue")]])
        await callback.message.edit_text("⏳ Onlayn raqib qidirilmoqda... Kuting.", reply_markup=kb)

@dp.callback_query(F.data == "cancel_queue")
async def cancel_queue(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in waiting_queue:
        waiting_queue.remove(user_id)
    await callback.message.edit_text("Qidiruv to'xtatildi.", reply_markup=main_menu_keyboard())

@dp.callback_query(F.data.startswith("duelin_"))
async def process_duel_answer(callback: CallbackQuery):
    _, duel_id, opt_idx = callback.data.split("_")
    opt_idx = int(opt_idx)
    user_id = callback.from_user.id

    if duel_id not in active_duels:
        await callback.message.edit_text("Bu duel tugagan.", reply_markup=main_menu_keyboard())
        return

    duel = active_duels[duel_id]
    q = QUESTIONS[duel["q_idx"]]

    if opt_idx == q["correct"]:
        if user_id == duel["p1"]: duel["p1_score"] += 10
        else: duel["p2_score"] += 10

    p1_data = get_user(duel["p1"])
    p2_data = get_user(duel["p2"])
    p1_name = p1_data[1] if p1_data else "1-o'yinchi"
    p2_name = p2_data[1] if p2_data else "2-o'yinchi"

    res = f"⚔️ **Duel natijasi:**\n\n{p1_name}: {duel['p1_score']} ball\n{p2_name}: {duel['p2_score']} ball\n\n"
    if duel["p1_score"] > duel["p2_score"]: res += f"🏆 G'olib: **{p1_name}**!"
    elif duel["p2_score"] > duel["p1_score"]: res += f"🏆 G'olib: **{p2_name}**!"
    else: res += "🤝 **Durang!**"

    del active_duels[duel_id]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")]])
    
    try: await bot.send_message(duel["p1"], res, reply_markup=kb, parse_mode="Markdown")
    except: pass
    try: await bot.send_message(duel["p2"], res, reply_markup=kb, parse_mode="Markdown")
    except: pass

@dp.callback_query(F.data == "ref_link")
async def show_referral(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    u = get_user(user_id)
    stars = u[3] if u else 0

    text = f"👥 **Do'stlarni taklif qilish**\n\nSizning yulduzchalaringiz: ⭐ **{stars} ta**\n\nHar bir do'stingiz uchun: **+5 yulduzcha** va **+20 ball**!\n\nSizning havolangiz:\n`{ref_link}`"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Do'stlarga ulashish", switch_inline_query=f"\nZakovat duelida o'ynaymizmi? Link: {ref_link}")],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "leaderboard")
async def leaderboard(callback: CallbackQuery):
    top_users = get_top_users(5)
    text = "🏆 **TOP-5 Peshqadamlar:**\n\n"
    for idx, u in enumerate(top_users, 1):
        text += f"{idx}. {u[0]} — {u[1]} ball (⭐ {u[2]})\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "my_profile")
async def profile(callback: CallbackQuery):
    u = get_user(callback.from_user.id)
    if u:
        text = f"👤 **Sizning profilingiz:**\n\nIsm: {u[1]}\nJami ballar: **{u[2]}**\nYulduzchalar: ⭐ **{u[3]}**\n"
    else:
        text = "Profil topilmadi."
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    await callback.message.edit_text("Asosiy menyu:", reply_markup=main_menu_keyboard())

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    print("Bot va Baza ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
