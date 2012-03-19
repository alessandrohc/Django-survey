"""
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'Django-survey.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name

class CustomIndexDashboard(Dashboard):
    """ Custom index dashboard for www. """
    
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        request = context['request']
        
        if request.user.is_superuser:
            # append an app list module for "Administration"
            self.children.append(modules.ModelList(
                _('ModelList: Administration'),
                column=1,
                collapsible=False,
                models=('django.contrib.*',),
            ))
            
            # append an app list module for "Applications"
            self.children.append(modules.ModelList(
                _('AppList: Applications'),
                collapsible=False,
                column=1,
                exclude=('django.contrib.*',),
            ))
        else:
            self.children.append(modules.ModelList(
                title = _('Administration'),
                column = 1,
                models = (
                    'survey.models.Survey',
                    'survey.models.Question',
                )
            ))
