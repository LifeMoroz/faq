from django.conf.urls import patterns, include, url
import settings
from django.contrib import admin
from questions.models import Message, QuestionsUser, AbstractVote, Question
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'questions.views.index', name='index'),
    url(r'^popular$', 'questions.views.popular'),
    url(r'^login$', 'questions.views.login'),
    url(r'^register$', 'questions.views.register'),
    url(r'^logout$', 'questions.views.logout'),
    url(r'^ask$', 'questions.views.ask'),
    url(r'^{0}/(\d+)$'.format(Question.URL_PREFIX), 'questions.views.question'),
    url(r'^{0}/(\d+)$'.format(QuestionsUser.URL_PREFIX), 'questions.views.user'),
    url(r'^{0}/(\w+)/(\w+)/(\d+)$'.format(AbstractVote.URL_PREFIX), 'questions.views.vote'),
    url(r'^{0}/(\d+)/(\w+)$'.format(Message.URL_PREFIX), 'questions.views.message'),
    url(r'^admin/', include(admin.site.urls)),
)
