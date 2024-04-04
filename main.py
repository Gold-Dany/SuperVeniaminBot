# Импортируем необходимые классы.
import random
import datetime
import difflib
import asyncio
import requests
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler, ConversationHandler
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
    future_university = Column(String)
    monday = Column(String)
    tuesday = Column(String)
    wednesday = Column(String)
    thursday = Column(String)
    friday = Column(String)
    saturday = Column(String)
    sunday = Column(String)


# Создаем таблицу, если она еще не существует
Base.metadata.create_all(engine)


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


def find_closest_country_name(name):
    countries = ["Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina",
                 "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
                 "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana",
                 "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon",
                 "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros",
                 "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia",
                 "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador",
                 "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini",
                 "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece",
                 "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras",
                 "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica",
                 "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia",
                 "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar",
                 "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius",
                 "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique",
                 "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua",
                 "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan",
                 "Palestine State", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland",
                 "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia",
                 "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia",
                 "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
                 "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka",
                 "State of Palestine", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania",
                 "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan",
                 "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America",
                 "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

    closest_match = difflib.get_close_matches(name, countries, n=1, cutoff=0.0)

    if closest_match:
        try:
            universities_names = get_universities(closest_match[0])
            list_universities = []
            if universities_names:
                for university in universities_names:
                    list_universities.append(university['name'])
            return random.choice(list_universities)
        except:
            return '-'
    else:
        universities_names = get_universities("Brazil")
        list_universities = []
        if universities_names:
            for university in universities_names:
                list_universities.append(university['name'])
        return random.choice(list_universities)


async def outputs(update, context):

    user = update.message.from_user
    username = user.username

    if 'waiting_for_name' in context.user_data and context.user_data['waiting_for_name']:
        try:
            del context.user_data['waiting_for_name']

            task = asyncio.ensure_future(get_info(update.message.text, username))
            while not task.done():
                await update.message.reply_text("Создание профиля...")
                await asyncio.sleep(1)
            result = await task

            await update.message.reply_text(result[0])

            # Отправка фото профиля
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=result[1])

        except Exception as e:
            await update.message.reply_text(f'Ошибка: {e}.\n\nПоянение: Проверьте существует ли ваше имя,'
                                            f' не занято ли оно или лимит запросов иссяк')

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


async def get_info(name, actual_user=''):
    try:
        existing_user = session.query(User).filter(User.name == name).first()
    except:
        return None

    if existing_user:
        return None

    else:
        try:
            # Переведенное на английский имя
            name_use = translit_russian_to_english(name)

            # Предсказание возраста
            url_age = f"https://api.agify.io/?name={name_use}"
            response_age = requests.get(url_age)
            data_age = response_age.json()
            age = int(data_age.get('age'))

            # Предсказание гендера
            url_gender = f"https://api.genderize.io/?name={name_use}"
            response_gender = requests.get(url_gender)
            data_gender = response_gender.json()
            gender = data_gender.get("gender")

            # Предсказание происхождения
            url_country = f"https://api.nationalize.io/?name={name_use}"
            response_country = requests.get(url_country)
            data_country = response_country.json()
            country = []

            for result in data_country['country']:
                country_name = result['country_id']
                probability = result['probability'] * 100
                country.append(f"{country_name}: {probability}%")

            country = '\n'.join(country)

            # Создание аватара
            url_photo = f"https://dog.ceo/api/breeds/image/random"
            response_photo = requests.get(url_photo)
            data_photo = response_photo.json()
            image_url = data_photo["message"]

            future_university = find_closest_country_name(name_use)

            # Создаем нового пользователя и сохраняем его в базу данных
            new_user = User(user_name=actual_user, name=name, age=age, gender=gender, photo=image_url, country=country,
                            future_university=future_university)

            session.add(new_user)
            session.commit()

            answer = [
                f'Имя: {name}\nВозраст: {age}\nПол: {gender}\n\nПредполагаю, что вы:\n{country}\n\n'
                f'Вам бы подошёл университет: {future_university}\n\n'
                f'Аватар:', image_url
            ]

            return answer

        except:

            try:
                url_photo = f"https://dog.ceo/api/breeds/image/random"
                response_photo = requests.get(url_photo)
                data_photo = response_photo.json()
                image_url = data_photo["message"]

                future_university = find_closest_country_name(name_use)

                # Создаем нового пользователя и сохраняем его в базу данных
                new_user = User(user_name=actual_user, name=name, photo=image_url, future_university=future_university)

                session.add(new_user)
                session.commit()

                answer = [
                    f'К сожалению, сейчас невозможно сделать для вашего имени полное предсказание\n\n'
                    f'Имя: {name}\n\nВам бы подошёл университет: {future_university}\n\nАватар:', image_url
                ]

                return answer

            except:
                return [f'Бот рухнул :(', '']


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
    context.user_data['waiting_for_name'] = True
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
    query = update.callback_query
    command = query.data
    actual_user = query.from_user.username

    if command == 'profile':
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
                f'\n\nИмя: {user.name}\nВозраст: {user.age}\nПол: {user.gender}\n\n'
                f'Вам бы подошёл университет: {user.future_university}\n\n'
                f'Предполагаю, что вы:\n{user.country}', user.photo
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


