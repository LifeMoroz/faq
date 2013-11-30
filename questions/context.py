# coding=utf8
from questions.models import QuestionsUser, Message
from django.core.cache import cache
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from questions.forms import QuestionForm
from tagging import tags
import json

# caching key
KEY = 'global_context'

# cache ttl
TTL = 60

# number of users
N = 10


def _update():
    """
    Updates global RequestContext data
    """

    context = {
        'project_name': 'There is no spoon',
        'last_users': QuestionsUser.objects.select_related('user').all()[:N]
    }

    # save to cache
    cache.set(KEY, context, TTL)
    return context


@receiver(post_save, sender=QuestionsUser)
def _user_create_listener(sender, instance, created, **kwargs):
    if not settings.CACHE_INVALIDATION:
        return
    if created:
        _update()


def glob(request):
    context = cache.get(KEY)
    if context is None:
        context = _update()

    context['tags_top'] = tags.get_top()
    try:
        user = request.user
    except AttributeError:
        return context
    question_user = QuestionsUser.objects.filter(user_id=user.id)

    # check if questionsUser exists
    if len(question_user) == 1:
        u = question_user[0]
        m = Message.objects.filter(user_id=u.id)
        context['messages'] = m
        context['self_user'] = question_user[0]

    context['tags_top'] = tags.get_top()

    return context
