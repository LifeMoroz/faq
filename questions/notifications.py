import redis
from models import Answer, QuestionsUser, Message
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
import json

r = redis.StrictRedis(host='127.0.0.1')

def _notify(url, title, author_id, question_id):
    """
    Create new Message and publish it
    """
    text = 'Your question "%s" has new answer!' % title
    data = {'content': text, 'url': url}
    data_json = json.dumps(data)
    r.publish('question:{0}:updates'.format(question_id), data_json)
    r.publish('user:{0}:updates'.format(author_id), data_json)
    m = Message(url=url, content=text, user_id=author_id)
    m.save()

@receiver(post_save, sender=Answer)
def _answer_create_listener(sender, instance, created, **kwargs):
    
    if not settings.CACHE_INVALIDATION:
        return
        
    if created:
        _notify(instance.get_absolute_url(),
            instance.question.title,
            instance.question.author.id, instance.question.id)
