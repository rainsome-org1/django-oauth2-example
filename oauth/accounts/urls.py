from django.conf.urls import patterns, url

from django.views.generic import TemplateView

urlpatterns = patterns('django.contrib.auth.views',
    url(r'^login/$', 'login', kwargs={'template_name': 'accounts/login.html'},
        name='accounts_log_in'),
    url(r'^logout/$', 'logout', kwargs={'next_page': '/'},
        name='accounts_log_out'),
    url(r'^profile/$', TemplateView.as_view(template_name='accounts/profile.html')),
)
