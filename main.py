import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '8949634245:AAHDezYpc8vNp2jdDPVQ00a2_a4Ua5FLanM'
ADMIN_ID = 7339897843
CONTACT_LINK = 'https://t.me/RMAD3'

bot = Bot(token=TOKEN)
dp = Dispatcher()

class AdminStates(StatesGroup):
    add_type = State()
    add_desc = State()
    add_price = State()
    add_media = State() # سميناها media لتقبل صور أو فيديوهات

async def init_db():
    async with aiosqlite.connect('store.db') as db:
        await db.execute('CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, desc TEXT, price TEXT, media_id TEXT, media_type TEXT)')
        await db.commit()

def main_menu(user_id):
    buttons = [
        [InlineKeyboardButton(text="🎮 فري فاير", callback_data="page_ff_0"),
         InlineKeyboardButton(text="📘 فيسبوك", callback_data="page_fb_0")],
        [InlineKeyboardButton(text="🎵 تيك توك", callback_data="page_tt_0")],
        [InlineKeyboardButton(text="📞 تواصل معي", url=CONTACT_LINK)]
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="🛠 لوحة تحكم الأدمن", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("مرحباً بك في متجرنا! اختر قسماً:", reply_markup=main_menu(msg.from_user.id))

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ إضافة حساب", callback_data="add_acc")],
        [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu")]
    ])
    await call.message.edit_text("🛠 لوحة تحكم الأدمن:", reply_markup=kb)

@dp.callback_query(F.data == "add_acc")
async def start_add(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("أرسل نوع الحساب (ff, fb, tt):")
    await state.set_state(AdminStates.add_type)

@dp.message(AdminStates.add_type)
async def get_type(msg: types.Message, state: FSMContext):
    await state.update_data(type=msg.text); await msg.answer("أرسل الوصف:"); await state.set_state(AdminStates.add_desc)

@dp.message(AdminStates.add_desc)
async def get_desc(msg: types.Message, state: FSMContext):
    await state.update_data(desc=msg.text); await msg.answer("أرسل السعر:"); await state.set_state(AdminStates.add_price)

@dp.message(AdminStates.add_price)
async def get_price(msg: types.Message, state: FSMContext):
    await state.update_data(price=msg.text); await msg.answer("أرسل صورة أو فيديو للحساب:"); await state.set_state(AdminStates.add_media)

@dp.message(AdminStates.add_media, F.photo | F.video)
async def save_acc(msg: types.Message, state: FSMContext):
    media_id = msg.photo[-1].file_id if msg.photo else msg.video.file_id
    media_type = 'photo' if msg.photo else 'video'
    data = await state.get_data()
    async with aiosqlite.connect('store.db') as db:
        await db.execute("INSERT INTO accounts (type, desc, price, media_id, media_type) VALUES (?,?,?,?,?)", 
                         (data['type'], data['desc'], data['price'], media_id, media_type))
        await db.commit()
    await msg.answer("✅ تم الإضافة بنجاح!"); await state.clear()

@dp.callback_query(F.data.startswith("page_"))
async def show_accounts(call: types.CallbackQuery):
    _, acc_type, index = call.data.split("_")
    index = int(index)
    async with aiosqlite.connect('store.db') as db:
        cursor = await db.execute("SELECT * FROM accounts WHERE type=?", (acc_type,))
        accs = await cursor.fetchall()
    if not accs: await call.answer("لا توجد حسابات!"); return
    acc = accs[index]
    caption = f"📝 {acc[2]}\n💵 السعر: {acc[3]}"
    if acc[5] == 'photo': await bot.send_photo(call.message.chat.id, photo=acc[4], caption=caption)
    else: await bot.send_video(call.message.chat.id, video=acc[4], caption=caption)

@dp.callback_query(F.data == "main_menu")
async def back_to_main(call: types.CallbackQuery):
    await call.message.edit_text("مرحباً بك في متجرنا! اختر قسماً:", reply_markup=main_menu(call.from_user.id))

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
