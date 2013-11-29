# coding=utf-8
import json
from redis_cache import get_redis_connection
from models import Answer, QuestionsUser, Message

# обработка событий
from django.dispatch import receiver
from django.db.models.signals import post_save

# константы рилтайма
from questions.management.commands.realtime import QUESTION_CHAN_PREF, USER_CHAN_PREF, UPDATES_TAG

# отправка сообщеий
from django.core.mail import send_mail

# настройки
from django.conf import settings


def _notify(url, title, author_id, autor_email, question_id):
    """
    Create new Message and publish it
    """
    # соединение с redis
    r = get_redis_connection()

    # разные сообщени автору и тем, кто на странице вопроса
    text_author = 'Your question "%s" has new answer!' % title
    text_other = 'Question %s has new answer!' % title

    # создание сообщения для оффлайн-нотификаций
    # проверка на то, что уже есть такое сообщение
    previous = Message.objects.filter(url=url)
    if not previous:
        m = Message(url=url, content=text_author, user_id=author_id)
        m.save()
        dismiss_url = m.dismiss_url()
    else:
        dismiss_url = previous[0].dismiss_url()

    # дамп в json
    data_author = {'content': text_author, 'url': url, 'dismiss_url': dismiss_url}
    data_other = {'content': text_other, 'url': url, 'dismiss_url': dismiss_url}
    data_author_json = json.dumps(data_author)
    data_other_json = json.dumps(data_other)

    r.publish('{0}:{1}:{2}'.format(QUESTION_CHAN_PREF, question_id, UPDATES_TAG), data_other_json)
    r.publish('{0}:{1}:{2}'.format(USER_CHAN_PREF, author_id, UPDATES_TAG), data_author_json)

    # проверка на тестовый имейл
    if 'testnoemails' in autor_email:
        return

    # подготовка данных для имейла
    email_message = text_author + '\n %s' % settings.EMAIL_LINKS_BASE + url
    email_subject = 'You have new answer!'
    email_from = settings.EMAIL_FROM

    # отправка имейла
    send_mail(email_subject, email_message, email_from, [autor_email, ])


@receiver(post_save, sender=Answer)
def _answer_create_listener(sender, instance, created, **kwargs):
    if not settings.CACHE_INVALIDATION:
        return

    if created:
        _notify(instance.get_absolute_url(),
                instance.question.title,
                instance.question.author.id,
                instance.question.author.user.email,
                instance.question.id)