async def handle_photo(update, context):
    new_file = await update.message.effective_attachment[-1].get_file()
    file = await new_file.download_to_drive()

    await update.message.reply_html(
        rf"Я успешно получил данное фото:",
    )

    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=file)


async def get_plane(update, context):
    user = update.message.from_user
    username = user.username

    try:
        existing_user = session.query(User).filter(User.user_name == username).first()
    except:
        return None

    if existing_user:

        get_user = session.query(User).filter(User.user_name == username).first()

        Monday = '\n'.join(str(get_user.monday).strip().split(','))
        Tuesday = '\n'.join(str(get_user.tuesday).strip().split(','))
        Wednesday = '\n'.join(str(get_user.wednesday).strip().split(','))
        Thursday = '\n'.join(str(get_user.thursday).strip().split(','))
        Friday = '\n'.join(str(get_user.friday).strip().split(','))
        Saturday = '\n'.join(str(get_user.saturday).strip().split(','))
        Sunday = '\n'.join(str(get_user.sunday).strip().split(','))

        await update.message.reply_text(
            f"Понедельник:\n{Monday}\n\n"
            f"Вторник:\n{Tuesday}\n\n"
            f"Среда:\n{Wednesday}\n\n"
            f"Четверг:\n{Thursday}\n\n"
            f"Пятница:\n{Friday}\n\n"
            f"Суббота:\n{Saturday}\n\n"
            f"Воскресенье:\n{Sunday}\n\n"
        )


async def make_plane(update, context):
    user = update.message.from_user
    username = user.username

    try:
        existing_user = session.query(User).filter(User.user_name == username).first()
    except:
        return None

    if existing_user:

        await update.message.reply_text(
            f"Введите расписание на Понедельник (через запятую без пробелов)"
        )

        return 1

    else:
        await update.message.reply_text(
            f"Для начала создайте профиль /start"
        )
        return ConversationHandler.END


async def get_monday(update, context):
    user = update.message.from_user
    username = user.username

    # Обновляем данные в таблице
    session.query(User). \
        filter(User.user_name == username). \
        update({'monday': update.message.text})
    session.commit()

    await update.message.reply_text(
        f"Введите расписание на Вторник (через запятую без пробелов)"
    )

    return 2


async def get_tuesday(update, context):
    user = update.message.from_user
    username = user.username

    # Обновляем данные в таблице
    session.query(User). \
        filter(User.user_name == username). \
        update({'tuesday': update.message.text})
    session.commit()

    await update.message.reply_text(
        f"Введите расписание на Среду (через запятую без пробелов)"
    )

    return 3


