from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.http import Http404, HttpResponseForbidden, HttpResponseNotFound, HttpResponse
from questions.forms import LoginForm, Register, QuestionForm, AnswerForm
from shorthands import json
from django.template.loader import render_to_string
from django.template import RequestContext
from models import Question, QuestionsUser, Answer, Message, AbstractVote
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User

import sphinxsearch

# register notifications signals:
import notifications

def search(request, query):
    q = sphinxsearch.SphinxClient().Query(query)
    matches = q['matches']






ORDERING_RATING = '-rating'
ORDERING_TYPES = (ORDERING_RATING, )

def question_to_dic(q):
    data = {}
    data['title'] = q.title
    data['url'] = q.get_absolute_url()
    data['author'] = {'url': q.author.get_absolute_url(),
                      'username': q.author.user.username}
    data['tags'] = q.tags()
    data['rating'] = q.rating
    data['creation_time'] = q.creation_time
    data['get_vote_up_url'] = q.get_vote_up_url()
    data['get_vote_down_url'] = q.get_vote_down_url()
    data['get_vote_cancel_url'] = q.get_vote_cancel_url()

    return data


def index(request):
    """
    Index page with new questions
    """
    data = {}

    # overlay ask form
    data['questionform'] = QuestionForm()

    # get all questions
    query = Question.objects.all()
    # TODO: Raw SQL



    # paginator realization

    paginator = Paginator(query, 20)
    page_number = request.GET.get('page', '1')

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    page.object_list = map(question_to_dic, page.object_list)
    data['questions'] = page

    # active page title (for header)
    data['active'] = 'index'

    return render(request, "index.html", data)


def popular(request):
    """
    Populat questions page
    """
    data = {}

    # overlay ask form
    data['questionform'] = QuestionForm()

    ordering = ORDERING_RATING

    # get questions ordered by rating
    query = Question.objects.order_by(ordering)
    # TODO: Raw SQL

    # pagination
    paginator = Paginator(query, 20)
    page_number = request.GET.get('page', '1')

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    data['questions'] = page

    # active page title
    data['active'] = 'popular'
    return render(request, "index.html", data)


def ask(request):
    """
    Ask POST-only handler
    """
    data = {'questionform': None}

    # check if POST
    if request.method != 'POST':
        return HttpResponseForbidden()

    tag_list = request.POST.get('tags', '').split(',')

    if '' in tag_list:
        tag_list.remove('')

    form = QuestionForm(request.POST)
    data['questionform'] = form
    data['form_tags'] = tag_list

    if form.is_valid():
        user = request.user
        question_user = QuestionsUser.objects.filter(user=user)

        # check if questionsUser exists
        if len(question_user) == 0:
            return HttpResponseForbidden()

        # create new question
        title = form.cleaned_data['title']
        content = form.cleaned_data['content']

        q = Question(author=question_user[0], title=title, content=content)

        q.save()

        # adding tags after save to have id
        q.add_tags(tag_list)

        return json({'status': 'ok', 'url': q.get_absolute_url()})

    return json({'status': 'error', 'html': render_to_string("ask.html", RequestContext(request, data))})


def question(request, question_id):
    """
    Question page
    """
    data = {}

    # overlay ask form
    data['questionform'] = QuestionForm()

    # active page title
    data['active'] = 'question'

    # new answer form
    data['form'] = AnswerForm()


    # optimized question query
    q = Question.objects.filter(id=int(question_id)).select_related('author',
                                                                    'author__user', 'author__user_username',
                                                                    'author__user_id', 'answer',
                                                                    'answer__author', 'answer__author__user__username',
                                                                    'answer__author__user__id',
    )

    # check if question exists
    if len(q) == 0:
        raise Http404

    q = q[0]

    # get all answers
    query = q.answers.all().select_related('author',
                                           'author__user', 'author__user_username', 'author__user_id')

    # pagination
    paginator = Paginator(query, 30)
    page_number = request.GET.get('page', '1')

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    data['question'] = q
    data['answers'] = page

    # new answer handling
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        data['form'] = form

        if form.is_valid():
            user = request.user
            question_user = QuestionsUser.objects.filter(user=user)

            # check if user exists
            if len(question_user) == 0:
                return HttpResponseForbidden()

            # create new answer
            question_user = question_user[0]
            content = form.cleaned_data['content']
            a = Answer(author=question_user, content=content, question=q)
            a.save()

            # redirect to question page
            return redirect(q.get_absolute_url())

    return render(request, "question.html", data)


