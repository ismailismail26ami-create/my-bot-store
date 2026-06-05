import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '8949634245:AAG_pelvpPsgLJwDtp_5hvYSRXXIc8nPL98'
ADMIN_ID = 7339897843
MY_ID = 00799999004388360037# معرفك للدفع
CONTACT_LINK = 'https://t.me/RMAD3'

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

# --- نظام البيع ---
@dp.callback_query(F.data.startswith("buy_"))
async def buy_account(call: types.CallbackQuery):
    acc_id = call.data.split("_")[1]
    await bot.send_message(MY_ID, f"🔔 طلب شراء جديد! \nرقم الحساب: {acc_id} \nمن المستخدم: @{call.from_user.username}")
    await call.answer("تم إرسال طلب الشراء للأدمن، سيتواصل معك قريباً!", show_alert=True)

# --- تغيير حالة الحساب لـ "مباع" ---
@dp.message(Command("sold")) # استخدم هذا الأمر لحذف الحساب من العرض (بيعه)
async def mark_as_sold(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    try:
        acc_id = msg.text.split()[1]
        async with aiosqlite.connect('store.db') as db:
            await db.execute("UPDATE accounts SET is_sold=1 WHERE id=?", (acc_id,))
            await db.commit()
        await msg.answer("✅ تم تحديد الحساب كمباع!")
    except: await msg.answer("استخدم الأمر هكذا: /sold رقم_الحساب")

# --- لوحة التحكم ---
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة", callback_data="add_acc"), InlineKeyboardButton(text="❌ حذف", callback_data="del_acc")],
        [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu")]
    ])
    await call.message.edit_text("🛠 لوحة التحكم:", reply_markup=kb)

# --- عرض الحسابات (مع زر الشراء) ---
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

# --- أرشيف المبيعات ---
@dp.callback_query(F.data == "sold_accs")
async def show_sold(call: types.CallbackQuery):
    async with aiosqlite.connect('store.db') as db:
        cursor = await db.execute("SELECT * FROM accounts WHERE is_sold=1")
        accs = await cursor.fetchall()
    if not accs: await call.answer("لا توجد مبيعات!"); return
    for acc in accs: await call.message.answer(f"✅ تم بيع حساب رقم: {acc[0]} \nالوصف: {acc[2]}")

# --- (دوال الإضافة والحذف كما في الكود السابق) ---
async def main():
    await init_db()
    await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
