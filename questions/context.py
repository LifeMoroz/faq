# coding=utf8
from questions.models import QuestionsUser
from django.core.cache import cache
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from questions.forms import QuestionForm

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
            'questionform': QuestionForm(),
            'project_name': 'There is no spoon',
            'last_users': QuestionsUser.objects.select_related('user').all()[:N]
    }
    
    # save to cache
    cache.set(KEY, context, TTL)
    return context
    
@receiver(post_save, sender=QuestionsUser)
def _user_create_listener(sender, instance, created, **kwargs):
    
    if settings.CACHE_INVALIDATION:
        return
    if created:
        _update()     
    

def glob(request):
    
    context = cache.get(KEY)
    if context is None:  
        context = _invalidate()

    return context
