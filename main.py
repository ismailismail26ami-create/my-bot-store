import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- الإعدادات ---
TOKEN = '8949634245:AAHDezYpc8vNp2jdDPVQ00a2_a4Ua5FLanM'
ADMIN_ID = 7339897843
MY_ID = 1058388452
CONTACT_LINK = 'https://t.me/RMAD3'

# --- خادم الويب (للإبقاء على البوت مستيقظاً) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
def run_web(): app.run(host='0.0.0.0', port=8080)

bot = Bot(token=TOKEN)
dp = Dispatcher()

class AdminStates(StatesGroup):
    add_type, add_desc, add_price, add_media, delete_id = State(), State(), State(), State(), State()

async def init_db():
    async with aiosqlite.connect('store.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS accounts 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, desc TEXT, price TEXT, 
             media_id TEXT, media_type TEXT, is_sold INTEGER DEFAULT 0)''')
        await db.commit()

def main_menu(user_id):
    buttons = [[InlineKeyboardButton(text="🎮 فري فاير", callback_data="page_ff_0"), InlineKeyboardButton(text="📘 فيسبوك", callback_data="page_fb_0")],
               [InlineKeyboardButton(text="🎵 تيك توك", callback_data="page_tt_0")],
               [InlineKeyboardButton(text="📦 المبيعات السابقة", callback_data="sold_accs")],
               [InlineKeyboardButton(text="📞 تواصل معي", url=CONTACT_LINK)]]
    if user_id == ADMIN_ID: buttons.append([InlineKeyboardButton(text="🛠 لوحة التحكم", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("مرحباً بك في متجرنا! اختر قسماً:", reply_markup=main_menu(msg.from_user.id))

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة", callback_data="add_acc"), InlineKeyboardButton(text="❌ حذف", callback_data="del_acc")],
        [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu")]
    ])
    await call.message.edit_text("🛠 لوحة التحكم:", reply_markup=kb)

# --- نظام البيع والأرشيف ---
@dp.callback_query(F.data.startswith("buy_"))
async def buy_account(call: types.CallbackQuery):
    acc_id = call.data.split("_")[1]
    await bot.send_message(MY_ID, f"🔔 طلب شراء جديد!\nرقم الحساب: {acc_id}\nالمستخدم: @{call.from_user.username}")
    await call.answer("تم إرسال الطلب للأدمن!", show_alert=True)

@dp.message(Command("sold"))
async def mark_as_sold(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    try:
        acc_id = msg.text.split()[1]
        async with aiosqlite.connect('store.db') as db:
            await db.execute("UPDATE accounts SET is_sold=1 WHERE id=?", (acc_id,))
            await db.commit()
        await msg.answer("✅ تم البيع ونقل الحساب للأرشيف!")
    except: await msg.answer("استخدم: /sold رقم_الحساب")

@dp.callback_query(F.data == "add_acc")
async def start_add(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("أرسل النوع (ff, fb, tt):")
    await state.set_state(AdminStates.add_type)

# [هنا تكمل دوال الإضافة كما في الكود السابق...]

@dp.callback_query(F.data.startswith("page_"))
async def show_accounts(call: types.CallbackQuery):
    _, acc_type, index = call.data.split("_")
    async with aiosqlite.connect('store.db') as db:
        cursor = await db.execute("SELECT * FROM accounts WHERE type=? AND is_sold=0", (acc_type,))
        accs = await cursor.fetchall()
    if not accs: await call.answer("لا توجد حسابات متاحة!"); return
    acc = accs[int(index)]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💰 شراء", callback_data=f"buy_{acc[0]}")]])
    caption = f"🆔 ID: {acc[0]}\n📝 {acc[2]}\n💵 السعر: {acc[3]}"
    if acc[5] == 'photo': await bot.send_photo(call.message.chat.id, photo=acc[4], caption=caption, reply_markup=kb)
    else: await bot.send_video(call.message.chat.id, video=acc[4], caption=caption, reply_markup=kb)

async def main():
    Thread(target=run_web).start() # تشغيل خادم الويب
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())
