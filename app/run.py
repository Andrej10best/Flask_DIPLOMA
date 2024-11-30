"""
Данный файл представляет собой основной файл приложения на Flask, который отвечает за настройку и запуск
веб-приложения для бронирования туров
"""

import os
import logging.config
from flask import Flask, render_template
from flask_mail import Mail, Message
from database.db import create_tables
from routes.admin_routes import setup_admin_routes
from routes.routes import setup_routes
from log_set.log_setting import LOGGING

# Настройка логирования
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('log')

# Создание экземпляра приложения Flask
app = Flask(__name__, template_folder='templates')

# Определение базового пути и создание папки для загрузки изображений
base_path = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(base_path, 'static', 'image', 'img_tour')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Настройка секретного ключа для сессий
app.config['SECRET_KEY'] = 'jsdhfuihf13485hjadsnvj98sdva8y7v'

# Настройка конфигурации для отправки почты
app.config['MAIL_SERVER'] = 'smtp.yandex.ru'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'Andrej10best@yandex.ru'
app.config['MAIL_PASSWORD'] = 'xwijghlbqktxboja'
app.config['MAIL_DEFAULT_SENDER'] = 'Andrej10best@yandex.ru'

# Инициализация расширения Flask-Mail
mail = Mail(app)

# Настройка маршрутов приложения
setup_routes(app)
setup_admin_routes(app)


@app.route('/success/<email>/<title>/<date>/<duration>/<number_of_people>/<price>')
def success_page(email, title, date, duration, number_of_people, price):
    """
        Обрабатывает успешное бронирование тура и отправляет уведомление на указанный email.

        Параметры:
        email (str): Email адрес получателя.
        title (str): Название тура.
        date (str): Дата начала тура.
        duration (str): Длительность тура в днях.
        number_of_people (str): Количество людей, бронирующих тур.
        price (str): Стоимость за человека.

        Возвращает:
        str: HTML-страница с подтверждением бронирования.
        """
    msg = Message('Tours for the soul. Добро пожаловать!', recipients=[email])
    msg.body = (f'\nБлагодарим Вас за бронирование тура!\n'
                f'Вами был выбран тур: {title}\n'
                f'Дата старта тура: {date}\n'
                f'Длительность тура: {duration} дн.\n'
                f'Количество людей: {number_of_people}\n'
                f'Стоимость за человека: {price} руб.\n'
                f'В течении 24 часов с Вами свяжется наш менеджер для уточнения дополнительных деталей и '
                f'информировании о предстоящем туре. Пожалуйста ожидайте звонка!')
    try:
        mail.send(msg)
        logger.info('Email успешно отправлен на адрес %s', email)
    except Exception as e:
        logger.error(
            'Ошибка при отправке email на адрес %s: %s', email, str(e))

    return render_template('user/success_book_page.html')


@app.errorhandler(404)
def page_not_found(e):
    """
        Обрабатывает ошибки 404 (страница не найдена).

        Параметры:
        e (Exception): Исключение, вызвавшее ошибку.

        Возвращает:
        tuple: HTML-страница ошибки 404 и код состояния 404.
        """
    logger.warning('Страница не найдена: %s', str(e))
    return render_template('user/error_page.html'), 404


if __name__ == '__main__':
    # Создание таблиц в базе данных и запуск приложени
    create_tables()
    logger.info('Приложение запущено')
    try:
        app.run()
    except Exception as e:
        logger.critical('Приложение остановлено с ошибкой: %s', str(e))
    finally:
        logger.info('Приложение остановлено')
