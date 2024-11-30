"""
Данный файл отвечает за настройку маршрутов и обработку запросов для пользователя в веб-приложении.
"""

import re
import logging.config
from flask import render_template, request, flash, redirect, url_for
from database.db import SessionLocal, TourTable, UserTable
from sqlalchemy import select
from log_set.log_setting import LOGGING

# Настройка логирования
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('log')


def setup_routes(app):
    """
        Настраивает маршруты для приложения Flask.

        Аргументы:
            app: Экземпляр приложения Flask, к которому будут добавлены маршруты.
        """

    @app.route('/')
    def welcome_page():
        """
            Обрабатывает запросы на главную страницу.

            Возвращает шаблон главной страницы и записывает в лог информацию о входе пользователя.
            """
        logger.info('Пользователь зашел на главную страницу.')
        return render_template('user/base_page.html')

    @app.route('/views/tours/')
    def tours_page():
        """
            Обрабатывает запросы на страницу со списком туров.

            Извлекает список туров из базы данных и отображает его. Если список пуст,
            возвращает страницу с сообщением об отсутствии туров.
            """
        with SessionLocal() as sessionloc:
            query = select(TourTable)
            result = sessionloc.execute(query)
            tour_models = result.scalars().all()
            if not tour_models:
                logger.info('Список туров пуст.')
                return render_template('user/empty_list_tours_page.html')

        logger.info('Отображение списка туров, найдено %d туров.', len(tour_models))
        return render_template('user/list_tours_page.html', tour_models=tour_models)

    @app.route('/current_tour/<tour_id>', methods=['POST', 'GET'])
    def current_tour(tour_id):
        """
            Обрабатывает запросы на страницу конкретного тура.

            Аргументы:
                tour_id (str): Идентификатор тура.

            Возвращает страницу с информацией о туре. Если метод запроса POST,
            обрабатывает данные формы для бронирования тура.
            """
        with SessionLocal() as sessionloc:
            query = select(TourTable).where(TourTable.id == tour_id)
            result = sessionloc.execute(query)
            tour_model = result.scalars().first()

            if not tour_model:
                logger.warning('Тур с ID %s не найден.', tour_id)
                return render_template('user/error_page.html')

            if request.method == 'POST':
                # Получение данных из формы
                name = request.form['name']
                email = request.form['email']
                phone = request.form['phone']
                number_of_people = request.form['number_of_people']

                # Проверка доступности мест
                if int(number_of_people) > tour_model.available_places:
                    flash('Кол-во людей больше кол-ва мест', category='error')
                    logger.warning('Пользователь попытался забронировать %s мест, но доступно только %s.',
                                   number_of_people, tour_model.available_places)
                    return redirect(url_for('current_tour', tour_id=tour_id))

                # Проверка на корректность количества людей
                if int(number_of_people) < 1:
                    flash('Вы не указали кол-во людей', category='error')
                    logger.warning('Пользователь не указал количество людей.')
                    return redirect(url_for('current_tour', tour_id=tour_id))

                # Проверка на корректность email
                if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', request.form['email']):
                    flash('Введите корректный email', category='error')
                    logger.warning('Некорректный email: %s', email)
                    return redirect(url_for('current_tour', tour_id=tour_id))

                # Проверка на корректность номера телефона
                if request.form['phone'] and not re.match(r"^\+7\d{10}$", str(request.form['phone'])):
                    flash('Номер должен начинаться с +7 в формате +7XXXXXXXXXX, где X-цифры', category='error')
                    logger.warning('Некорректный номер телефона: %s', phone)
                    return redirect(url_for('current_tour', tour_id=tour_id))

                # Если все проверки пройдены, создаем нового пользователя
                else:
                    new_user = UserTable(
                        name=name,
                        email=email,
                        phone=phone,
                        number_of_people=number_of_people,
                        tour_id=tour_id
                    )

                    # Обновляем количество доступных и занятых мест
                    tour_model.available_places -= int(number_of_people)
                    tour_model.occupied_places += int(number_of_people)
                    sessionloc.add(new_user)
                    sessionloc.commit()

                    logger.info('Пользователь %s успешно забронировал %s мест на тур с ID %s.',
                                name, number_of_people, tour_id)

                    # Перенаправление на страницу успеха с переданными параметрами для отправки email
                    title = tour_model.title
                    date = tour_model.start_date_tour
                    duration = tour_model.duration
                    price = tour_model.price_per_person

                    return redirect(url_for('success_page',
                                            email=email,
                                            title=title,
                                            date=date,
                                            duration=duration,
                                            number_of_people=number_of_people,
                                            price=price
                                            )
                                    )

            logger.info('Отображение страницы бронирования для тура с ID %s.', tour_id)
            return render_template('user/book_tour_page.html', tour_model=tour_model)
