from django.contrib import admin
from models import *

class QuestionsUserAdmin(admin.ModelAdmin):
    readonly_fields = ("registration_time",)

admin.site.register([Question, Answer])

admin.site.register(QuestionsUser, QuestionsUserAdmin)
# Register your models here.
