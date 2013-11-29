# -*- coding: utf-8 -*-
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

words = ['load', 'error']


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
                   .format(Answer._meta.db_table, question, user, text))
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
        self.log_rate = 100
        super(Command, self).__init__()

    def generate(self, count, generator, name, *args, **kwargs):
        start = time.time()
        op_start = time.time()
        self.stdout.write('Generating {0:>5} {1:<15}'.format(count, name))
        for i in range(count):
            generator(*args, **kwargs)
            if not i % self.log_rate and i != 0:
                elapsed = time.time() - start
                start = time.time()
                self.stdout.write('Generated {0:>6} {1:<15} {2:.2f} op/s'.format(i, name, self.log_rate / elapsed))

                if not i % (self.log_rate * 10):
                    self.stdout.write('{0:>3}% ETA: {1:.2f} s'
                        .format((100. * i / count), (count - i) / (self.log_rate / elapsed)))

        elapsed = time.time() - op_start
        self.stdout.write('Generated {0:>6} {1:<15} {2:.2f} op/sec'.format(count, name, count / elapsed))

    def handle(self, *args, **options):
        users = []
        questions = []
        answers = []
        a_votes = []
        q_votes = []
        user_count = 1000

        if len(args) == 1:
            user_count = int(args[0])

        global words
        words = open('dict.txt').read().splitlines(False)

        user = settings.DATABASES['default']['USER']
        password = settings.DATABASES['default']['PASSWORD']
        db = settings.DATABASES['default']['NAME']
        connection = mysqldb.connect(user=user, passwd=password, db=db)

        self.stdout.write('Word dictionary: %s words' % len(words))
        self.stdout.write('Removing...')

        QuestionsUser.objects.all().delete()
        self.stdout.write('Removed users')
        Question.objects.all().delete()
        self.stdout.write('Removed questions')
        Answer.objects.all().delete()
        self.stdout.write('Removed answers')
        Vote.objects.all().delete()
        self.stdout.write('Removed votes')
        AnswerVote.objects.all().delete()
        self.stdout.write('Removed answers')
        Message.objects.all().delete()
        c = redis.StrictRedis()
        c.flushdb()
        self.stdout.write('Removed tags and notifications')

        # рассчет количества элементов
        question_count = user_count * 10
        answer_count = question_count * 10
        tag_count = 120
        likes_count = answer_count * 2
        votes_questions = int((1. * question_count / (question_count + answer_count)) * likes_count)
        votes_answers = int((1. * answer_count / (question_count + answer_count)) * likes_count)
        tag_linked = likes_count
        comment_count = answer_count

        # список тегов
        tag_list = random.sample(words, tag_count)

        # вывод на экран количество элементов
        self.stdout.write('Data generation:')
        for k, v in [('users', user_count),
                     ('questions', question_count),
                     ('answers', answer_count),
                     ('tags', tag_count),
                     ('votes', likes_count),
                     ('comments', comment_count)]:
            self.stdout.write('{0:<10} = {1:>10}'.format(k, v))

        time.sleep(1.5)

        # генерация данных
        self.generate(user_count, user_generator, 'users', users)
        self.generate(question_count, questions_generator, 'questions',  users, questions)
        self.generate(answer_count, answers_generator, 'answers', connection, users, questions, answers)
        self.generate(tag_linked, tag_generator, 'tags', questions, tag_list)
        self.generate(votes_questions, votesq_generator, 'questions votes', connection, users, questions, q_votes)
        self.generate(votes_answers, votesa_generator, 'answers votes', connection, users, answers, a_votes)

        self.stdout.write('OK')

               
            
        
        

