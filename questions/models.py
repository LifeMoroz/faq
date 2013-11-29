# coding=utf-8
from django.db import models
from django.contrib.auth.models import User
from tagging import tags
import visits
from questions.management.commands.realtime import QUESTION_CHAN_PREF, USER_CHAN_PREF, UPDATES_TAG


def _url(*args):
    url = '/'
    return url + '/'.join(args)


class AbstractVote(models.Model):
    model = None
    URL_PREFIX = 'v'

    author = models.ForeignKey('QuestionsUser')
    difference = models.SmallIntegerField(default=1)

    POSITIVE_IMPACT = 1
    NEGATIVE_IMPACT = -1

    ACTION_UP = 'up'
    ACTION_DOWN = 'down'
    ACTION_CANCEL = 'cancel'
    ACTION_ACCEPT = 'accept'
    MODEL_QUESTION = 'q'
    MODEL_ANSWER = 'a'
    MODELS = (MODEL_QUESTION, MODEL_ANSWER)
    ACTIONS = (ACTION_UP, ACTION_DOWN, ACTION_CANCEL, ACTION_ACCEPT)

    def __unicode__(self):
        if self.difference > 0:
            return 'positive'
        elif self.difference < 0:
            return 'negative'
        else:
            return 'neutral'

    class Meta:
        abstract = True
        # slows down data generation
        # unique_together = ['author', 'model']


class AbstractRated(models.Model):

    rating = models.IntegerField(default=0, db_index=True)
    author = models.ForeignKey('QuestionsUser', db_index=True)
    vote_class = AbstractVote

    class Meta:
        abstract = True

    def vote(self, user, diff):
        """
        Vote method for votable objects
        """

        # not allowing to rate own model
        if user == self.author:
            return

        # search for previous votes
        v = self.vote_class.objects.all().filter(author_id=user.id, model_id=self.id)

        # removing previous votes
        if len(v) != 0:
            v = v[0]
            # rolling back author rating
            if v.difference == 1:
                self.author.rating -= self.vote_class.POSITIVE_IMPACT
            else:
                self.author.rating -= self.vote_class.NEGATIVE_IMPACT

            # rolling back model rating
            self.rating -= v.difference

            # removing vote 
            v.delete()

        # not creating new vote object on cancel
        if diff != 0:
            v = self.vote_class.objects.create(model=self, author=user, difference=diff)
            v.save()

        # changing question rating
        self.rating += diff
        self.save()

        # changing author rating
        if diff == 1:
            self.author.rating += self.vote_class.POSITIVE_IMPACT
        elif diff == -1:
            self.author.rating += self.vote_class.NEGATIVE_IMPACT
        self.author.save()

    def _get_vote_url(self, action):

        vote_slug = self.vote_class.URL_PREFIX
        model_slug = self.URL_PREFIX
        model_id = str(self.id)
        return _url(vote_slug, action, model_slug, model_id)

    def get_vote_up_url(self):
        return self._get_vote_url(self.vote_class.ACTION_UP)

    def get_vote_down_url(self):
        return self._get_vote_url(self.vote_class.ACTION_DOWN)

    def get_vote_cancel_url(self):
        return self._get_vote_url(self.vote_class.ACTION_CANCEL)

    def vote_up(self, user):
        return self.vote(user, 1)

    def vote_down(self, user):
        return self.vote(user, -1)

    def cancel_vote(self, user):
        return self.vote(user, 0)

    def get_absolute_url(self):
        return _url(self.URL_PREFIX, str(self.id))

    def get_accept_url(self):
        return self._get_vote_url(self.vote_class.ACTION_ACCEPT)


class Vote(AbstractVote):
    model = models.ForeignKey('Question', related_name='votes')
    POSITIVE_IMPACT = 3
    NEGATIVE_IMPACT = -2


class AnswerVote(AbstractVote):
    model = models.ForeignKey('Answer', related_name='votes')
    POSITIVE_IMPACT = 5
    NEGATIVE_IMPACT = -2