def user(request, user_id):
    """
    User page
    """

    data = {}

    # active page title
    data['active'] = 'user'

    # useer query
    u = QuestionsUser.objects.filter(id=int(user_id)).values('id', 'user__username')

    if len(u) == 0:
        raise Http404

    u = u[0]

    data['question_user'] = u

    # answers and questions
    data['questions'] = Question.objects.filter(author_id=int(user_id)).select_related()
    data['answers'] = Answer.objects.filter(author_id=int(user_id)).select_related()

    return render(request, "user.html", data)

# VOTE API CONSTANTS
# see models.AbstractVote

# VOTES API VIEW
def vote(request, vote_action, vote_model, model_id):
    """
    Api for votes and answer acceptions
    """
    if request.method != 'POST':
        return HttpResponseForbidden()

    if vote_action not in AbstractVote.ACTIONS:
        return HttpResponseNotFound()

    if vote_model not in AbstractVote.MODELS:
        return HttpResponseNotFound()

    user = request.user
    question_user = QuestionsUser.objects.filter(user=user)

    if len(question_user) == 0:
        return HttpResponseForbidden()

    question_user = question_user[0]

    model = None

    if vote_model == AbstractVote.MODEL_QUESTION:
        model = Question
    elif vote_model == AbstractVote.MODEL_ANSWER:
        model = Answer

    if not model:
        return HttpResponseNotFound()

    m = model.objects.filter(id=int(model_id))

    if len(m) == 0:
        return HttpResponseNotFound()

    m = m[0]

    data = {}
    data['action'] = 'vote'
    data['status'] = 'ok'

    if vote_action == AbstractVote.ACTION_UP:
        m.vote_up(question_user)
    elif vote_action == AbstractVote.ACTION_DOWN:
        m.vote_down(question_user)
    elif vote_action == AbstractVote.ACTION_CANCEL:
        m.cancel_vote(question_user)
    elif vote_action == AbstractVote.ACTION_ACCEPT:
        m.accept(question_user)
        data['action'] = 'accept'

    data['rating'] = m.rating

    return json(data)


def register(request):
    """
    Registration page
    """
    data = {'incorrect': False, 'disabled': False, 'noredirect': True}

    # error message
    data['messages'] = []

    if request.method == 'POST':
        form = Register(request.POST)
        email = request.POST.get('email')
        password = request.POST.get('password')
        username = request.POST.get('username')

        # Checking if email/username taken
        # TODO: Safety audit
        if User.objects.filter(email=email):
            data['incorrect'] = True
            data['messages'].append('Email %s is already taken' % email)

        if User.objects.filter(username=username):
            data['incorrect'] = True
            data['messages'].append('Username %s is already taken' % username)

        if form.is_valid():
            # check for duplicate emails
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = form.cleaned_data['username']

            if not data['incorrect']:
                user = User.objects.create_user(email=email, password=password, username=username)
                user.save()

                q_user = QuestionsUser(user=user)
                q_user.save()

                u = authenticate(username=username, password=password)
                auth_login(request, u)

                if 'redirect' in request.GET:
                    return redirect(request.GET['redirect'])
                else:
                    return redirect(index)
        else:
            data['messages'].append('Invalid input')
    else:
        form = Register()
    data['form'] = form

    return render(request, "register.html", data)


def login(request):
    """
    login page
    """
    data = {'incorrect': False, 'disabled': False,
            'active': 'login', 'noredirect': True
    }
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():

            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])

            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    return redirect(index)
                else:
                    data['disabled'] = True
            else:
                data['incorrect'] = True
    else:
        form = LoginForm()
    data['form'] = form
    return render(request, "login.html", data)


def logout(request):
    """
    Logout link handler
    """
    auth_logout(request)
    return redirect(index)


MESSAGE_ACTION_DISMISS = 'dismiss'
MESSAGE_ACTIONS = (MESSAGE_ACTION_DISMISS, )


def message(request, m_id, action):
    """
    Message api
    """
    # check method
    if request.method != 'POST':
        return HttpResponseForbidden('Only POST requests')

    # check action name
    if action not in Message.ACTIONS:
        return HttpResponseNotFound('Wrong action "%s"' % action)

    # check message existance    
    m = Message.objects.filter(id=int(m_id))
    if not m:
        return HttpResponseNotFound('Message with id=%s not found' % m_id)
    m = m[0]

    if action == Message.ACTION_DISMISS:
        m.delete()
        return json({'status': 'ok'})

    return HttpResponseNotFound('Action %s not implemented' % action)    
    
    
