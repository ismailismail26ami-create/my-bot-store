import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات ---
TOKEN = '8949634245:AAHDezYpc8vNp2jdDPVQ00a2_a4Ua5FLanM'
ADMIN_ID = 7339897843
CHANNEL_ID = '@RAMD02I'
CONTACT_LINK = 'https://t.me/RMAD3'

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- الحالات ---
class AddAccount(StatesGroup):
    type = State()
    desc = State()
    price = State()
    rating = State()

# --- قاعدة البيانات ---
async def init_db():
    async with aiosqlite.connect('store.db') as db:
        await db.execute('CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY, type TEXT, desc TEXT, price TEXT)')
        await db.commit()

# --- فحص الاشتراك ---
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- الأزرار ---
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 فري فاير", callback_data="page_ff_0"),
         InlineKeyboardButton(text="📘 فيسبوك", callback_data="page_fb_0")],
        [InlineKeyboardButton(text="🎵 تيك توك", callback_data="page_tt_0")],
        [InlineKeyboardButton(text="⭐ تقييم البوت", callback_data="rate_bot"),
         InlineKeyboardButton(text="📞 تواصل معي", url=CONTACT_LINK)]
    ])

def get_nav_markup(acc_type, index, total):
    buttons = []
    nav_row = []
    if index > 0: nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{acc_type}_{index-1}"))
    if index < total - 1: nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{acc_type}_{index+1}"))
    if nav_row: buttons.append(nav_row)
    buttons.append([InlineKeyboardButton(text="💰 شراء الحساب", url=CONTACT_LINK)])
    buttons.append([InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- الأوامر ---
@dp.message(Command("start"))
async def start(msg: types.Message):
    if not await is_subscribed(msg.from_user.id):
        await msg.answer(f"⚠️ يرجى الاشتراك في القناة أولاً لتفعيل البوت:\n{CHANNEL_ID}")
        return
    await msg.answer("مرحباً بك في متجرنا الرقمي! اختر قسماً:", reply_markup=main_menu())

@dp.callback_query(F.data == "main")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text("مرحباً بك في المتجر! اختر قسماً:", reply_markup=main_menu())

# --- التقييم ---
@dp.callback_query(F.data == "rate_bot")
async def rate_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("نقدر رأيك! أرسل تقييمك في رسالة:")
    await state.set_state(AddAccount.rating)

@dp.message(AddAccount.rating)
async def get_rating(msg: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"⭐ تقييم جديد من {msg.from_user.full_name}:\n{msg.text}")
    await msg.answer("✅ شكراً لك على تقييمك!")
    await state.clear()

# --- عرض الحسابات ---
@dp.callback_query(F.data.startswith("page_"))
async def show_accounts(call: types.CallbackQuery):
    _, acc_type, index = call.data.split("_")
    index = int(index)
    async with aiosqlite.connect('store.db') as db:
        cursor = await db.execute("SELECT * FROM accounts WHERE type=?", (acc_type,))
        accs = await cursor.fetchall()
    if not accs:
        await call.answer("لا توجد حسابات في هذا القسم!")
        return
    acc = accs[index]
    await call.message.edit_text(f"📦 ({index+1}/{len(accs)})\n📝 {acc[2]}\n💵 السعر: {acc[3]}", 
                                 reply_markup=get_nav_markup(acc_type, index, len(accs)))

# --- إضافة حساب (للأدمن فقط) ---
@dp.message(Command("add"))
async def admin_add(msg: types.Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID: return
    await msg.answer("أرسل نوع الحساب (ff, fb, tt):")
    await state.set_state(AddAccount.type)

@dp.message(AddAccount.type)
async def get_type(msg: types.Message, state: FSMContext):
    await state.update_data(type=msg.text); await msg.answer("أرسل الوصف:"); await state.set_state(AddAccount.desc)

@dp.message(AddAccount.desc)
async def get_desc(msg: types.Message, state: FSMContext):
    await state.update_data(desc=msg.text); await msg.answer("أرسل السعر:"); await state.set_state(AddAccount.price)

@dp.message(AddAccount.price)
async def save_acc(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    async with aiosqlite.connect('store.db') as db:
        await db.execute("INSERT INTO accounts (type, desc, price) VALUES (?,?,?)", (data['type'], data['desc'], msg.text))
        await db.commit()
    await msg.answer("✅ تم إضافة الحساب!"); await state.clear()

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
