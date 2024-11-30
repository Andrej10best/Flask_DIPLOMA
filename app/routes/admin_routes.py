"""
Данный файл отвечает за настройку маршрутов и обработку запросов для админа в веб-приложении.
"""

import os
import re
import logging.config
from config import *
from flask import render_template, session, redirect, url_for, request, abort, flash
from database.db import SessionLocal, TourTable, UserTable
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from log_set.log_setting import LOGGING

# Настройка логирования
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('log')

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    """
        Проверяет, разрешено ли загружать файл с указанным именем.

        Аргументы:
            filename (str): Имя файла для проверки.

        Возвращает:
            bool: True, если файл имеет допустимое расширение, иначе False.
        """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def setup_admin_routes(app):
    """
        Настраивает маршруты для админ-панели приложения Flask.

        Аргументы:
            app: Экземпляр приложения Flask, к которому будут добавлены маршруты.
        """

    @app.route('/admin', methods=['POST', 'GET'])
    def admin_page():
        """
            Обрабатывает запросы на страницу авторизации админа.

            Если пользователь уже авторизован, перенаправляет на профиль.
            При успешной авторизации сохраняет информацию в сессии и перенаправляет на профиль.
                """
        if 'userLogged' in session:
            logger.info('Пользователь %s уже авторизован, перенаправление на профиль.', session['userLogged'])
            return redirect(url_for('profile_page', username=session['userLogged']))
        elif request.method == 'POST' and request.form['username'] == login and request.form['psw'] == psw:
            session['userLogged'] = request.form['username']
            logger.info('Пользователь %s успешно авторизован.', session['userLogged'])
            return redirect(url_for('profile_page', username=session['userLogged']))

        return render_template('admin/admin_login.html')

    @app.route('/profile/<username>', methods=['POST', 'GET'])
    def profile_page(username):
        """
            Отображает профиль админа и предоставляет доступ к действиям.

            Аргументы:
                username (str): Имя пользователя, для которого отображается профиль.

            Возвращает:
                HTML: Шаблон профиля админа или перенаправление в случае неавторизованного доступа.
            """
        if 'userLogged' not in session or session['userLogged'] != username:
            logger.warning('Неавторизованный доступ к профилю %s', username)
            abort(401)

        if request.method == 'POST':
            action = request.form.get('action')
            logger.info('Пользователь %s выбрал действие: %s', username, action)
            if action == "Добавить тур":
                return redirect(url_for('add_tour_page', username=session['userLogged']))
            elif action == "Изменить/удалить тур":
                return redirect(url_for('up_del_tour_page', username=session['userLogged']))
            elif action == "Клиенты":
                return redirect(url_for('clients', username=session['userLogged']))

        return render_template('admin/admin_edit_list.html')

    @app.route('/clients/<username>')
    def clients(username):
        """
            Отображает список клиентов.

            Аргументы:
                username (str): Имя пользователя, для которого отображается список клиентов.

            Возвращает:
                HTML: Шаблон со списком клиентов или сообщение об отсутствии клиентов.
            """
        if 'userLogged' not in session or session['userLogged'] != username:
            logger.warning('Неавторизованный доступ к клиентам %s', username)
            abort(401)

        with SessionLocal() as sessionloc:
            query = select(UserTable).options(joinedload(UserTable.tour))
            result = sessionloc.execute(query)
            user_models = result.scalars().all()

            if not user_models:
                logger.info('Список клиентов пуст.')
                return render_template('user/empty_list_users_page.html')

        logger.info('Отображение списка клиентов для %s', username)
        return render_template('admin/admin_clients_page.html', user_models=user_models)

    @app.route('/up_del_tour_page/<username>', methods=['POST', 'GET'])
    def up_del_tour_page(username):
        """
            Отображает страницу для изменения или удаления туров.

            Аргументы:
                username (str): Имя пользователя, для которого отображается страница.

            Возвращает:
                HTML: Шаблон со списком туров или сообщение об отсутствии туров.
            """
        if 'userLogged' not in session or session['userLogged'] != username:
            logger.warning('Неавторизованный доступ к изменению/удалению туров %s', username)
            abort(401)

        with SessionLocal() as sessionloc:
            query = select(TourTable)
            result = sessionloc.execute(query)
            tour_models = result.scalars().all()
            if not tour_models:
                logger.info('Список туров пуст.')
                return render_template('user/empty_list_tours_page.html')

        logger.info('Отображение списка туров для %s', username)
        return render_template('admin/admin_up_or_del_tour_page.html', tour_models=tour_models)

    @app.route('/up_del_tour_page/update/<tour_id>', methods=['POST', 'GET'])
    def update_tour(tour_id):
        """
            Обрабатывает запросы на обновление информации о туре.

            Аргументы:
                tour_id (str): Идентификатор тура, который необходимо обновить.

            Возвращает:
                HTML: Шаблон для обновления тура или сообщение об ошибках валидации.
            """
        if request.method == 'POST':
            with SessionLocal() as sessionloc:
                query = select(TourTable).where(TourTable.id == tour_id)
                result = sessionloc.execute(query)
                tour_model = result.scalars().first()

                if not tour_model:
                    logger.warning('Тур с ID %s не найден для обновления.', tour_id)
                    return render_template('user/empty_list_tours_page.html')

                # Получение данных из формы
                title = request.form['title']
                description = request.form['description']
                place = request.form['place']
                start_date_tour = request.form['start_date_tour']
                duration = request.form['duration']
                max_people = request.form['max_people']
                available_places = request.form['available_places']
                occupied_places = request.form['occupied_places']
                price_per_person = request.form['price_per_person']

                # Проверка на длину заголовка
                if len(title) > 17:
                    flash('Длина заголовка более 17 символов', category='error')
                    logger.warning('Ошибка валидации для тура %s: длина заголовка более 17 символов',
                                   tour_id)
                    return redirect(url_for('update_tour', tour_id=tour_id))

                # Проверка на длину описания
                if len(description) > 1100:
                    flash('Длина описания более 1100 символов', category='error')
                    logger.warning('Ошибка валидации для тура %s: длина описания более 1100 символов',
                                   tour_id)
                    return redirect(url_for('update_tour', tour_id=tour_id))

                # Проверка на длину локации
                if len(place) > 27:
                    flash('Длина локации более 27 символов', category='error')
                    logger.warning('Ошибка валидации для тура %s: длина локации более 27 символов', tour_id)
                    return redirect(url_for('update_tour', tour_id=tour_id))

                # Проверка на формат даты
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', start_date_tour):
                    flash('Формат даты XXXX-XX-XX, где Х - число', category='error')
                    logger.warning('Ошибка валидации для тура %s: неверный формат даты', tour_id)
                    return redirect(url_for('update_tour', tour_id=tour_id))

                # Проверка на длительность тура
                if not re.match(r'^\d+', duration):
                    flash('Длительность тура должна быть в виде числа', category='error')
                    logger.warning('Ошибка валидации для тура %s: длительность не является числом', tour_id)
                    return redirect(url_for('update_tour', tour_id=tour_id))

                # Проверка на максимальное кол-во людей
                if not re.match(r'^\d+', max_people):
                    flash('Максимальное кол-во человек должно быть в виде числа', category='error')
                    logger.warning('Ошибка валидации для тура %s: максимальное количество не является числом',
                                   tour_id)
                    return redirect(url_for('update_tour', tour_id=tour_id))

                # Проверка на кол-во свободных мест
                if not re.match(r'^\d+', available_places):
                    flash('Кол-во свободных мест должно быть в виде числа', category='error')
                    logger.warning(
                        'Ошибка валидации для тура %s: количество свободных мест не является числом',
                        tour_id)
                    return redirect(url_for('update_tour', tour_id=tour_id))

                # Сравнивание свободных мест и максимальное кол-во мест
                if available_places > max_people:
                    flash('Кол-во свободных мест должно быть меньше максимального кол-ва мест',
                          category='error')
                    logger.warning('Ошибка валидации для тура %s: свободные места больше максимального',
                                   tour_id)
                    return redirect(url_for('update_tour', tour_id=tour_id))

                # Сравнивание занятых мест и свободных
                if occupied_places > available_places:
                    flash('Кол-во занятых мест должно быть меньше кол-ва свободных', category='error')
                    logger.warning('Ошибка валидации для тура %s: занятые места больше свободных', tour_id)
                    return redirect(url_for('update_tour', tour_id=tour_id))

                # Проверка цены
                if not re.match(r'^\d+', price_per_person):
                    flash('Значение цены должно быть в виде числа', category='error')
                    logger.warning('Ошибка валидации для тура %s: цена не является числом', tour_id)
                    return redirect(url_for('update_tour', tour_id=tour_id))

                # Если все проверки пройдены, обновляем тур
                else:
                    tour_model.title = title
                    tour_model.description = description
                    tour_model.place = place
                    tour_model.start_date_tour = start_date_tour
                    tour_model.duration = duration
                    tour_model.max_people = max_people
                    tour_model.available_places = available_places
                    tour_model.occupied_places = occupied_places
                    tour_model.price_per_person = price_per_person

                    sessionloc.commit()
                    flash('Тур успешно обновлен', category='success')
                    logger.info('Тур с ID %s успешно обновлен.', tour_id)
                    return redirect(url_for('update_tour', tour_id=tour_id))

        return render_template('admin/admin_update_tour_page.html')

    @app.route('/add_tour_page/<username>', methods=['POST', 'GET'])
    def add_tour_page(username):
        """
            Обрабатывает запросы на добавление нового тура.

            Аргументы:
                username (str): Имя пользователя, добавляющего тур.

            Возвращает:
                HTML: Шаблон для добавления тура или сообщение об ошибках валидации.
            """
        if 'userLogged' not in session or session['userLogged'] != username:
            logger.warning('Неавторизованный доступ к добавлению тура %s', username)
            abort(401)

        if request.method == 'POST':
            # Проверка наличия файла в запросе
            if 'image_path' not in request.files:
                logger.warning('Файл изображения отсутствует в запросе.')
                return redirect(request.url)
            file = request.files['image_path']

            # Если файл пустой, перенаправляем
            if file.filename == '':
                logger.warning('Файл изображения пустой.')
                return redirect(request.url)

            # Проверяем разрешение файла
            if file and allowed_file(file.filename):
                filename = file.filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                logger.info('Файл изображения %s успешно загружен.', filename)

            # Получение данных из формы
            title = request.form['title']
            description = request.form['description']
            place = request.form['place']
            start_date_tour = request.form['start_date_tour']
            duration = request.form['duration']
            max_people = request.form['max_people']
            available_places = request.form['available_places']
            occupied_places = request.form['occupied_places']
            price_per_person = request.form['price_per_person']

            # Валидация данных идентичная проверки на обновление тура
            if len(title) > 17:
                flash('Длина заголовка более 17 символов', category='error')
                logger.warning('Ошибка валидации при добавлении тура: длина заголовка более 17 символов')
                return redirect(url_for('add_tour_page', username=username))

            if len(description) > 1100:
                flash('Длина описания более 1100 символов', category='error')
                logger.warning('Ошибка валидации при добавлении тура: длина описания более 1100 символов')
                return redirect(url_for('add_tour_page', username=username))

            if len(place) > 27:
                flash('Длина локации более 27 символов', category='error')
                logger.warning('Ошибка валидации при добавлении тура: длина локации более 27 символов')
                return redirect(url_for('add_tour_page', username=username))

            if not re.match(r'^\d{4}-\d{2}-\d{2}$', start_date_tour):
                flash('Формат даты XXXX-XX-XX, где Х - число', category='error')
                logger.warning('Ошибка валидации при добавлении тура: неверный формат даты')
                return redirect(url_for('add_tour_page', username=username))

            if not re.match(r'^\d+', duration):
                flash('Длительность тура должна быть в виде числа', category='error')
                logger.warning('Ошибка валидации при добавлении тура: длительность не является числом')
                return redirect(url_for('add_tour_page', username=username))

            if not re.match(r'^\d+', max_people):
                flash('Максимальное кол-во человек должно быть в виде числа', category='error')
                logger.warning('Ошибка валидации при добавлении тура: максимальное количество не является числом')
                return redirect(url_for('add_tour_page', username=username))

            if not re.match(r'^\d+', available_places):
                flash('Кол-во свободных мест должно быть в виде числа', category='error')
                logger.warning('Ошибка валидации при добавлении тура: количество свободных мест не является числом')
                return redirect(url_for('add_tour_page', username=username))

            if available_places > max_people:
                flash('Кол-во свободных мест должно быть меньше максимального кол-ва мест', category='error')
                logger.warning('Ошибка валидации при добавлении тура: свободные места больше максимального')
                return redirect(url_for('add_tour_page', username=username))

            if occupied_places > available_places:
                flash('Кол-во занятых мест должно быть меньше кол-ва свободных', category='error')
                logger.warning('Ошибка валидации при добавлении тура: занятые места больше свободных')
                return redirect(url_for('add_tour_page', username=username))

            if not re.match(r'^\d+', price_per_person):
                flash('Значение цены должно быть в виде числа', category='error')
                logger.warning('Ошибка валидации при добавлении тура: цена не является числом')
                return redirect(url_for('add_tour_page', username=username))

            else:
                with SessionLocal() as sessionloc:
                    new_tour = TourTable(
                        title=title,
                        description=description,
                        place=place,
                        start_date_tour=start_date_tour,
                        duration=int(duration),
                        max_people=int(max_people),
                        available_places=int(available_places),
                        occupied_places=int(occupied_places),
                        price_per_person=float(price_per_person),
                        image_path=filename
                    )

                    sessionloc.add(new_tour)
                    sessionloc.commit()

                flash('Тур успешно загружен', category='success')
                logger.info('Тур "%s" успешно добавлен.', title)
                return redirect(url_for('add_tour_page', username=username))

        return render_template('admin/admin_add_tour_page.html')

    # Удалить тур
    @app.route('/up_del_tour_page/delete/<tour_id>', methods=['POST', 'GET'])
    def delete_tour(tour_id):
        """
            Обрабатывает запросы на удаление тура.

            Аргументы:
                tour_id (str): Идентификатор тура, который необходимо удалить.

            Возвращает:
                HTML: Шаблон для удаления тура или сообщение об ошибках.
            """
        if request.method == 'POST':
            with SessionLocal() as sessionloc:
                query = select(TourTable).where(TourTable.id == tour_id)
                result = sessionloc.execute(query)
                tour_model = result.scalars().first()

                if not tour_model:
                    logger.warning('Тур с ID %s не найден для удаления.', tour_id)
                    return render_template('user/empty_list_tours_page.html')

                action = request.form.get('action')
                if action == "Удалить тур":
                    delete_query = delete(TourTable).where(TourTable.id == tour_id)
                    delete_user = delete(UserTable).where(UserTable.tour_id == tour_id)
                    sessionloc.execute(delete_query)
                    sessionloc.execute(delete_user)
                    sessionloc.commit()
                    flash('Тур удален', category='success')
                    logger.info('Тур с ID %s успешно удален.', tour_id)
                    return redirect(url_for('delete_tour', tour_id=tour_id))

        return render_template('admin/admin_delete_tour_page.html')

    # Удалить пользователя
    @app.route('/clients/delete/<user_id>/<tour_id>', methods=['POST', 'GET'])
    def delete_user(user_id, tour_id):
        """
            Обрабатывает запросы на удаление пользователя из тура и обновляет кол-во мест в туре.

            Аргументы:
                user_id (str): Идентификатор пользователя, которого необходимо удалить.
                tour_id (str): Идентификатор тура, из которого необходимо удалить пользователя.

            Возвращает:
                HTML: Шаблон для удаления пользователя или сообщение об ошибках.
            """
        if request.method == 'POST':
            with SessionLocal() as sessionloc:
                query_tour = select(TourTable).where(TourTable.id == tour_id)
                result = sessionloc.execute(query_tour)
                tour_model = result.scalars().first()

                query_user = select(UserTable).where(UserTable.id == user_id)
                result = sessionloc.execute(query_user)
                user_model = result.scalars().first()

                action = request.form.get('action')
                if action == "Удалить пользователя":
                    # Обновления мест в туре после удаления пользователя
                    tour_model.available_places += user_model.number_of_people
                    tour_model.occupied_places -= user_model.number_of_people

                    delete_user = delete(UserTable).where(UserTable.id == user_id)
                    sessionloc.execute(delete_user)
                    sessionloc.commit()
                    flash('Пользователь удален', category='success')
                    logger.info(
                        'Пользователь с ID %s успешно удален из тура с ID %s.', user_id, tour_id)
                    return redirect(url_for('delete_user', user_id=user_id, tour_id=tour_id))

        return render_template('admin/admin_delete_user_page.html')
