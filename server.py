# Импортируем необходимые классы.
import random
import datetime
import difflib
import asyncio
import requests
import logging
import os
import re
from PIL import Image, ImageOps, ImageDraw, ImageFont
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
class User(Base):  # База данных для профилей
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


class Game_history(Base):  # База данных для отображения истории игры
    __tablename__ = 'users_game_history'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    note = Column(Integer)


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

            await update.message.reply_text("Одну секунду...")

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

    elif 'waiting_for_information' in context.user_data and context.user_data['waiting_for_information']:
        try:
            del context.user_data['waiting_for_information']

            information = update.message.text.split()
            max_score = int(information[0])
            min_score = int(information[1])
            num_tasks = int(information[2])
            user_expectation = int(information[3])
            preference = str(information[4])
            hour = int(information[5])

            # Расчет ожидаемого балла на основе полученных данных
            expectation = (max_score + min_score) / 2

            # Изменение ожидаемого балла в зависимости от количества заданий
            if num_tasks > 0:
                expectation += (expectation / num_tasks)

            if user_expectation > max_score * 0.9:
                expectation *= 1.3
            elif user_expectation > max_score * 0.75:
                expectation *= 1.2
            elif user_expectation > max_score * 0.5:
                expectation *= 1.1
            else:
                expectation *= 0.7

            # Изменение ожидаемого балла в зависимости от времени написания
            if 8 <= hour < 12:  # Утро
                if preference == 'утро':
                    expectation *= 1.2
                elif preference == 'день':
                    expectation *= 1.1
                elif preference == 'вечер':
                    expectation *= 0.8

            elif 12 <= hour < 18:  # День
                if preference == 'утро':
                    expectation *= 1.1
                elif preference == 'день':
                    expectation *= 1.2
                elif preference == 'вечер':
                    expectation *= 0.8

            elif 18 <= hour <= 23:  # Вечер
                if preference == 'утро':
                    expectation *= 0.8
                elif preference == 'день':
                    expectation *= 1.1
                elif preference == 'вечер':
                    expectation *= 1.2

            else:  # Самое плохое время
                expectation *= 0.7

            if expectation > max_score:
                expectation = max_score

            await update.message.reply_text(f'Вы: {user_expectation} VS  Бот: {round(expectation, 1)}')

            temporary_user = update.message.from_user
            temporary_username = temporary_user.username

            new_note = Game_history(name=temporary_username, note=f'Вы: '
                                                                  f'{max_score} {min_score} {num_tasks} {user_expectation} '
                                                                  f'{preference} {hour} VS  Бот: {round(expectation, 1)}')

            session.add(new_note)
            session.commit()

        except:
            await update.message.reply_text(f'Ошибка: Неверный ввод данных')

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

    else:
        messages = [
            "Когда ты понимаешь, что не понимаешь...",
            "Пытаюсь понять, что я не понимаю, но не понимаю, что не понимаю!",
            "В мире полно загадок, но самая большая загадка - мое непонимание.",
            "Когда тебе говорят что-то не понятное, а ты делаешь вид, что понял, но на самом деле не понимаешь ни "
            "черта.",
            "Загадки, загадки, а я все равно не понимаю...",
            "Понимание - это такая роскошь, которой мне по-прежнему не понять.",
            "Чем дальше в лес, тем больше непонимания.",
            "В мире много вопросов, но я не понимаю даже ответов.",
            "Когда кажется, что все понимают, а ты даже не понимаешь что они понимают...",
            "Не могу понять, почему я не понимаю?",
            "Понимание - это когда ты понимаешь, что не понимаешь, но все равно не понимаешь.",
            "В мире много тайн, а я просто не понимаю их.",
            "Почему так сложно понять, что не понимаешь?",
            "Запутался в собственном непонимании...",
            "Понимаю, что не понимаю, но все равно не понимаю.",
            "Жизнь - это книга загадок, а я не могу расшифровать ни одной страницы.",
            "Чем больше я учусь, тем больше непонимания в мире.",
            "Я не понимаю, почему я не понимаю?",
            "Непонимание - это когда ты слышишь слова, но не понимаешь их смысла.",
            "Понимание - это не про меня...",
            "Непонимание - это моя вторая половина.",
            "Когда ты уже потерялся в собственном непонимании и не можешь найти выход.",
            "Я не понимаю, почему я не понимаю?",
            "Непонимание - это мое второе имя.",
            "Чем больше я узнаю, тем больше непонимания в мире.",
            "Я вечный студент непонимания.",
            "Когда все говорят на одном языке, а ты остаешься на другом...",
            "Понимать или не понимать, вот в чем вопрос.",
            "Мир загадок, а я просто не могу их разгадать.",
            "Может быть, я не так понял, но я даже не понимаю своего непонимания.",
            "Понимание - это чужая планета для меня.",
            "Загадки, загадки, а я все равно не могу их решить.",
            "Когда ты пытаешься понять, но у тебя ничего не получается...",
            "Я не понимаю, почему понимание не приходит ко мне.",
            "Не понимать - это новое понимание.",
            "Когда все видят, а я не понимаю.",
            "Не понимаешь - не горюй, это не твой стиль.",
            "Непонимание - это мое хобби.",
            "Плыву по течению непонимания...",
            "Подари мне понимание, а я верну тебе непонимание.",
            "Когда ты погружаешься в мир непонимания и туда заблудился...",
            "Понимание - это как оазис в пустыне, который мне никогда не увидеть.",
            "Новый день, новое непонимание.",
            "Понимание - это как запретный плод, который мне не угодить.",
            "В мире много вопросов, но ноль ответов на моем языке.",
            "Я вечный искатель понимания.",
            "Не понимать - это быть как все.",
            "Может быть, я не так понимаю, но я даже не понимаю, что не понимаю.",
            "Понимание - это как сказка, которую мне не рассказывали.",
            "В мире много людей, которые понимают, но я не к ним отношусь.",
            "Понимание - это как чужой ноутбук, на котором мне не разобраться.",
            "Когда ты думаешь, что понимаешь, но на самом деле вообще не понимаешь.",
            "Непонимание - это когда все слова звучат как ноты, а ты не можешь собрать из них мелодию.",
            "Понимание - это как оазис в пустыне, который мне никогда не увидеть.",
            "Загадки, загадки, а я все равно не могу их решить.",
            "Когда ты сталкиваешься с непониманием, а оно как дымка прячется от тебя.",
            "Я заблудился в своем собственном непонимании.",
            "Понимание - это как запретный плод, который мне не угодить.",
            "В мире много вопросов, но ноль ответов на моем языке.",
            "Я вечный искатель понимания.",
            "Не понимать - это быть как все.",
            "Может быть, я не так понимаю, но я даже не понимаю, что не понимаю.",
            "Понимание - это как сказка, которую мне не рассказывали.",
            "В мире много людей, которые понимают, но я не к ним отношусь.",
            "Понимание - это как чужой ноутбук, на котором мне не разобраться.",
            "Когда ты думаешь, что понимаешь, но на самом деле вообще не понимаешь.",
            "Непонимание - это когда все слова звучат как ноты, а ты не можешь собрать из них мелодию.",
            "Понимание - это как оазис в пустыне, который мне никогда не увидеть.",
            "Загадки, загадки, а я все равно не могу их решить.",
            "Когда ты сталкиваешься с непониманием, а оно как дымка прячется от тебя.",
            "Я заблудился в своем собственном непонимании.",
            "Понимание - это как запретный плод, который мне не угодить.",
            "В мире много вопросов, но ноль ответов на моем языке.",
            "Я вечный искатель понимания.",
            "Не понимать - это быть как все.",
            "Может быть, я не так понимаю, но я даже не понимаю, что не понимаю.",
            "Понимание - это как сказка, которую мне не рассказывали.",
            "В мире много людей, которые понимают, но я не к ним отношусь.",
            "Понимание - это как чужой ноутбук, на котором мне не разобраться.",
            "Когда ты думаешь, что понимаешь, но на самом деле вообще не понимаешь.",
            "Непонимание - это когда все слова звучат как ноты, а ты не можешь собрать из них мелодию.",
            "Понимание - это как оазис в пустыне, который мне никогда не увидеть.",
            "Загадки, загадки, а я все равно не могу их решить.",
            "Когда ты сталкиваешься с непониманием, а оно как дымка прячется от тебя.",
            "Я заблудился в своем собственном непонимании.",
            "Понимание - это как запретный плод, который мне не угодить.",
            "В мире много вопросов, но ноль ответов на моем языке.",
            "Я вечный искатель понимания.",
            "Не понимать - это быть как все.",
            "Может быть, я не так понимаю, но я даже не понимаю, что не понимаю.",
            "Понимание - это как сказка, которую мне не рассказывали.",
            "В мире много людей, которые понимают, но я не к ним отношусь.",
            "Понимание - это как чужой ноутбук, на котором мне не разобраться.",
            "Когда ты думаешь, что понимаешь, но на самом деле вообще не понимаешь.",
            "Непонимание - это когда все слова звучат как ноты, а ты не можешь собрать из них мелодию.",
            "Понимание - это как оазис в пустыне, который мне никогда не увидеть.",
            "Загадки, загадки, а я все равно не могу их решить.",
            "Когда ты сталкиваешься с непониманием, а оно как дымка прячется от тебя.",
            "Я заблудился в своем собственном непонимании.",
            "Понимание - это как запретный плод, который мне не угодить.",
            "В мире много вопросов, но ноль ответов на моем языке.",
            "Я вечный искатель понимания.",
            "Не понимать - это быть как все.",
            "Может быть, я не так понимаю, но я даже не понимаю, что не понимаю.",
            "Понимание - это как сказка, которую мне не рассказывали.",
            "В мире много людей, которые понимают, но я не к ним отношусь.",
            "Понимание - это как чужой ноутбук, на котором мне не разобраться.",
            "Когда ты думаешь, что понимаешь, но на самом деле вообще не понимаешь.",
            "Непонимание - это когда все слова звучат как ноты, а ты не можешь собрать из них мелодию.",
            "Понимание - это как оазис в пустыне, который мне никогда не увидеть.",
            "Загадки, загадки, а я все равно не могу их решить.",
            "Когда ты сталкиваешься с непониманием, а оно как дымка прячется от тебя.",
            "Я заблудился в своем собственном непонимании.",
            "Понимание - это как запретный плод, который мне не угодить.",
            "В мире много вопросов, но ноль ответов на моем языке.",
            "Я вечный искатель понимания.",
            "Не понимать - это быть как все.",
            "Может быть, я не так понимаю, но я даже не понимаю, что не понимаю.",
            "Понимание - это как сказка, которую мне не рассказывали.",
            "В мире много людей, которые понимают, но я не к ним отношусь.",
            "Понимание - это как чужой ноутбук, на котором мне не разобраться.",
            "Когда ты думаешь, что понимаешь, но на самом деле вообще не понимаешь.",
            "Непонимание - это когда все слова звучат как ноты, а ты не можешь собрать из них мелодию.",
            "Понимание - это как оазис в пустыне, который мне никогда не увидеть.",
            "Загадки, загадки, а я все равно не могу их решить.",
            "Когда ты сталкиваешься с непониманием, а оно как дымка прячется от тебя.",
            "Я заблудился в своем собственном непонимании.",
            "Понимание - это как запретный плод, который мне не угодить.",
            "В мире много вопросов, но ноль ответов на моем языке.",
            "Я вечный искатель понимания.",
            "Не понимать - это быть как все.",
            "Может быть, я не так понимаю, но я даже не понимаю, что не понимаю.",
            "Понимание - это как сказка, которую мне не рассказывали.",
            "В мире много людей, которые понимают, но я не к ним отношусь.",
            "Понимание - это как чужой ноутбук, на котором мне не разобраться.",
            "Когда ты думаешь, что понимаешь, но на самом деле вообще не понимаешь.",
            "Непонимание - это когда все слова звучат как ноты, а ты не можешь собрать из них мелодию.",
            "Понимание - это как оазис в пустыне, который мне никогда не увидеть.",
            "Загадки, загадки, а я все равно не могу их решить.",
            "Когда ты сталкиваешься с непониманием, а оно как дымка прячется от тебя.",
            "Я заблудился в своем собственном непонимании.",
            "Понимание - это как запретный плод, который мне не угодить.",
            "В мире много вопросов, но ноль ответов на моем языке.",
            "Я вечный искатель понимания."]

        await update.message.reply_text(random.choice(messages))


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
        f"Здравствуйте, уважаемый {user.mention_html()}! Меня зовут Вениамин, и я рад приветствовать вас."
        f" Если у вас еще не возникла необходимость в создании профиля, пожалуйста,"
        f" примите во внимание возможность создания его для более удобного и эффективного взаимодействия.",
        reply_markup=markup
    )


