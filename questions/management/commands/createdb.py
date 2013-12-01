# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import time
from questions.models import *
import MySQLdb as mysqldb
from django.conf import settings


class Command(BaseCommand):
    help = 'Creates db'

    def __init__(self):
        self.log_rate = 100
        super(Command, self).__init__()

    def handle(self, *args, **options):

        # загружаем настройки БД
        user = settings.DATABASES['default']['USER']
        password = settings.DATABASES['default']['PASSWORD']
        db = settings.DATABASES['default']['NAME']

        self.stdout.write(u'Создание БД')
        connection = None

        try:
            connection = mysqldb.connect(user=user, passwd=password)
        except (mysqldb.OperationalError, mysqldb.ProgrammingError) as e:
            self.stderr.write(u'Ошибка подключения к БД: %s' % e[1])
            exit(-1)

        conn = connection.cursor()

        try:
            conn.execute('CREATE DATABASE {0} CHARACTER SET utf8'.format(db))
            self.stdout.write(u'База данных создана')
        except mysqldb.OperationalError as e:
            # что-то пошло не так
            self.stderr.write(u'Ошибка создания БД: %s' % e[1])
            return
        except mysqldb.ProgrammingError as e:
            self.stderr.write(u'Ошибка создания БД: %s' % e[1])
            if e[0] == 1007:
                self.stderr.write(u'База данных уже существует')
                while True:
                    self.stdout.write(u'Удалить базу данных? (y/N) ', ending='')
                    try:
                        answer = raw_input().lower()
                    except KeyboardInterrupt:
                        answer = 'n'
                    if answer == 'y':
                        conn.execute('DROP DATABASE {0}'.format(db))
                        self.stdout.write(u'База данных удалена')
                        conn.execute('CREATE DATABASE {0} CHARACTER SET utf8'.format(db))
                        self.stdout.write(u'База данных создана')
                        break
                    if answer == '' or answer == 'n':
                        self.stdout.write(u'База данных НЕ будет удалена')
                        return
                    self.stderr.write(u'Пожалуйста, введите y или n')
            else:
                return
        self.stdout.write('OK')