async def get_wednesday(update, context):
    user = update.message.from_user
    username = user.username

    # Обновляем данные в таблице
    session.query(User). \
        filter(User.user_name == username). \
        update({'wednesday': update.message.text})
    session.commit()

    await update.message.reply_text(
        f"Введите расписание на Четверг (через запятую без пробелов)"
    )

    return 4


async def get_thursday(update, context):
    user = update.message.from_user
    username = user.username

    # Обновляем данные в таблице
    session.query(User). \
        filter(User.user_name == username). \
        update({'thursday': update.message.text})
    session.commit()

    await update.message.reply_text(
        f"Введите расписание на Пятницу (через запятую без пробелов)"
    )

    return 5


async def get_friday(update, context):
    user = update.message.from_user
    username = user.username

    # Обновляем данные в таблице
    session.query(User). \
        filter(User.user_name == username). \
        update({'friday': update.message.text})
    session.commit()

    await update.message.reply_text(
        f"Введите расписание на Субботу (через запятую без пробелов)"
    )

    return 6


async def get_saturday(update, context):
    user = update.message.from_user
    username = user.username

    # Обновляем данные в таблице
    session.query(User). \
        filter(User.user_name == username). \
        update({'saturday': update.message.text})
    session.commit()

    await update.message.reply_text(
        f"Введите расписание на Воскресенье (через запятую без пробелов)"
    )

    return 7


async def get_sunday(update, context):
    user = update.message.from_user
    username = user.username

    # Обновляем данные в таблице
    session.query(User). \
        filter(User.user_name == username). \
        update({'sunday': update.message.text})
    session.commit()

    await update.message.reply_text(
        f"Все данные успешно получены. Вы можете увидеть всё расписание по команде /get_plane"
    )

    return ConversationHandler.END


async def today_plane(update, context):
    user = update.message.from_user
    username = user.username

    try:
        existing_user = session.query(User).filter(User.user_name == username).first()
    except:
        return None

    if existing_user:

        get_user = session.query(User).filter(User.user_name == username).first()

        Monday = '\n'.join(str(get_user.monday).strip().split(','))
        Tuesday = '\n'.join(str(get_user.tuesday).strip().split(','))
        Wednesday = '\n'.join(str(get_user.wednesday).strip().split(','))
        Thursday = '\n'.join(str(get_user.thursday).strip().split(','))
        Friday = '\n'.join(str(get_user.friday).strip().split(','))
        Saturday = '\n'.join(str(get_user.saturday).strip().split(','))
        Sunday = '\n'.join(str(get_user.sunday).strip().split(','))

        # Получить текущую дату
        today = datetime.date.today()

        # Получить день недели (пн = 0, вт = 1, ..., вс = 6)
        weekday = today.weekday()

        # Определить название дня недели
        days_of_week = [Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]

        # Рандомный факт о кошках
        url_fact = f"https://catfact.ninja/fact"
        response_fact = requests.get(url_fact)
        data_fact = response_fact.json()
        fact_url = data_fact["fact"]

        await update.message.reply_text(
            f'А вы знали, что...  {fact_url}\n\nВаше расписание на сегодня:\n{days_of_week[weekday]}'
        )

    else:
        await update.message.reply_text(
            f"Для начала создайте профиль /start"
        )


async def stop(update, context):
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    text_handler = MessageHandler(filters.TEXT, outputs)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("get_plane", get_plane))
    application.add_handler(CommandHandler("today_plane", today_plane))

    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        entry_points=[CommandHandler('make_plane', make_plane)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_monday)],
            # Функция читает ответ на второй вопрос и задаёт третий.
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tuesday)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_wednesday)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_thursday)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_friday)],
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_saturday)],
            7: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sunday)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(conv_handler)

    echo_photo_handler = MessageHandler(filters.PHOTO, handle_photo)
    application.add_handler(echo_photo_handler)

    application.add_handler(text_handler)
    application.add_handler(CallbackQueryHandler(button_click))

    # Запускаем приложение.
    application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
