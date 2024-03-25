# Импортируем необходимые классы.
import asyncio
import requests
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

BOT_TOKEN = '7026188438:AAGflEWSktuzwbFSuuuS0TF5_eprpEK_-F8'

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

# Создаем соединение с базой данных
engine = create_engine('sqlite:///users.db', echo=True)

# Создаем базовый класс моделей и сессию для работы с базой данных
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


# Определяем модель пользователя
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    user_name = Column(String)
    gender = Column(String)
    country = Column(String)
    photo = Column(String)


# Создаем таблицу, если она еще не существует
Base.metadata.create_all(engine)

input_name = False
actual_user = ''


def get_universities(country):
    url = f"http://universities.hipolabs.com/search?country={country}"
    response = requests.get(url)
    name_of_universities = response.json()
    return name_of_universities


async def country_universities(country):
    universities_names = get_universities(country)
    list_universities = []
    if universities_names:
        for university in universities_names:
            list_universities.append(university['name'])
        return '\n'.join(list_universities[:25])
    else:
        return "Нет доступных университетов для указанной страны"


async def outputs(update, context):
    global input_name

    if input_name is True:
        try:
            task = asyncio.ensure_future(get_info(update.message.text))
            while not task.done():
                await update.message.reply_text("Создание профиля...")
                await asyncio.sleep(2)
            result = await task

            await update.message.reply_text(result[0])
            # Отправка фото профиля
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=result[1])

        except:
            await update.message.reply_text('Ошибка, похоже... Такого имени на данный момент не существует '
                                            'или оно уже занято!')
            input_name = False

    elif '/searchcountry' in update.message.text:
        task = asyncio.ensure_future(country_universities(update.message.text.replace('/searchcountry ', '')))
        while not task.done():
            await update.message.reply_text("Получение списка университетов...")
            await asyncio.sleep(1)
        result = await task
        await update.message.reply_text(result)

    elif '/searchname' in update.message.text:
        task = asyncio.ensure_future(get_university_info(update.message.text.replace('/searchname ', '')))
        while not task.done():
            await update.message.reply_text("Получение информации...")
            await asyncio.sleep(1)
        result = await task
        await update.message.reply_text(result)


async def get_university_info(university_name):
    # Формируем URL запроса
    url = f"http://universities.hipolabs.com/search?name={university_name}"

    # Отправляем GET запрос
    response = requests.get(url)
    data = response.json()
    if len(data) > 0:
        # Выводим информацию о первом найденном университете
        a = data[0]["name"]
        b = data[0]["country"]
        c = data[0]["web_pages"][0]
        list_inf = [a, b, c]
        return '\n'.join(list_inf)
    else:
        return "Университет не найден."


async def get_info(name):
    global input_name, actual_user

    try:
        existing_user = session.query(User).filter(User.name == name).first()
    except:
        return None

    if existing_user:
        return None

    else:
        name_use = translit_russian_to_english(name)

        url_age = f"https://api.agify.io/?name={name_use}"
        response_age = requests.get(url_age)
        data_age = response_age.json()
        age = int(data_age.get('age')) // 2

        url_gender = f"https://api.genderize.io/?name={name_use}"
        response_gender = requests.get(url_gender)
        data_gender = response_gender.json()
        gender = data_gender.get("gender")

        url_photo = f"https://dog.ceo/api/breeds/image/random"
        response_photo = requests.get(url_photo)
        data_photo = response_photo.json()
        image_url = data_photo["message"]

        url_country = f"https://api.nationalize.io/?name={name_use}"
        response_country = requests.get(url_country)
        data_country = response_country.json()
        country = []

        for result in data_country['country']:
            country_name = result['country_id']
            probability = result['probability'] * 100
            country.append(f"{country_name}: {probability}%")

        country = '\n'.join(country)

        # Создаем нового пользователя и сохраняем его в базу данных
        new_user = User(user_name=actual_user, name=name, age=age, gender=gender, photo=image_url, country=country)
        session.add(new_user)
        session.commit()

        answer = [
            f'Имя: {name}\nВозраст: {age}\nПол: {gender}\n\nПредполагаю, что вы:\n{country}\n\nАватар:', image_url
        ]

    input_name = False

    return answer


async def start(update, context):
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Профиль", callback_data='profile'),
          InlineKeyboardButton("Помощь", callback_data='get_help')]]
    )

    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я Вениамин. Если у вас еще нет профиля, создайте!.",
        reply_markup=markup
    )


async def profile(update, context):
    global input_name
    input_name = True
    await update.message.reply_html(
        rf"Введите, пожалуйста, ваше имя. У нас очень простая система регистрации :)",
    )


async def get_help(update, context):
    await update.message.reply_text(
        '/searchcountry <страна> - Поиск университетов по стране'
        '\n/searchname <название института> - Поиск информации о университете'

    )


def delete_user(existing_user):
    session.query(User).filter(User.user_name == existing_user).delete()
    session.commit()


async def button_click(update, context):
    global actual_user
    query = update.callback_query
    command = query.data

    if command == 'profile':
        actual_user = query.from_user.username
        try:
            existing_user = session.query(User).filter(User.user_name == actual_user).first()
        except:
            return None

        if existing_user:

            markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Удалить профиль", callback_data='delete_user')]]
            )

            await query.answer()

            user = session.query(User).filter(User.user_name == actual_user).first()
            answer = [
                f'\n\nИмя: {user.name}\nВозраст: {user.age}\nПол: {user.gender}\n\nПредполагаю, что вы:\n{user.country}'
                , user.photo
            ]

            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=answer[1])
            await query.message.reply_text(
                rf"У вас уже имеется профиль!{answer[0]}!",
                reply_markup=markup
            )

        else:
            await query.answer()
            await profile(query, context)

    elif command == 'get_help':
        await query.answer()
        await get_help(query, context)

    elif command == 'delete_user':
        await query.answer()
        actual_user = query.from_user.username
        delete_user(actual_user)
        await query.message.reply_text(
            'Ваш профиль успешно удален!'
        )


def translit_russian_to_english(text):
    translit_dict = {
        'а': 'a', 'б': 'b', 'в': 'v',
        'г': 'g', 'д': 'd', 'е': 'e',
        'ё': 'yo', 'ж': 'zh', 'з': 'z',
        'и': 'i', 'й': 'y', 'к': 'k',
        'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': "'", 'ы': 'y', 'ь': "'", 'э': 'e',
        'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V',
        'Г': 'G', 'Д': 'D', 'Е': 'E',
        'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z',
        'И': 'I', 'Й': 'Y', 'К': 'K',
        'Л': 'L', 'М': 'M', 'Н': 'N',
        'О': 'O', 'П': 'P', 'Р': 'R',
        'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts',
        'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': "'", 'Ы': 'Y', 'Ь': "'", 'Э': 'E',
        'Ю': 'Yu', 'Я': 'Ya',
    }
    result = ""
    for char in text:
        if char in translit_dict:
            result += translit_dict[char]
        else:
            result += char
    return result


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    text_handler = MessageHandler(filters.TEXT, outputs)
    application.add_handler(CommandHandler("start", start))

    application.add_handler(text_handler)
    application.add_handler(CallbackQueryHandler(button_click))

    # Запускаем приложение.
    application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
