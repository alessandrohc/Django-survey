# -*- coding: utf-8 -*-
"""Survey Models
"""
import datetime

from django.db import models
from django.conf import settings
from django.core.cache import cache
from django.utils import encoding
from django.template.defaultfilters import date as datefilter
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

QTYPE_CHOICES = (
    ('T', _('Text')),
    ('A', _('Texto grande')),
    ('i', _('Numbers')),
    ('S', _(u'Lista de opções')),
    ('R', _(u'Botões de radio')),
    ('C', _(u'Botões de caixa de marcação'))
)
##########################################################################
class SurveyManager(models.Manager):

    def surveys_for(self, recipient):
        recipient_type = ContentType.objects.get_for_model(recipient)
        return Survey.objects.filter(visible=True,recipient_type=recipient_type, recipient_id=recipient.id)

##########################################################################
class Survey(models.Model):
    title = models.CharField(_('title'), max_length=255, unique=True)
    slug  = models.SlugField(_('slug'), max_length=255, blank=True)
    
    description= models.TextField(
        verbose_name=_("description"),
        help_text=_("This field appears on the public web site and should give an overview to the interviewee"),
        blank=True
    )
    ## Add validation on datetimes
    opens   = models.DateTimeField(_('date publish'))
    closes  = models.DateTimeField(_(u'data de término'))
    # Define the behavior of the survey
    visible = models.BooleanField(_('active'))
    public  = models.BooleanField(_('show results at end of the survey'))
    
    # Usado para restringir pesquisas a usuários com login e senha no sistema
    restricted = models.BooleanField(
        verbose_name=_(u"Somente usuários autenticados"), blank=True, default=False)
    
    allows_multiple_interviews = models.BooleanField(
        verbose_name=_("allows multiple interviews"), blank=True, default=False)
    
    template_name = models.CharField(_('template name'), 
        max_length=150, null=True, blank=True,
        help_text=_("This field is used to define a custom template (Example: 'dj_survey/template/my_add_interview_forms.html')."))
    
    # Control who can edit the survey
    # TODO: Plug this control in the view used to edit the survey
    created_by = models.ForeignKey(User, related_name="created_surveys",null=True)
    editable_by = models.ForeignKey(User, related_name="owned_surveys",null=True)

    # Integration in Pinax
    recipient_type = models.ForeignKey(ContentType,null=True)
    recipient_id = models.PositiveIntegerField(null=True)
    recipient = generic.GenericForeignKey('recipient_type', 'recipient_id')

    objects = SurveyManager()

    @property
    def _cache_name(self):
        if not self.id:
            id = 'new'
        else:
            id = int(self.id)
        return 'survey_' + repr(id) + '_status'

    @property
    def open(self):
        if not self.visible: return False
        value = cache.get(self._cache_name)
        if value is not None: return value
        now = datetime.datetime.now()
        if self.opens >= now:
            value = False
            duration = (now - self.opens).seconds
        elif self.closes >= now:
            value = True
            duration = (self.opens - now).seconds
        else:
            value = False
            duration = 60*60*24*31
        if duration:
            cache.set(self._cache_name, value, duration)
        return value

    @property
    def closed(self):
        return not self.open

    @property
    def status(self):
        if not self.visible: return _('private')
        if self.open: return _('open')
        if datetime.datetime.now() < self.opens:
            return unicode(_('opens ')) + datefilter(self.opens)
        return _('closed')

    @property
    def answer_count(self):
        if hasattr(self, '_answer_count'):
            return self._answer_count
        self._answer_count = sum(q.answer_count for q in self.questions.iterator())
        return self._answer_count

    @property
    def interview_count(self):
        # NOTSURE: Do we realy need this optimisation?
        if hasattr(self, '_interview_count'):
            return self._interview_count
        self._interview_count = len(Answer.objects.filter(
            question__survey=self.id).values('interview_uuid').distinct())
        return self._interview_count

    @property
    def session_key_count(self):
        # NOTSURE: Do we realy need this optimisation?
        if hasattr(self, '_session_key_count'):
            return self._submission_count
        self._submission_count = len(Answer.objects.filter(
            question__survey=self.id).values('session_key').distinct())
        return self._submission_count


    def has_answers_from(self, session_key):
        return bool(
            Answer.objects.filter(session_key__exact=session_key.lower(),
            question__survey__id__exact=self.id).distinct().count())

    def has_answers_from_user(self, user):
        """Find if a User has already awsered to survey
        """
        return bool(
            Answer.objects.filter(user=user,
            question__survey__id__exact=self.id).distinct().count())

    def __unicode__(self):
        return u' - '.join([self.slug, self.title])

    @models.permalink
    def get_absolute_url(self):
        return ('survey-detail', (), {'survey_id': self.id})
    
    def save(self):
        res = super(Survey, self).save()
        cache.delete(self._cache_name)
        return res

    def answers_viewable_by(self, user):
        if not self.visible: return False
        if self.public: return True
        if user.is_anonymous(): return False
        return user.has_perm('survey.view_answers')
    
    class Meta:
        verbose_name        = _("Pesquisa")
        verbose_name_plural = _("Pesquisas")

