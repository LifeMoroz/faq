# -*- coding: utf-8 -*-
import os
import random
import string
import time
from time import gmtime, strftime
import MySQLdb as mysqldb
import redis

from django.core.management.base import BaseCommand
from django.conf import settings
from questions.models import *
from django.contrib.auth.models import User
import tagging.tags
import questions.visits as visits


# TODO: убрать из глобальных переменных
words = []


def string_gen(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def text_gen(size=128):
    f = random.choice(words).capitalize()
    tail = [f]
    n = len(f) + 1
    while n < size:
        word = random.choice(words).lower()
        if (n + len(word)) > size:
            break
        tail.append(word)
        n += len(word) + 1
    return ' '.join(tail)


def time_gen():
    t = gmtime()
    result = strftime('%Y-%m-%d %H:%M:%S', t)
    return result


def email_gen(size=7, chars=string.ascii_lowercase + string.digits + '_'):
    return 'testnoemails_' + ''.join(random.choice(chars) for x in range(size)) \
           + '@%s' % random.choice(['mail.ru', 'yandex.ru', 'gmail.com',
                                    'yahoo.com', 'bk.ru', 'ya.ru'])


def gen_user():
    password = string_gen()
    t = time_gen()
    username = string_gen(10)
    email = email_gen()
    user = User(username=username, email=email, password=password)
    user.save()
    q_user = QuestionsUser(user=user, registration_time=t)
    q_user.save()
    return q_user


def gen_question(user):
    title = text_gen(random.randint(50, 128)) + '?'
    text = text_gen(random.randint(256, 800))
    date = time_gen()
    views = random.randint(0, 1000)
    q = Question(creation_time=date, content=text, title=title, author_id=user)
    q.save()
    visits.set_visits(Question.URL_PREFIX, q.id, views)
    return q


def accept_fast(conn, answer_id, question_id, answered_questions):
    if question_id in answered_questions:
        return

    cursor = conn.cursor()
    cursor.execute("UPDATE questions_answer SET correct = true WHERE id = '{0}'".format(answer_id))
    cursor.execute("UPDATE questions_question SET answer_id = {0} WHERE id = '{1}'".format(answer_id, question_id))
    answered_questions.append(question_id)


def vote_fast(conn, model, vote_class, user_id, diff, votes):
    """
    Fast vote generation method
    """

    cursor = conn.cursor()

    # пропускаем ненужные проверочки
    # не голосуем одним юзером за одну вещь дважды

    # вот эта проверка может тормозить
    # TODO: optimize
    if any(v['user_id'] == user_id
           and v['model_id'] == model['id']
           for v in votes):
        return

    # генерируем объект
    # v = vote_class.objects.create(model_id=model['id'], author_id=user_id, difference=diff)
    # v.save()

    cursor.execute("INSERT INTO {0} (model_id, author_id, difference) VALUES ({1}, {2}, {3})"
                   .format(vote_class._meta.db_table, model['id'], user_id, diff))
    v_id = conn.insert_id()

    # изменяем рейтинг модели
    cursor.execute("UPDATE questions_{0} SET rating = rating + {1} WHERE id = {2}"
                   .format(model['table'], diff, model['id']))
    author_diff = vote_class.POSITIVE_IMPACT
    if diff == -1:
        author_diff = vote_class.NEGATIVE_IMPACT
    cursor.execute("UPDATE questions_questionsuser SET rating = rating + {1} WHERE id = {0}"
                   .format(model['author_id'], author_diff))

    return {'model_id': model['id'], 'id': v_id, 'user_id': user_id}


def gen_answer(conn, question, user):
    cursor = conn.cursor()
    text = text_gen(random.randint(100, 300))
    # a = Answer(question_id=question, author_id=user, content=text)
    # a.save()
    cursor.execute("INSERT INTO {0} (question_id, author_id, content, correct, rating) "
                   "VALUES ('{1}', '{2}', '{3}', false, 0)"
                   .format('questions_answer', question, user, text))
    a_id = conn.insert_id()
    return a_id


def gen_qvote(conn, question, user_id, votes):
    return vote_fast(conn, question, Question.vote_class, user_id, random.choice([1, -1]), votes)


def gen_avote(conn, answer, user_id, votes):
    return vote_fast(conn, answer, Answer.vote_class, user_id, random.choice([1, -1]), votes)


def user_generator(users):
    u = gen_user()
    users.append(u.id)


def questions_generator(users, questions):
    u = random.choice(users)
    q = gen_question(u)
    questions.append({'id': q.id, 'author_id': u, 'table': 'question'})


def answers_generator(conn, users, questions, answers):
    answered_questions = []
    u = random.choice(users)
    q = random.choice(questions)
    a_id = gen_answer(conn, q['id'], u)

    if random.random() > 0.8:
        accept_fast(conn, a_id, q['id'], answered_questions)

    answers.append({'author_id': u, 'question': q, 'id': a_id, 'table': 'answer'})


def tag_generator(questions, all_tags):
    q_id = random.choice(questions)['id']
    tagging.tags.add_tag(Question.URL_PREFIX, q_id, random.choice(all_tags))


def votesa_generator(conn, users, answers, votes):
    u = random.choice(users)
    a = random.choice(answers)
    v = gen_avote(conn, a, u, votes)
    if v:
        votes.append(v)


def votesq_generator(conn, users, questions, votes):
    u = random.choice(users)
    q = random.choice(questions)
    v = gen_qvote(conn, q, u, votes)
    if v:
        votes.append(v)


class Command(BaseCommand):
    help = 'Generates testing data'

    args = '[n]'

    def __init__(self):
        # разница в секундах между отображением прогресса
        self.log_rate = 0.7
        super(Command, self).__init__()

    def clear(self, connection):
        try:
            self._clear(connection)
        except (mysqldb.OperationalError, mysqldb.ProgrammingError) as e:
            self.stderr.write(u'Ошибка БД: %s' % e[1])
            if e[0] == 1146:
                self.stderr.write(u'Таблица не найдена. Попробуйте python manage.py syncdb')
            exit(-1)

    def _clear(self, connection):
        """
        Очистка базы данных
        @param connection: соединение с БД
        """

        cursor = connection.cursor()
        self.stdout.write(u'Очистка БД...')

        # убираем проверку на внешние ключи
        # чтобы можно было все удалить
        cursor.execute('SET FOREIGN_KEY_CHECKS=0')

        cursor.execute('TRUNCATE TABLE questions_questionsuser')
        # QuestionsUser.objects.all().delete()
        self.stdout.write(u'Юзеры удалены')

        cursor.execute('TRUNCATE TABLE questions_question')
        # Question.objects.all().delete()
        self.stdout.write(u'Вопросы удалены')

        cursor.execute('TRUNCATE TABLE questions_answer')
        # Answer.objects.all().delete()
        self.stdout.write(u'Ответы удалены')

        # Vote.objects.all().delete()
        cursor.execute('TRUNCATE TABLE questions_vote')
        # AnswerVote.objects.all().delete()
        cursor.execute('TRUNCATE TABLE questions_answervote')
        self.stdout.write(u'Лайки удалены')

        #Message.objects.all().delete()
        cursor.execute('TRUNCATE TABLE questions_message')
        self.stdout.write(u'Сообщения удалены')

        # возвращаем проверку
        # (если не возвратим, то останется до конца соединения)
        cursor.execute('SET FOREIGN_KEY_CHECKS=1')

        # удаляем все из редиски
        c = redis.StrictRedis()
        c.flushdb()
        self.stdout.write(u'Риалтайм-нотификации и теги удалены')

        self.stdout.write(u'Удаление успешно завершено')

    def generate(self, count, generator, name, *args, **kwargs):
        """
        Обертка над генераторами данных с удобным логом прогресса
        @param count: количество элементов
        @param generator: генератор
        @param name: имя элемента (множ. число)
        @param args: аргументы генератора
        @param kwargs: key-аргументы генератора
        """
        last_time = time.time()
        start_i = 0     # количество обработанных элементов
        start_time = time.time()
        self.stdout.write(u'Генерация      {0:>5} {1:<16}'.format(count, name))
        for i in range(count):
            # генерируем что-то, передавая параметры в генератор
            generator(*args, **kwargs)
            # время с последнего лога
            elapsed = time.time() - last_time

            # выводим лог если прошло достаточно времени
            if elapsed > self.log_rate:
                # количество обработанных элементов с последнего раза
                processed = i - start_i

                # обновляем счетчики времени и кол-ва
                start_i = i
                last_time = time.time()
                from_start = last_time - start_time
                speed = processed / elapsed
                speed_from_start = (count - i) / (i / from_start)
                completed_percentage = (100. * i / count)

                self.stdout.write(u'Сгенерировано {0:>6} {1:<16}'
                                  u' {2:.2f} в секудну'.format(i, name, speed))
                self.stdout.write('{0:>3.0f}% ETA: {1:.2f} s'
                    .format(completed_percentage, speed_from_start))

        # полное время выполнения
        elapsed = time.time() - start_time
        speed = count / elapsed
        self.stdout.write(u'Сгенерировано {0:>6} {1:<16} {2:.2f} в секудну'
            .format(count, name, speed))

    def handle(self, *args, **options):
        users = []      # список id-шников пользователей
        questions = []  # список вопросов
        answers = []    # список для ответов
        a_votes = []    # лайки ответов
        q_votes = []    # лайки вопросов
        user_count = 1000

        if len(args) == 1:
            user_count = int(args[0])

        # проверка настроек
        # в режиме отладки ORM сжирает много памяти
        if settings.DEBUG:
            self.stderr.write(u'В режиме отладки низкая производительность. Установите settings.DEBUG = False')
            return

        # а эта штука вообще создаст кучу ненужных сообщений
        if settings.CACHE_INVALIDATION:
            self.stderr.write(u'Ивалидация кеша и нотификации включены. \n'
                              u'Установите settings.CACHE_INVALIDATION = False')
            return

        # загрузка словаря
        global words

        base_dir = os.path.dirname(os.path.abspath(__file__))
        # словарь хранится в папке data
        dict_path = os.path.join(base_dir, 'data', 'dict.txt')

        # проверим, вдруг кто его удалил
        try:
            words_file = open(dict_path)
            words = words_file.read().splitlines(False)
        except IOError:
            words = []

        if not words:
            self.stderr.write(u'Словарь не найден в %s' % dict_path)
            return

        # загружаем настройки БД
        user = settings.DATABASES['default']['USER']
        password = settings.DATABASES['default']['PASSWORD']
        db = settings.DATABASES['default']['NAME']

        # попытка коннекта к БД
        try:
            connection = mysqldb.connect(user=user, passwd=password,
                                         db=db)
        except mysqldb.OperationalError as e:
            # что-то пошло не так
            self.stderr.write(u'Невозможно подключиться к БД: %s' % e[1])

            # а тут мы точно знаем, что БД не существует
            if e[0] == 1049:
                self.stderr.write(u'База данных не существует')
            return

        self.stdout.write(u'Слов в словаре: %s' % len(words))

        # рассчет количества элементов
        question_count = user_count * 10
        answer_count = question_count * 10
        tag_count = 120
        likes_count = answer_count * 2

        # распределяем лайки пропорционально количеству
        # ответов и вопросов соответственно
        votes_questions = int((1. * question_count / (question_count + answer_count)) * likes_count)
        votes_answers = int((1. * answer_count / (question_count + answer_count)) * likes_count)

        tag_linked = likes_count
        comment_count = answer_count

        # список тегов
        # берем рандомные слова из словаря
        tag_list = random.sample(words, tag_count)

        # вывод на экран количество элементов
        self.stdout.write(u'Будет сгенерировано:')
        for k, v in [(u'пользователей', user_count),
                     (u'вопросов', question_count),
                     (u'ответов', answer_count),
                     (u'связей тегов', tag_linked),
                     (u'лайков', likes_count),
                     (u'комментов', comment_count)]:
            self.stdout.write(u'{0:<15} = {1:>8}'.format(k, v))

        # позволяем нам проверить, все ли ок
        try:
            self.stdout.write(u'Нажмите Ctrl+C для отмены')
            time.sleep(2)
        except KeyboardInterrupt:
            self.stdout.write(u'Генерация тестовых данных отменена')
            self.stdout.write('OK')
            return

        # очистка
        self.clear(connection)

        # генерация данных
        try:
            self.generate(user_count, user_generator, u'пользователей', users)
            self.generate(question_count, questions_generator, u'вопросов',  users, questions)
            self.generate(answer_count, answers_generator, u'ответов', connection, users, questions, answers)
            connection.commit()
            self.generate(tag_linked, tag_generator, u'тегов', questions, tag_list)
            self.generate(votes_questions, votesq_generator, u'лайков вопросов', connection, users, questions, q_votes)
            self.generate(votes_answers, votesa_generator, u'лайков ответов', connection, users, answers, a_votes)
            connection.commit()
        except KeyboardInterrupt:
            # генерация прервана с клавиатуры
            # очищаем базу данных
            self.stderr.write(u'Генерация тестовых данных прервана. Очистка БД')
            self.clear(connection)
        except (mysqldb.OperationalError, mysqldb.ProgrammingError) as e:
            self.stderr.write(u'Ошибка БД: %s' % e)
            if e[0] == 1146:
                self.stderr.write(u'Таблица не найдена. Попробуйте python manage.py syncdb')
        else:
            self.stdout.write('OK')
        finally:
            connection.close()
