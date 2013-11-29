# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import time
from questions.models import *
from django.db import connection


def vote_fast(conn, model, vote_class):
    """
    Fast vote recalculation
    """

    diff = model['difference']
    conn.execute("UPDATE questions_{0} SET rating = rating + {1} WHERE id = {2}"
        .format(model['table'], diff, model['id']))

    author_diff = vote_class.POSITIVE_IMPACT
    if diff == -1:
        author_diff = vote_class.NEGATIVE_IMPACT

    conn.execute("UPDATE questions_questionsuser SET rating = rating + {1} WHERE id = {0}"
        .format(model['author_id'], author_diff))


class Command(BaseCommand):
    help = 'Generates testing data'

    def __init__(self):
        self.log_rate = 100
        super(Command, self).__init__()

    def handle(self, *args, **options):

        self.stdout.write('Resetting rating')
        conn = connection.cursor()
        conn.execute('UPDATE questions_question SET rating = 0')
        conn.execute('UPDATE questions_answer SET rating = 0')
        conn.execute('UPDATE questions_questionsuser SET rating = 0')
        self.stdout.write('Recalculation rating')

        i = 0
        start = time.time()
        for v in Vote.objects.all():
            m = {'table': 'question', 'id': v.id, 'author_id': v.author_id, 'difference': v.difference}
            vote_fast(conn, m, Vote)
            i += 1
            if not i % self.log_rate and i != 0:
                elapsed = time.time() - start
                start = time.time()
                self.stdout.write('Recalculated {0:>6} {1:<15} {2:.2f} op/s'.format(i, 'votes', self.log_rate / elapsed))

        for v in AnswerVote.objects.all():
            m = {'table': 'answer', 'id': v.id, 'author_id': v.author_id, 'difference': v.difference}
            vote_fast(conn, m, Vote)
            if not i % self.log_rate and i != 0:
                elapsed = time.time() - start
                start = time.time()
                self.stdout.write('Recalculated {0:>6} {1:<15} {2:.2f} op/s'
                    .format(i, 'votes', self.log_rate / elapsed))

        self.stdout.write('OK')