async def profile(update, context):
    context.user_data['waiting_for_name'] = True
    await update.message.reply_html(
        rf"Введите, пожалуйста, ваше имя. У нас очень простая система регистрации :)",
    )


async def get_help(update, context):
    html_document = (
        'Для общения с ботом используются команды:'
        '\n\n\n<i>/searchcountry [страна] - Поиск университетов по стране</i> &#127758'
        '\n\n<i>/searchname [название института] - Поиск информации о университете</i> &#127963'
        '\n\nОстальные команды находятся в <b>≡ Меню</b>'
        '\n\nДля создания профиля введите /start и нажмите кнопку <b>Профиль</b> &#129421'
        '\n\nЧтобы создать свой <b>стикер</b> пришлите <b>фото</b> с описанием(через пробел):'
        '<i>\n - &#128208 Ширина рамки</i>'
        '<i>\n - &#128150 Цвет рамки</i>'
        '<i>\n - &#127912 Цвет текста на стикере</i>'
        '<i>\n - &#128221 Текст (до ± 36 символов, отображающихся корректно на стикере.'
        ' Чтобы оставить поле для текста пустым, введите <b>None</b>)</i>'
    )

    await update.message.reply_text(html_document, parse_mode='HTML')


def delete_user(existing_user):
    session.query(User).filter(User.user_name == existing_user).delete()
    session.query(Game_history).filter(Game_history.name == existing_user).delete()
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
    try:
        new_file = await update.message.effective_attachment[-1].get_file()
        file = await new_file.download_to_drive()

        # Открыть изображение PIL
        image = Image.open(file)

        # 512x512
        resized_image = image.resize((512, 512))

        # Рамка
        # Извлечь размер рамки, цвет рамки и текст из описания под фото
        caption = update.message.caption
        info_match = re.search(r'(\d+) (\w+) (\w+) (.+)', caption)

        if info_match:
            border_size = int(info_match.group(1))
            border_color = info_match.group(2)
            text_color = info_match.group(3)
            text = info_match.group(4)
            if text == 'None':
                text = ''

        else:
            border_size = 10  # По умолчанию
            border_color = 'white'  # По умолчанию
            text_color = 'white'  # По умолчанию
            text = ''  # По умолчанию

        bordered_image = ImageOps.expand(resized_image, border=border_size, fill=border_color)
        bordered_image1 = ImageOps.expand(resized_image, border=border_size, fill=border_color)

        texts = []

        if len(text) > 17:
            texts.append(text[:17])
            texts.append(text[17:])

            draw = ImageDraw.Draw(bordered_image)
            font = ImageFont.truetype("arial.ttf", 50)
            text_width, text_height = draw.textsize(text, font)
            draw.text((15, (512 - text_height) // 2), texts[0], fill=text_color, font=font)
            draw.text((15, (512 - text_height) // 1.6), texts[1], fill=text_color, font=font)

            draw = ImageDraw.Draw(bordered_image1)
            draw.text((15, (512 - text_height) // 2), texts[0], fill=text_color, font=font)
            draw.text((15, (512 - text_height) // 1.6), texts[1], fill=text_color, font=font)

        else:

            # Добавить текст на изображение
            draw = ImageDraw.Draw(bordered_image)
            font = ImageFont.truetype("arial.ttf", 50)
            text_width, text_height = draw.textsize(text, font)
            draw.text(((512 - text_width) // 2, (512 - text_height) // 2), text, fill=text_color, font=font)

            draw = ImageDraw.Draw(bordered_image1)
            draw.text(((512 - text_width) // 2, (512 - text_height) // 2), text, fill=text_color, font=font)

        # Стикер
        sticker_file = "bordered_image_sticker.webp"
        bordered_image.save(sticker_file, "WEBP")
        sticker_file1 = "bordered_image1_sticker1.png"
        bordered_image1.save(sticker_file1, "PNG")

        await update.message.reply_html(
            "Я успешно получил данное фото и преобразовал в стикер. Вы можете создать набор с этим стикером, "
            "загрузив следующий файл PNG в бота по ссылке "
            "https://t.me/StickerReceiverBot"
        )

        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=open(sticker_file, 'rb'))

        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(sticker_file1, 'rb'))

        os.remove(file)

    except:
        await update.message.reply_html(
            "Ошибка: Некорректное фото или описание. Если вы хотите получить стикер, введите "
            "через пробел(ширина рамки(10...), цвет рамки(white...), текст для отображения на стикере("
            "чтобы отсавить поле для текста пустым введите None))",
        )

        os.remove(file)


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
            f"Введите расписание на Понедельник (через запятую без пробелов). /stop - остановиться."
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


async def Expectation_vs_Reality(update, context):
    user = update.message.from_user
    username = user.username

    try:
        existing_user = session.query(User).filter(User.user_name == username).first()
    except:
        return None

    if existing_user:
        html_document = ('<b>Добро пожаловать в игру EXPECTATION vs REALITY! &#128579;</b>\n\n'
                         'Введите через пробел:'
                         '\n- <i>Максимальный балл</i>'
                         '\n- <i>Минимальный балл</i>'
                         '\n- <i>Количество заданий</i>'
                         '\n- <i>Ожидаемый результат</i>'
                         '\n- <i>В какое время суток вы соображаете лучше (утро, день, вечер)</i>'
                         '\n- <i>Время написания (час по типу: 15, 16, 9)</i>')

        await update.message.reply_text(html_document, parse_mode='HTML')

        context.user_data['waiting_for_information'] = True

    else:
        await update.message.reply_text('Для начала создайте профиль /start')


async def check_game_history(update, context):
    try:
        history = []
        user = update.message.from_user
        username = user.username
        notes = session.query(Game_history).filter(Game_history.name == username).all()

        for idx, note in enumerate(notes, start=1):
            history.append(f'{idx}. {note.note}')

        await update.message.reply_text('\n\n'.join(history))
    except:
        await update.message.reply_text('Нет истории')


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    text_handler = MessageHandler(filters.TEXT, outputs)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("get_schedule", get_plane))
    application.add_handler(CommandHandler("today_schedule", today_plane))
    application.add_handler(CommandHandler("Expectation_vs_Reality", Expectation_vs_Reality))
    application.add_handler(CommandHandler("check_game_history", check_game_history))

    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        entry_points=[CommandHandler('make_schedule', make_plane)],

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
