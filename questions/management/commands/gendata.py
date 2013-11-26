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

WORDS = ['load', 'error']

def string_gen(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))
    
def text_gen(size=128):
    f = random.choice(WORDS).capitalize()
    tail = []
    tail.append(f)
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

def email_gen(size=7, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size)) + '@mail.ru'

def insert_user(cursor, id):
    password = string_gen()
    datetime = time_gen()
    is_superuser = 0
    username = string_gen(10)
    first_name = string_gen(20)
    last_name = string_gen()
    email = email_gen()
    is_staff = 0
    is_active = 1
    date_joined = time_gen()

    
def gen_user():
    password = string_gen()
    t = time_gen()
    username = string_gen(10)
    email = email_gen()
    user = User(username=username, email=email, password=password)
    user.save()
    q_user = QuestionsUser(user=user, registration_time = t)
    q_user.save()
    return q_user
    
        

def gen_question(user):
    title = text_gen(random.randint(50, 128)) + '?'
    text = text_gen(random.randint(256, 800))
    #author = randrange(1,10000)
    date = time_gen()
    #solved = random.randint(0,1)
    rate = 0
    q = Question(creation_time=date, content=text, title=title, author_id=user)
    q.save()
    return q
    
def gen_answer(question, user):
    text = text_gen(random.randint(100, 300))
    a = Answer(question_id = question, author_id = user, content = text) 
    a.save()
    return a
    
def gen_qvote(question, user):
    if random.randint(0, 1) == 0:
        Question.objects.get(id=question).vote_up(QuestionsUser.objects.get(id=user))
    else:
        Question.objects.get(id=question).vote_down(QuestionsUser.objects.get(id=user))

def gen_avote(answer, user):
    if random.randint(0, 1) == 0:
        Answer.objects.get(id=answer).vote_up(QuestionsUser.objects.get(id=user))
    else:
        Answer.objects.get(id=answer).vote_down(QuestionsUser.objects.get(id=user))
    

def insert_answer(cursor, id):
    text = string_gen(120)
    question_id = randrange(1, 100000)
    author = randrange(1, 10000)
    date = time_gen()
    is_right = random.randint(0, 10)
    if is_right == 0:
        is_right = 1
    else:
        is_right = 0
    rate = 0
    

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
            questions.append(q.id)
            if not i % (N // 10):
                self.stdout.write('Generated %s questions' % i)
                
        for i in range(100 * N):
            u = random.choice(users)
            q = random.choice(questions)
            a = gen_answer(q, u)
            if random.random() > 0.8:
                a.accept(a.question.author)
                a.save()
            answers.append(a.id)
            if not i % (N // 10):
                self.stdout.write('Generated %s answers' % i)
                
        for i in range(100 * N):
            u = random.choice(users)
            a = random.choice(answers)
            q = random.choice(questions)
            gen_qvote(q, u)
            gen_avote(a, u)

            if not i % (N // 10):
                self.stdout.write('Generated %s votes' % (i*2))           
                
               
            
        
        

