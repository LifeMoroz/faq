from django.conf.urls import patterns, include, url
import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'questions.views.index', name='index'),
    url(r'^popular$', 'questions.views.popular', name='popular'),
    url(r'^login$', 'questions.views.login'),
    url(r'^register$', 'questions.views.register'),
    url(r'^logout$', 'questions.views.logout'),
    url(r'^ask$', 'questions.views.ask'),
    url(r'^question/(\d+)$', 'questions.views.question'),
    url(r'^user/(\d+)$', 'questions.views.user'),
    url(r'^vote/(\w+)/(\w+)/(\d+)$', 'questions.views.vote'),
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
