# -*- coding: utf-8 -*-
import sys
from django.core.management.base import BaseCommand, CommandError

import random
from random import randrange
import string
from time import gmtime, strftime
import datetime
from questions.models import *
from django.contrib.auth.models import User
import urllib
import tagging.tags
from django.db import connection

WORDS = ['load', 'error']


def string_gen(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


def text_gen(size=128):
    f = random.choice(WORDS).capitalize()
    tail = [f]
    n = len(f) + 1
    while n < size:
        word = random.choice(WORDS).lower()
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
    return ''.join(random.choice(chars) for x in range(size)) \
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
    q = Question(creation_time=date, content=text, title=title, author_id=user)
    q.save()
    return q


def vote_fast(model, vote_class, user_id, diff, votes):
    """
    Fast vote generation method
    """
    conn = connection.cursor()
    # mysql_query("UPDATE table SET field = field + 1 WHERE id = $number");

    # пропускаем ненужные проверочки
    # не голосуем одним юзером за одну вещь дважды
    try:
        if any(v['user_id'] == user_id
                and v['model_id'] == model['id']
                and v['table'] == model['table']
               for v in votes):
            return
    except TypeError:
        print votes
        exit(-1)
    # генерируем объект
    v = vote_class.objects.create(model_id=model['id'], author_id=user_id, difference=diff)
    v.save()

    # изменяем рейтинг модели
    conn.execute("UPDATE questions_{0} SET rating = rating + {1} WHERE id = {2}"
        .format(model['table'], diff, model['id']))
    author_diff = vote_class.POSITIVE_IMPACT
    if diff == -1:
        author_diff = vote_class.NEGATIVE_IMPACT
    conn.execute("UPDATE questions_questionsuser SET rating = rating + {1} WHERE id = {0}"
        .format(author_diff, diff))

    return {'model_id': model['id'], 'id': v.id, 'user_id': user_id, 'table': model['table']}


def gen_answer(question, user):
    text = text_gen(random.randint(100, 300))
    a = Answer(question_id=question, author_id=user, content=text)
    a.save()
    return a


def gen_qvote(question, user_id, votes):
    return vote_fast(question, Question.vote_class, user_id, random.choice([1, -1]), votes)


def gen_avote(answer, user_id, votes):
    return vote_fast(answer, Answer.vote_class, user_id, random.choice([1, -1]), votes)


class Command(BaseCommand):
    help = 'Generates testing data'

    args = '[n]'

    def handle(self, *args, **options):
        users = []
        questions = []
        answers = []

        N = 1000

        if len(args) == 1:
            N = int(args[0])

        self.stdout.write('Generationg data for %s users' % N)

        global WORDS
        WORDS = open('dict.txt').read().splitlines()

        self.stdout.write('Word dictionary: %s words' % len(WORDS))

        self.stdout.write('Flushing')
        QuestionsUser.objects.all().delete()
        Question.objects.all().delete()
        Answer.objects.all().delete()
        Vote.objects.all().delete()
        AnswerVote.objects.all().delete()

        for i in range(N):
            u = gen_user()
            users.append(u.id)
            self.stdout.write('Generated %s users' % i)

        for i in range(10 * N):
            u = random.choice(users)
            q = gen_question(u)
            questions.append({'id': q.id, 'author_id': u, 'table': 'question'})
            if not i % (N // 10):
                self.stdout.write('Generated %s questions' % i)

        for i in range(100 * N):
            u = random.choice(users)
            q = random.choice(questions)
            a = gen_answer(q['id'], u)
            if random.random() > 0.8:
                a.accept(q['author_id'])
                a.save()
            answers.append({'author_id': u, 'question': q, 'id': a.id, 'table': 'answer'})
            if not i % (N // 10):
                self.stdout.write('Generated %s answers' % i)

        for i in range(100 * N):
            q_id = random.choice(questions)['id']
            tagging.tags.add_tag(Question.URL_PREFIX, q_id, random.choice(WORDS))
            if not i % (N // 10):
                self.stdout.write('Generated %s tags' % i)

        votes = []

        for i in range(100 * N):
            u = random.choice(users)
            a = random.choice(answers)
            q = random.choice(questions)
            v = gen_qvote(q, u, votes)
            if v:
                votes.append(v)
            v = gen_avote(a, u, votes)
            if v:
                votes.append(v)

            if not i % (N // 10):
                self.stdout.write('Generated %s votes' % (i * 2))
                
               
            
        
        

