import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات ---
TOKEN = '8949634245:AAG_pelvpPsgLJwDtp_5hvYSRXXIc8nPL98'
ADMIN_ID = 7339897843
MY_ID = 1058388452
CONTACT_LINK = 'https://t.me/RMAD3'

bot = Bot(token=TOKEN)
dp = Dispatcher()

class AdminStates(StatesGroup):
    add_type = State()
    add_desc = State()
    add_price = State()
    add_media = State()
    add_media_type = State()

async def init_db():
    async with aiosqlite.connect('store.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS accounts 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, desc TEXT, price TEXT, 
             media_id TEXT, media_type TEXT, is_sold INTEGER DEFAULT 0)''')
        await db.commit()

def main_menu(user_id):
    buttons = [
        [InlineKeyboardButton(text="🎮 فري فاير", callback_data="page_ff_0"), InlineKeyboardButton(text="📘 فيسبوك", callback_data="page_fb_0")],
        [InlineKeyboardButton(text="🎵 تيك توك", callback_data="page_tt_0")],
        [InlineKeyboardButton(text="📦 المبيعات السابقة", callback_data="sold_accs")],
        [InlineKeyboardButton(text="📞 تواصل معي", url=CONTACT_LINK)]
    ]
    if user_id == ADMIN_ID: 
        buttons.append([InlineKeyboardButton(text="🛠 لوحة التحكم", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("مرحباً بك في متجرنا! اختر قسماً:", reply_markup=main_menu(msg.from_user.id))

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة", callback_data="add_acc")],
        [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="back_main")]
    ])
    await call.message.edit_text("🛠 لوحة التحكم:", reply_markup=kb)

@dp.callback_query(F.data == "back_main")
async def back_main(call: types.CallbackQuery):
    await call.message.edit_text("القائمة الرئيسية:", reply_markup=main_menu(call.from_user.id))

@dp.callback_query(F.data.startswith("page_"))
async def show_accounts(call: types.CallbackQuery):
    _, acc_type, index = call.data.split("_")
    async with aiosqlite.connect('store.db') as db:
        cursor = await db.execute("SELECT * FROM accounts WHERE type=? AND is_sold=0", (acc_type,))
        accs = await cursor.fetchall()
    
    if not accs: 
        await call.answer("لا توجد حسابات متاحة حالياً!"); return
    
    acc = accs[int(index)]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💰 شراء", callback_data=f"buy_{acc[0]}")]])
    caption = f"🆔 ID: {acc[0]}\n📝 الوصف: {acc[2]}\n💵 السعر: {acc[3]}"
    
    if acc[5] == 'photo': 
        await bot.send_photo(call.message.chat.id, photo=acc[4], caption=caption, reply_markup=kb)
    else: 
        await bot.send_video(call.message.chat.id, video=acc[4], caption=caption, reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def buy_account(call: types.CallbackQuery):
    acc_id = call.data.split("_")[1]
    await bot.send_message(MY_ID, f"🔔 طلب شراء جديد!\nرقم الحساب: {acc_id}\nالمستخدم: @{call.from_user.username}")
    await call.answer("تم إرسال الطلب للأدمن!", show_alert=True)

async def main():
    await init_db()
    # تنظيف أي تحديثات معلقة قديمة عند التشغيل
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__": 
    asyncio.run(main())
