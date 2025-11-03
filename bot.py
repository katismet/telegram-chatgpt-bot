import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from config import BOT_TOKEN
import asyncio
from aiogram.filters import Command
import aiohttp
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Кнопки ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Поиск рецептов')],
        [KeyboardButton(text='Мои рецепты')]
    ],
    resize_keyboard=True
)

# --- Простая in-memory база избранных рецептов ---
favorites_db = {}

def get_recipe_inline(recipe_id):
    buttons = [
        [
            InlineKeyboardButton(text='Добавить в избранное', callback_data=f'favadd:{recipe_id}'),
            InlineKeyboardButton(text='Показать рецепт', callback_data=f'show:{recipe_id}')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_recipe_list_markup(recipes):
    buttons = []
    for recipe in recipes:
        buttons.append([
            InlineKeyboardButton(text=recipe['title'], callback_data=f'show:{recipe['id']}'),
            InlineKeyboardButton(text='❤️', callback_data=f'favadd:{recipe['id']}')
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- Рейтинг ---
def get_rating_markup(recipe_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⭐️', callback_data=f'rate:{recipe_id}:1'),
         InlineKeyboardButton(text='⭐️⭐️', callback_data=f'rate:{recipe_id}:2'),
         InlineKeyboardButton(text='⭐️⭐️⭐️', callback_data=f'rate:{recipe_id}:3'),
         InlineKeyboardButton(text='⭐️⭐️⭐️⭐️', callback_data=f'rate:{recipe_id}:4'),
         InlineKeyboardButton(text='⭐️⭐️⭐️⭐️⭐️', callback_data=f'rate:{recipe_id}:5')]
    ])

# --- Состояния ---
class SearchStates(StatesGroup):
    waiting_for_query = State()

# --- Хэндлеры ---
@dp.message(Command('start'))
async def send_welcome(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Я помогу найти рецепты и сохранить их в избранное. Выберите действие:",
        reply_markup=main_menu
    )

@dp.message(lambda message: message.text == 'Поиск рецептов')
async def search_recipes(message: types.Message, state: FSMContext):
    await message.answer("Введите название блюда или ингредиент для поиска рецепта:")
    await state.set_state(SearchStates.waiting_for_query)

@dp.message(SearchStates.waiting_for_query)
async def handle_search_query(message: types.Message, state: FSMContext):
    query = message.text.strip()
    await message.answer('Ищу рецепты...')
    recipes = await search_mealdb(query)
    if not recipes:
        await message.answer('Ничего не найдено. Попробуйте другой запрос.')
    else:
        markup = get_recipe_list_markup(recipes)
        await message.answer('Найденные рецепты:', reply_markup=markup)
    await state.clear()

@dp.message(lambda message: message.text == 'Мои рецепты')
async def my_recipes(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    favs = favorites_db.get(user_id, [])
    if not favs:
        await message.answer('У вас нет избранных рецептов.')
    else:
        markup = get_favorites_list_markup(favs)
        await message.answer('Ваши избранные рецепты:', reply_markup=markup)

# --- Пример структуры для отображения рецепта ---
async def show_recipe(chat_id, recipe, show_full=False):
    text = f"<b>{recipe['title']}</b>"
    if show_full:
        text += f"\n{recipe.get('desc', '')}"
    markup = get_recipe_inline(recipe['id'])
    await bot.send_photo(chat_id, recipe.get('img', ''), caption=text, parse_mode='HTML', reply_markup=markup)

# --- Обработка нажатия на кнопку 'В избранное' ---
@dp.callback_query(lambda c: c.data and c.data.startswith('favorite:'))
async def process_favorite(callback_query: types.CallbackQuery):
    recipe_id = callback_query.data.split(':')[1]
    # Здесь будет логика добавления/удаления из избранного
    await callback_query.answer('Рецепт добавлен в избранное (заглушка)')

# --- Изменить добавление в избранное: рейтинг по умолчанию 0 ---
@dp.callback_query(lambda c: c.data and c.data.startswith('favadd:'))
async def add_to_favorites(callback_query: types.CallbackQuery):
    recipe_id = callback_query.data.split(':')[1]
    user_id = callback_query.from_user.id
    url = f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={recipe_id}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            meal = data['meals'][0] if data['meals'] else None
            if not meal:
                await callback_query.answer('Рецепт не найден!')
                return
            title = meal['strMeal']
            img = meal.get('strMealThumb', '')
            if user_id not in favorites_db:
                favorites_db[user_id] = []
            if not any(r['id'] == recipe_id for r in favorites_db[user_id]):
                favorites_db[user_id].append({'id': recipe_id, 'title': title, 'img': img, 'rating': 0})
                await callback_query.answer('Добавлено в избранное!')
            else:
                await callback_query.answer('Уже в избранном!')

# --- После показа рецепта предлагать поставить рейтинг ---
@dp.callback_query(lambda c: c.data and c.data.startswith('show:'))
async def show_full_recipe(callback_query: types.CallbackQuery):
    recipe_id = callback_query.data.split(':')[1]
    url = f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={recipe_id}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            meal = data['meals'][0] if data['meals'] else None
            if meal:
                desc = meal.get('strInstructions', '')
                img = meal.get('strMealThumb', '')
                text = f"<b>{meal['strMeal']}</b>\n{desc}"
                if len(text) > 1000:
                    text = text[:997] + '...'
                markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Добавить в избранное', callback_data=f'favadd:{recipe_id}')]])
                await callback_query.message.answer_photo(img, caption=text, parse_mode='HTML', reply_markup=markup)
                # Предложить поставить рейтинг
                await callback_query.message.answer('Поставьте рейтинг этому рецепту:', reply_markup=get_rating_markup(recipe_id))
            else:
                await callback_query.answer('Рецепт не найден!')
    await callback_query.answer()

# --- Обработка выставления рейтинга ---
@dp.callback_query(lambda c: c.data and c.data.startswith('rate:'))
async def rate_recipe(callback_query: types.CallbackQuery):
    _, recipe_id, rating = callback_query.data.split(':')
    user_id = callback_query.from_user.id
    rating = int(rating)
    favs = favorites_db.get(user_id, [])
    for recipe in favs:
        if recipe['id'] == recipe_id:
            recipe['rating'] = rating
            await callback_query.answer(f'Вы поставили {rating} ⭐️')
            break
    else:
        await callback_query.answer('Сначала добавьте рецепт в избранное!')

# --- Сортировка избранных по рейтингу ---
def get_favorites_list_markup(favs):
    # Сортируем по убыванию рейтинга, потом по названию
    favs_sorted = sorted(favs, key=lambda r: (-r.get('rating', 0), r['title']))
    buttons = [
        [InlineKeyboardButton(text=f"{recipe['title']} {'⭐️'*recipe.get('rating', 0)}", callback_data=f'showfav:{recipe['id']}')] for recipe in favs_sorted
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- В showfav также предлагать поставить рейтинг ---
@dp.callback_query(lambda c: c.data and c.data.startswith('showfav:'))
async def show_favorite_recipe(callback_query: types.CallbackQuery):
    recipe_id = callback_query.data.split(':')[1]
    url = f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={recipe_id}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            meal = data['meals'][0] if data['meals'] else None
            if meal:
                desc = meal.get('strInstructions', '')
                img = meal.get('strMealThumb', '')
                text = f"<b>{meal['strMeal']}</b>\n{desc}"
                if len(text) > 1000:
                    text = text[:997] + '...'
                await callback_query.message.answer_photo(img, caption=text, parse_mode='HTML')
                await callback_query.message.answer('Поставьте рейтинг этому рецепту:', reply_markup=get_rating_markup(recipe_id))
            else:
                await callback_query.answer('Рецепт не найден!')
    await callback_query.answer()

async def search_mealdb(query):
    url = f'https://www.themealdb.com/api/json/v1/1/search.php?s={query}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            meals = data.get('meals')
            if not meals:
                return []
            recipes = []
            for meal in meals:
                recipes.append({
                    'id': meal['idMeal'],
                    'title': meal['strMeal'],
                    'desc': meal.get('strInstructions', '')[:300] + '...',
                    'img': meal.get('strMealThumb', '')
                })
            return recipes

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