# Для системы нотификаций
class Message(models.Model):
    URL_PREFIX = 'm'
    ACTION_DISMISS = 'dismiss'
    ACTIONS = (ACTION_DISMISS, )

    class Meta:
        ordering = ['creation_time', ]

    content = models.CharField(max_length=256)
    url = models.URLField()
    user = models.ForeignKey('QuestionsUser', related_name='messages')
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True)

    def dismiss_url(self):
        return _url(self.URL_PREFIX, str(self.id), self.ACTION_DISMISS)


class Taggable(models.Model):
    URL_PREFIX = None

    class Meta:
        abstract = True

    def tags(self):
        t = tags.get_tags(self.URL_PREFIX, self.id)
        data = []
        for tag in t:
            data.append({'title': tag, 'url': _url('tag', tag)})
        return data

    def add_tag(self, tag):
        tags.add_tag(self.URL_PREFIX, self.id, tag)

    def remove_tag(self, tag):
        tags.remove_tag(self.URL_PREFIX, self.id, tag)

    def add_tags(self, tag_list):
        tags.add_tags(self.URL_PREFIX, self.id, tag_list)


# Вопрос – заголовок, содержание, автор, дата создания
class Question(AbstractRated, Taggable):
    URL_PREFIX = AbstractVote.MODEL_QUESTION
    title = models.CharField(max_length=256)
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True)
    content = models.TextField(max_length=1024)
    answer = models.ForeignKey('Answer', null=True, blank=True, related_name='+')
    views = models.PositiveIntegerField(default=0)

    vote_class = Vote

    class Meta:
        ordering = ['-creation_time', ]

    def __unicode__(self):
        return self.title

    def accept(self, answer, user_id):
        if self.author.id != user_id:
            return  # TODO: Process error

        if answer.question != self:
            return  # TODO: Process error

        if self.answer:
            return  # TODO: Process error

        answer.correct = True
        answer.save()
        self.answer = answer
        self.save()

    # канал обновлений
    def get_channel(self):
        return ':'.join([QUESTION_CHAN_PREF, str(self.id), UPDATES_TAG])

    # просмотры
    def get_visits(self):
        v = visits.get_visits(self.URL_PREFIX, self.id)
        if not v:
            v = 0
        return v

    def visit(self):
        visits.visit(self.URL_PREFIX, self.id)


# Ответ – содержание, вопрос, автор, дата написания, флаг правильного ответа.
class Answer(AbstractRated):
    URL_PREFIX = AbstractVote.MODEL_ANSWER

    vote_class = AnswerVote

    content = models.TextField(max_length=1024)
    # https://docs.djangoproject.com/en/dev/ref/models/fields/#foreignkey
    question = models.ForeignKey('Question', related_name='answers')
    correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['-rating']

    def __unicode__(self):
        return self.content[:80]

    def get_absolute_url(self):
        return self.question.get_absolute_url()

    def accept(self, user):
        return self.question.accept(self, user)


# Пользователь – электронная почта, никнейм, пароль, дата регистрации.
# никнейм, пароль, электронная почта уже являются полями
# встроенного в Django User
class QuestionsUser(models.Model):
    URL_PREFIX = 'u'

    user = models.OneToOneField(User, db_index=True)
    registration_time = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0, db_index=True)

    class Meta:
        ordering = ['-registration_time']

    def get_absolute_url(self):
        return _url(self.URL_PREFIX, str(self.id))

    def username(self):
        return self.user.username

    def __unicode__(self):
        return self.user.username

    def get_channel(self):
        return ':'.join([USER_CHAN_PREF, str(self.id), UPDATES_TAG])


class AbstractComment(models.Model):
    URL_PREFIX = 'c'

    class Meta:
        abstract = True

    user = models.OneToOneField(User, db_index=True)
    content = models.TextField(max_length=512)
    model_name = 'self'
    model = models.ForeignKey(model_name, related_name='comments')

    def __unicode__(self):
        return self.content[:80]


class QuestionComment(models.Model):
    model_name = 'Question'


class AnswerComment(models.Model):
    model_name = 'Answer'