##########################################################################
class Question(models.Model):
    survey = models.ForeignKey(Survey, related_name='questions', verbose_name=_('survey'))
    
    text = models.TextField(_('question text'))
    
    qtype = models.CharField(_('formato de resposta'), max_length=2, choices=QTYPE_CHOICES, default='T')
    required = models.BooleanField(_('required'), default=True)
    
    order = models.IntegerField(verbose_name = _("order"), null=True, blank=True)
    
    # Define if the user must select at least 'choice_num_min' number of
    # choices and at most 'choice_num_max'
    choice_num_min = models.IntegerField(_("minimum number of choices"), null=True, blank=True,)
    choice_num_max = models.IntegerField(_("maximum number of choices"), null=True, blank=True,)
    
    # TODO: Modify the forms to respect the style defined by this attr (html,css)
    qstyle = models.TextField(_("Html Style"),null=True, blank=True)
    ## model validation for requiring choices.

    @property
    def answer_count(self):
        if hasattr(self, '_answer_count'):
            return self._answer_count
        self._answer_count = self.answers.count()
        return self._answer_count

    def duplicate(self):
        new_question = Question(survey=self.survey,
                                qtype=self.qtype,
                                required=self.required,
                                text=self.text,
                                order=self.order,
                                qstyle=self.qstyle)
        new_question.save()
        choices = Choice.objects.filter(question=self)
        for choice in choices:
            new_choice = Choice(question=new_question,
                                text=choice.text,
                                order=choice.order)
            new_choice.save()

    def __unicode__(self):
        return u' - '.join([self.survey.slug, self.text])

    class Meta:
        # http://code.google.com/p/django-survey/issues/detail?id=24
        # unique_together = (('survey', 'text'),)
        order_with_respect_to='survey'
        ordering = ('survey', 'order')
        verbose_name        = _("Pergunta")
        verbose_name_plural = _("Perguntas")
        
    class Admin:
        list_select_related = True
        list_filter = ('survey', 'qtype')
        list_display_links = ('text',)
        list_display = ('survey', 'text', 'qtype', 'required')
        search_fields = ('text',)
        
    @models.permalink
    def get_absolute_url(self):
        return ('survey-detail', (), {'survey_id': self.survey.id})
    
    @models.permalink
    def get_update_url(self):
        return ('question-update', (), {'survey_id': self.survey.id, 'question_id': self.id} )

    # TODO: add this a fallback to this optimisation with django ORM.
    @property
    def choice_count(self):
        return self.choices.count()
    
##########################################################################
class Choice(models.Model):
    ## validate question is of proper qtype
    question = models.ForeignKey(Question, related_name='choices',
                                 verbose_name=_('question'))
    text = models.CharField(_('choice text'), max_length=500)

    order = models.IntegerField(verbose_name = _("order"),
                                null=True, blank=True)

    @models.permalink
    def get_update_url(self):
        return ('choice-update', (), {'question_id': self.question.id,'choice_id' :self.id  })

    @property
    def count(self):
        if hasattr(self, '_count'):
            return self._count
        self._count = Answer.objects.filter(question=self.question_id, text=self.text).count()
        return self._count

    def __unicode__(self):
        return self.text

    class Meta:
        #  unique_together = (('question', 'text'),)
        order_with_respect_to='question'
        ordering = ('question', 'order')
        verbose_name        = _("Choice")
        verbose_name_plural = _("Choices")
        
##########################################################################
class Answer(models.Model):
    user = models.ForeignKey(User, related_name='answers',
                             verbose_name=_('user'), editable=False,
                             blank=True,null=True)
    question = models.ForeignKey(Question, related_name='answers',
                                 verbose_name=_('question'), editable=False)
    ## sessions expire, survey results do not, so keep the key.
    session_key = models.CharField(_('session key'), max_length=40)
    text = models.TextField(_('answer text'))
    submission_date = models.DateTimeField(auto_now=True)
    # UUID is used to calculate the number of interviews
    interview_uuid = models.CharField(_("Interview unique identifier"),max_length=36)
    
    class Meta:
        # unique_together = (('question', 'session_key'),)
        permissions = (("view_answers", "Can view survey answers"),
                       ("view_submissions", "Can view survey submissions"))
        verbose_name        = _("Answer")
        verbose_name_plural = _("Answers")
    
    def __unicode__(self):
        return self.text