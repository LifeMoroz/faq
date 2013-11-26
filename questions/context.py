# coding=utf8
from questions.models import QuestionsUser
from django.core.cache import cache
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings

# caching key
KEY = 'global_context'

# cache ttl
TTL = 60

# number of users
N = 10


def _invalidate():
    context = {
            'project_name': 'There is no spoon',
            'last_users': QuestionsUser.objects.select_related('user').all()[:N]
    }
    cache.set(KEY, context, TTL)
    return context
    
@receiver(post_save, sender=QuestionsUser)
def _user_create_listener(sender, instance, created, **kwargs):
    if settings.DATA_GEN:
        return
    if created:
        _invalidate()     
    

def glob(request):
    
    context = cache.get(KEY)
    if context is None:  
        context = _invalidate()

    return context
