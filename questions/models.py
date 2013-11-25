# coding=utf-8
from django.db import models
from django.contrib.auth.models import User


class Vote(models.Model):
    model = models.ForeignKey('Question', related_name='votes')
    author = models.ForeignKey('QuestionsUser')
    difference = models.SmallIntegerField(default=1)
    POSITIVE_IMPACT = 3
    NEGATIVE_IMPACT = -2
    
    def __unicode__(self):
        if self.difference > 0 :
            return 'positive'
        elif self.difference < 0:
            return 'negative'
        else:
            return 'neutral'


class AnswerVote(models.Model):
    model = models.ForeignKey('Answer', related_name='votes')
    author = models.ForeignKey('QuestionsUser')
    difference = models.SmallIntegerField(default=1)
    POSITIVE_IMPACT = 5
    NEGATIVE_IMPACT = -2



def _vote(model, vote_class, user, diff):
    """
    Vote method for votable objects
    TODO: move to abstract model
    """    
    
    # not allowing to rate own model
    if user == model.author:
        return
    
    # search for previous votes
    v = vote_class.objects.all().filter(author=user, model=model)
    
    # removing previous votes
    if len(v) != 0:
        v = v[0]
        # rolling back author rating
        if v.difference == 1:
            model.author.rating -= Vote.POSITIVE_IMPACT
        else:
            model.author.rating -= Vote.NEGATIVE_IMPACT
            
        # rolling back model rating
        model.rating -= v.difference   
        
        # removing vote 
        v.delete()
    
    # not creating new vote object on cancel
    if diff != 0:
        v = vote_class.objects.create(model=model, author=user, difference=diff)
        v.save()
    
    # changing question rating
    model.rating += diff
    model.save()

    # changing author rating
    if diff == 1:
        model.author.rating += vote_class.POSITIVE_IMPACT
    elif diff == -1:
        model.author.rating += vote_class.NEGATIVE_IMPACT
    model.author.save()
    

# Вопрос – заголовок, содержание, автор, дата создания
class Question(models.Model):
    title = models.CharField(max_length=256)
    author = models.ForeignKey('QuestionsUser', related_name='questions', db_index=True)
    content = models.TextField(max_length=1024)
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True)
    rating = models.IntegerField(default=0, db_index=True)
    answer = models.ForeignKey('Answer', null=True, blank=True, related_name='+')
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-creation_time', ]

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return '/question/%i' % self.id
        
    def get_vote_up_url(self):
        return '/vote/up/question/%i' % self.id
    
    def get_vote_down_url(self):
        return '/vote/down/question/%i' % self.id    
        
    def get_vote_cancel_url(self):
        return '/vote/cancel/question/%i' % self.id 
   
    def vote_up(self, user):
        return self._vote(user, 1)

    def vote_down(self, user):
        return self._vote(user, -1)

    def cancel_vote(self, user):
        return self._vote(user, 0)
        
    def _vote(self, user, diff):
        _vote(self, Vote, user, diff)
        
    def accept(self, answer, user):
        if self.author != user:
            return # TODO: Process error        
    
        if answer.question != self:
            return # TODO: Process error
        
        if self.answer:
            return # TODO: Process error
        
        answer.correct = True
        answer.save()
        self.answer = answer
        self.save()
        
        
        
# Ответ – содержание, вопрос, автор, дата написания, флаг правильного ответа.
class Answer(models.Model):
    content = models.TextField(max_length=1024)
    # https://docs.djangoproject.com/en/dev/ref/models/fields/#foreignkey
    question = models.ForeignKey('Question', related_name='answers')
    author = models.ForeignKey('QuestionsUser', related_name='answers')
    rating = models.IntegerField(default=0)
    correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['-rating']

    def __unicode__(self):
        return self.content[:80]
        
    def get_absolute_url(self):
        return self.question.get_absolute_url()

    def _vote(self, user, diff):
        _vote(self, AnswerVote, user, diff)
        
    def get_vote_up_url(self):
        return '/vote/up/answer/%i' % self.id
    
    def get_vote_down_url(self):
        return '/vote/down/answer/%i' % self.id    
        
    def get_vote_cancel_url(self):
        return '/vote/cancel/answer/%i' % self.id  
        
    def get_accept_url(self):
        return '/vote/accept/answer/%s' % self.id     
                  
    def vote_up(self, user):
        return self._vote(user, 1)

    def vote_down(self, user):
        return self._vote(user, -1)

    def cancel_vote(self, user):
        return self._vote(user, 0)
        
        
    def accept(self, user):
        return self.question.accept(self, user)

# Пользователь – электронная почта, никнейм, пароль, дата регистрации.
# никнейм, пароль, электронная почта уже являются полями
# встроенного в Django User
class QuestionsUser(models.Model):
    user = models.OneToOneField(User, db_index=True)
    registration_time = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0, db_index=True)
    
    class Meta:
        ordering = ['-registration_time']
        
    def get_absolute_url(self):
        return '/user/%i' % self.id
        
    def username(self):
        return self.user.username

    def __unicode__(self):
        return self.user.username


