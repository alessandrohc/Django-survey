from django.conf.urls.defaults import patterns, url
from django.utils.translation import ugettext_lazy as _
from django.views.generic.list_detail import object_list
from django.conf.urls.defaults import *


from models import Survey


from views import answers_list, answers_detail,\
                survey_detail, survey_edit, survey_add,\
                editable_survey_list, survey_delete, survey_update,\
                question_add, question_update,question_delete,\
                choice_add, choice_update, choice_delete,\
                visible_survey_list, \
                ajax


urlpatterns = patterns('',

    url(r'^visible/$', visible_survey_list, name='surveys-visible'),
    url(r'^editable/$', editable_survey_list, name='surveys-editable'),

    url(r'^detail/(?P<survey_slug>[-\w]+)/$', survey_detail,   name='survey-detail'),

    url(r'^answers/(?P<survey_slug>[-\w]+)/$',
        answers_list,    name='survey-results'),
    url(r'^answers/(?P<survey_slug>[-\w]+)/(?P<key>[a-fA-F0-9]{10,40})/$',
        answers_detail,  name='answers-detail'),

    url(r'^edit/(?P<survey_slug>[-\w]+)/$', survey_edit,   name='survey-edit'),
    url(r'^add/$', survey_add,   name='survey-add'),
    url(r'^update/(?P<survey_slug>[-\w]+)/$', survey_update,   name='survey-update'),
    url(r'^delete/(?P<survey_slug>[-\w]+)/$', survey_delete, name='survey-delete'),

    url(r'^question/add/(?P<survey_slug>[-\w]+)/$', question_add,   name='question-add'),
    url(r'^question/update/(?P<survey_slug>[-\w]+)/(?P<question_id>\d+)/$', question_update,   name='question-update'),
    url(r'^question/delete/(?P<survey_slug>[-\w]+)/(?P<question_id>\d+)/$', question_delete,   name='question-delete'),

    url(r'^choice/add/(?P<question_id>\d+)/$', choice_add,   name='choice-add'),
    url(r'^choice/update/(?P<question_id>\d+)/(?P<choice_id>\d+)/$', choice_update,   name='choice-update'),
    url(r'^choice/delete/(?P<survey_slug>[-\w]+)/(?P<choice_id>\d+)/$', choice_delete,   name='choice-delete'),

    url(r'^admin/$', ajax),
    
    url(r'^api/$', 'survey.api.base'),
    url(r'^api/surveys$', 'survey.api.surveys'),
    url(r'^api/surveys/(?P<survey_id>\d+)$', 'survey.api.surveys'),
    url(r'^api/surveys/(?P<survey_id>\d+).form$', 'survey.api.edit_survey'),
    
    url(r'^api/surveys/(?P<survey_id>\d+)/questions$', 'survey.api.questions'),
    url(r'^api/surveys/(?P<survey_id>\d+)/questions/(?P<question_id>\d+)$', 'survey.api.questions'),
    url(r'^api/surveys/(?P<survey_id>\d+)/recalculate_orders$', 'survey.api.question_recalculate_orders'),

    
    url(r'^api/surveys/(?P<survey_id>\d+)/questions/(?P<question_id>\d+).form$', 'survey.api.edit_question'),
    url(r'^api/surveys/(?P<survey_id>\d+)/questions/(?P<question_id>\d+)/duplicate', 'survey.api.duplicate_question'),
    url(r'^api/surveys/(?P<survey_id>\d+)/questions/(?P<question_id>\d+)/choices$', 'survey.api.choices'),
    url(r'^api/surveys/(?P<survey_id>\d+)/questions/(?P<question_id>\d+)/choices/(?P<choice_id>\d+)$', 'survey.api.choices'),
    
    url(r'^api/surveys/(?P<survey_id>\d+)/questions/(?P<question_id>\d+)/choices/recalculate_orders$', 'survey.api.choice_recalculate_orders'),

    
    )
