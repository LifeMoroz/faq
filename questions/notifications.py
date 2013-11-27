from redis_cache import get_redis_connection
from models import Answer, QuestionsUser, Message
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
import json
from questions.management.commands.realtime import QUESTION_CHAN_PREF, USER_CHAN_PREF, UPDATES_TAG


def _notify(url, title, author_id, question_id):
    """
    Create new Message and publish it
    """
    r = get_redis_connection()
    text = 'Your question "%s" has new answer!' % title

    m = Message(url=url, content=text, user_id=author_id)
    m.save()

    data = {'content': m.content, 'url': m.url, 'dismiss_url': m.dismiss_url()}
    data_json = json.dumps(data)

    r.publish('{0}:{1}:{2}'.format(QUESTION_CHAN_PREF, question_id, UPDATES_TAG), data_json)
    r.publish('{0}:{1}:{2}'.format(USER_CHAN_PREF, author_id, UPDATES_TAG), data_json)

@receiver(post_save, sender=Answer)
def _answer_create_listener(sender, instance, created, **kwargs):
    if not settings.CACHE_INVALIDATION:
        return

    if created:
        _notify(instance.get_absolute_url(),
                instance.question.title,
                instance.question.author.id, instance.question.id)
