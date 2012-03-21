# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin
from django.contrib.auth.views import login, logout, password_change
from django.views.generic.simple import direct_to_template
from django.conf import settings
# survey imports
from survey.urls import redirect_start
import survey.views

admin.autodiscover()

# redirecionamento de survey para a página inicial
urlpatterns = redirect_start()

urlpatterns += patterns('',
    # Admin
    url(r'^admin/', include(admin.site.urls)),
    (r'^grappelli/', include('grappelli.urls')),
    
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', 
     {'document_root': settings.MEDIA_ROOT}),
    
    url(r'^login/$', login,
        {'template_name':'admin/login.html'},name='auth_login'),
    
    url(r'^logout/$', logout,
        {'template_name':'registration/logged_out.html'},name='auth_logout'),
    
    url(r'^password_change/$', password_change,
        {'template_name':'admin/password_change.html'},name='auth_password_change'),
)
