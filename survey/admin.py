# -*- coding: utf-8 -*-
from survey.models import Answer, Choice, Question, Survey
from django.contrib import admin

class ChoiceInline(admin.TabularInline):
    """
    A newforms-admin inline option class for the ``Choice`` model.
    """
    model = Choice
    extra = 4
    fields = ('text', 'order',)

class QuestionOptions(admin.ModelAdmin):
    """
    A newforms-admin options class for the ``Question`` model.
    """
    class Media:
        js = ("/static/js/control_hide.js",)
        
    list_select_related = True
    list_filter = ('survey', 'qtype')
    list_display_links = ('text',)
    
    list_display = (
        'survey', 
        'text', 
        'qtype', 
        'required'
    )
    # exclui a exibição dos seguintes campos.
    exclude = (
        'choice_num_min', 
        'choice_num_max', 
        'qstyle', 
        'order'
    )
    search_fields = ('text',)
    
    inlines = [
        ChoiceInline,
        ]

class QuestionInline(admin.TabularInline):
    """
    A newforms-admin inline option class for the ``Question`` model.
    """
    model = Question
    extra = 1
    fields = ('text', 'order',)
    template = 'admin/survey/question/edit_inline_tabular.html'

class SurveyOptions(admin.ModelAdmin):
    """
    A newforms-admin options class for the ``Survey`` model.
    """
    fields = (
        'title',
        'description',
        'opens',
        'closes',
        'visible',
        'public',
        'restricted'
    )

class AnswerOptions(admin.ModelAdmin):
    """
    A newforms-admin options class for the ``Answer`` model.
    """
    list_display = (
        'interview_uuid',
        'question', 'user', 
        'submission_date',
        'session_key', 'text'
    )
    #list_filter = ('question__survey',)
    search_fields = ('text',)
    list_select_related=True

class ChoiceOptions(admin.ModelAdmin):
    list_display = ('question','text',)
    search_fields = ('text',)
    list_filter = ('question',)

# The try/catch blocks are there to supress the ``AlreadyRegistered`` warning.
try: admin.site.register(Question, QuestionOptions)
except: pass
try: admin.site.register(Survey, SurveyOptions)
except: pass
try: admin.site.register(Answer, AnswerOptions)
except: pass
try: admin.site.register(Choice, ChoiceOptions)
except: pass
