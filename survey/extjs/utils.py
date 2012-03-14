import datetime
import pickle
from copy import copy, deepcopy
from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.forms import fields, widgets
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from django.forms.forms import BoundField
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.core.serializers.json import Serializer as JSONSerializer
from django.utils.text import capfirst
import simplejson
from django.utils.functional import Promise
from django.utils.encoding import force_unicode
from django.shortcuts import get_object_or_404


from django.http import HttpResponseRedirect
try:
    from django.utils.decorators import available_attrs
except ImportError:
    # django 1.1
    try:
        from functools import wraps, update_wrapper, WRAPPER_ASSIGNMENTS
    except ImportError:
        from django.utils.functional import wraps, update_wrapper, WRAPPER_ASSIGNMENTS  # Python 2.4 fallback.
    def available_attrs(fn):
        """
        Return the list of functools-wrappable attributes on a callable.
        This is required as a workaround for http://bugs.python.org/issue3445.
        """
        return tuple(a for a in WRAPPER_ASSIGNMENTS if hasattr(fn, a))

try:
    from functools import update_wrapper, wraps
except ImportError:
    from django.utils.functional import update_wrapper, wraps  # Python 2.4 fallback.

class ExtJSONEncoder(DjangoJSONEncoder):
    """
    JSONEncoder subclass that knows how to encode django forms into ExtJS config objects.
    """

    CHECKBOX_EDITOR = {
        'xtype': 'checkbox',
        'hideLabel': True
    }
    COMBO_EDITOR = {
        'listWidth': 'auto',
        'value': '',
        'mode': 'local',
        'width': 150,
        'xtype': 'combo',
        'forceSelection': True,
        'editable': True,
        'triggerAction': 'all',
        'selectOnFocus': True,
        'typeAhead': True,
    }

    MULTI_SELECT_EDITOR = {
        'width': 150,
        'xtype': 'multiselect'
    }

    DATE_EDITOR = {
        'xtype': 'datefield'
    }
    EMAIL_EDITOR = {
        'vtype':'email',
        'xtype': 'textfield'
    }
    NUMBER_EDITOR = {
        'xtype': 'numberfield'
    }
    NULL_EDITOR = {
        'fieldHidden': True,
        'xtype': 'textfield'
    }
    TEXT_EDITOR = {
        'xtype': 'textfield'
    }
    TEXTAREA_EDITOR = {
        'xtype': 'textarea'
    }
    TIME_EDITOR = {
        'xtype': 'timefield'
    }
    URL_EDITOR = {
        'vtype':'url',
        'xtype': 'textfield'
    }
    FILE_EDITOR = {
        'xtype': 'fileuploadfield'
    }
    CHAR_PIXEL_WIDTH = 8

    EXT_DEFAULT_CONFIG = {
        'xtype': 'textfield',
        'labelWidth': 300,
        'autoWidth': True,
    }

    DJANGO_EXT_FIELD_TYPES = {
        fields.BooleanField: ["Ext.form.Checkbox", CHECKBOX_EDITOR],
        fields.CharField: ["Ext.form.TextField", TEXT_EDITOR],
        fields.IPAddressField: ["Ext.form.TextField", TEXT_EDITOR],
        fields.SlugField: ["Ext.form.TextField", TEXT_EDITOR],
        fields.ChoiceField: ["Ext.form.ComboBox", COMBO_EDITOR],
        fields.TypedChoiceField: ["Ext.form.ComboBox", COMBO_EDITOR],
        fields.DateField: ["Ext.form.DateField", DATE_EDITOR],
        fields.DateTimeField: ["Ext.form.DateField", DATE_EDITOR],
        fields.DecimalField: ["Ext.form.NumberField", NUMBER_EDITOR],
        fields.EmailField: ["Ext.form.TextField", EMAIL_EDITOR],
        fields.IntegerField: ["Ext.form.NumberField", NUMBER_EDITOR],
        ModelChoiceField: ["Ext.form.ComboBox", COMBO_EDITOR],
        ModelMultipleChoiceField: ["Ext.ux.form.MultiSelect", MULTI_SELECT_EDITOR],
        fields.MultipleChoiceField: ["Ext.ux.form.MultiSelect",MULTI_SELECT_EDITOR],
        fields.NullBooleanField: ["Ext.form.Checkbox", CHECKBOX_EDITOR],
        fields.SplitDateTimeField: ["Ext.form.DateField", DATE_EDITOR],
        fields.TimeField: ["Ext.form.DateField", TIME_EDITOR],
        fields.URLField: ["Ext.form.TextField", URL_EDITOR],
        fields.ImageField: ["Ext.ux.form.FileUploadField", FILE_EDITOR],
        fields.FileField: ["Ext.ux.form.FileUploadField", FILE_EDITOR]
    }

    DJANGO_EXT_WIDGET_TYPES = {
        widgets.Textarea: ["Ext.form.TextArea", TEXTAREA_EDITOR],
    }

    EXT_DATE_ALT_FORMATS = 'm/d/Y|n/j/Y|n/j/y|m/j/y|n/d/y|m/j/Y|n/d/Y|m-d-y|m-d-Y|m/d|m-d|md|mdy|mdY|d|Y-m-d'

    EXT_TIME_ALT_FORMATS = 'm/d/Y|m-d-y|m-d-Y|m/d|m-d|d'

    DJANGO_EXT_FIELD_ATTRS = {
        #Key: django field attribute name
        #Value: tuple[0] = ext field attribute name,
        #       tuple[1] = default value
        'choices': ['store', None],
        #'default': ['value', None],
        'fieldset': ['fieldSet', None],
        'help_text': ['helpText', None],
        'initial': ['value', None],
        'label': ['fieldLabel', None],
        'boxlabel': ['boxLabel', None],
        'max_length': ['maxLength', None],
        'max_value': ['maxValue', None],
        'min_value': ['minValue', None],
        'name': ['name', None],
        'required': ['allowBlank', False],
        'size': ['width', None],
        'hidden': ['fieldHidden', False],
        'value': ['value', False],
    }

    def default(self, o):
        """Serializer
        """
        # Serialize : Forms
        if issubclass(o.__class__, forms.Form) or issubclass(o.__class__, forms.ModelForm):
            flds = []

            for name, field in o.fields.items():
                if isinstance(field, dict):
                    field['title'] = name
                else:
                    field.name = name
                # Bound fields with data
                bf = BoundField(o, field, name)
                cfg = self.default(bf)
                flds.append(cfg)
            return flds

        if isinstance(o, Promise):
            return force_unicode(o)

        # Serialize : Dict
        elif isinstance(o, dict):
            #Fieldset
            default_config = {
                'autoHeight': True,
                'collapsible': True,
                'items': [],
                'labelWidth': 200,
                'title': o['title'],
                'xtype':'fieldset',
            }
            del o['title']

            #Ensure fields are added sorted by position
            for name, field in sorted(o.items()):
                field.name = name
                default_config['items'].append(self.default(field))
            return default_config

        # Serialize BoundFields
        elif issubclass(o.__class__, BoundField):
            default_config = {}
            if o.field.__class__ in self.DJANGO_EXT_FIELD_TYPES:
                default_config.update(self.DJANGO_EXT_FIELD_TYPES[o.field.__class__][1])

                #print o.field.widget.__class__
                if o.field.widget.__class__ in self.DJANGO_EXT_WIDGET_TYPES:
                    default_config.update(self.DJANGO_EXT_WIDGET_TYPES[o.field.widget.__class__][1])

            else:
                default_config.update(self.EXT_DEFAULT_CONFIG)
            config = deepcopy(default_config)
            for dj, ext in self.DJANGO_EXT_FIELD_ATTRS.items():
                v = None

                # Adapt the value with type of field
                if dj == 'size':
                    v = o.field.widget.attrs.get(dj, None)
                    if v is not None:
                        if o.field.__class__ in (fields.DateField, fields.DateTimeField, fields.SplitDateTimeField, fields.TimeField):
                            v += 8
                        #Django's size attribute is the number of characters,
                        #so multiply by the pixel width of a character
                        v = v * self.CHAR_PIXEL_WIDTH
                elif dj == 'hidden':
                    v = o.field.widget.attrs.get(dj, default_config.get('fieldHidden', ext[1]))
                elif dj == 'name':
                    v = o.field.name
                elif dj == 'required':
                    v = not o.field.required
                elif dj == 'value':
                    # Get value depends of source
                    # http://code.djangoproject.com/browser/django/trunk/django/forms/forms.py#L432
                    if not o.form.is_bound:
                        data = o.form.initial.get(o.name, o.field.initial)
                        if callable(data):
                            data = data()
                        # temp hack for Checkbox
                        if not data and isinstance(o.field, fields.BooleanField):
                            data = o.data
                    else:
                        data = o.data
                    v = data
                elif dj == 'label':
                    v = o.field.widget.attrs.get(dj, None)
                    if v is None:
                        v = getattr(o.field, 'label', None)
                        if v is None:
                            v = capfirst(o.field.name.replace("_", " "))
                        else:
                            v = force_unicode(v)
                elif dj == 'boxlabel':
                    if isinstance(o.field, fields.BooleanField):
                        v = o.field.widget.attrs.get(dj, None)
                        if v is None:
                            v = getattr(o.field, 'label', None)
                            if v is None:
                                v = capfirst(o.field.name.replace("_", " "))
                            else:
                                v = force_unicode(v)
                        v = v + u'?'
                elif getattr(o.field, dj, ext[1]) is None:
                    pass
                elif isinstance(ext[1], basestring):
                    v = getattr(o.field, dj, getattr(field, ext[1]))
                elif dj == 'choices':
                    v = getattr(o.field, dj, None)
                else:
                    v = getattr(o.field, dj, ext[1])

                # Time to use v
                if v is not None:
                    ejs, df = ext # extjsfield name, default value
                    if ejs == 'value':
                        config[ejs] = v
                        if default_config == self.CHECKBOX_EDITOR:
                            config['checked'] = v
                    if ejs == 'name':
                        config[ejs] = v
                        config['header'] = v
                        if default_config == self.COMBO_EDITOR:
                            config['hiddenName'] = v
                    elif ejs not in ('dataIndex', 'fieldLabel', 'header', 'defaultValue'):
                        if ejs == 'store':
                            config[ejs] = [ [force_unicode(y), force_unicode(z)] for y, z in v]
                        else:
                            config[ejs] = v

                    elif isinstance(v, unicode):
                        config[ext[0]] = v.encode('utf8')
                    else:
                        config[ext[0]] = v

            return config
        elif issubclass(o.__class__, models.Model):
            return force_unicode(o)
        else:
            # Go up
            return super(ExtJSONEncoder, self).default(o)

def query_from_request(request, queryset, fields):
    """Modify a queryset with request args

    Params :
     - request
     - queryset : queryset to modify
     - fields : dict with query <=> django field associations

    For example request with::

        name=toto&sort=id

    With fields::

        fields = {"name": "group__name", "id": "id"}

    Is equivalent to::

        queryset.filter(group__name__icontains="toto").order_by(['id'])

    queryset can be limited with start= & limit=

    """
    # Filter time
    for extfield, djfield in fields.items():
        if extfield in request.REQUEST:
            value = request.REQUEST.get(extfield)
            filter_args = {'%s__icontains' % djfield : value}
            queryset = queryset.filter(**filter_args)

    # Sort time
    if 'sort' in request.REQUEST:
        sort = request.REQUEST.get('sort')
        if sort not in fields.keys():
            raise IndexError("Sort criter not listed in fields")
        dj_sort = fields[sort]

        if 'dir' in request.REQUEST:
            direction = request.REQUEST.get('dir')
            if direction == 'DESC':
                dj_sort = '-%s' % (dj_sort)
        queryset = queryset.order_by(dj_sort)

    # get start time
    start = request.REQUEST.get("start", 0)
    try:
        start = int(start)
    except ValueError:
        # Silent error because of user
        return queryset.none()

    # limit time
    if 'limit' in request.REQUEST:
        limit = request.REQUEST.get('limit')
        try:
            limit = int(limit)
        except ValueError:
            # Silent error because of user
            return queryset.none()
        queryset = queryset[start:start+limit]
    elif start:
        queryset = queryset[start:]

    return queryset

class ExtJSONSerializer(JSONSerializer):
    """Convert a queryset into
    """
    def end_object(self, obj):
        """Don't add pk, model"""
        self.objects["data"].append(self._current)
        self._current = None

    def end_serialization(self):
        self.options.pop('stream', None)
        self.options.pop('fields', None)
        self.options.pop('use_natural_keys', None)
        extjs = self.options.pop('extjs', None)
        simplejson.dump(self.objects, self.stream, cls=ExtJSONEncoder, **self.options)
    def start_serialization(self):
        self._current = None
        self.message = getattr(self.options, "message", None)
        self.objects = {"success": True, "data":[]}
        if self.message:
            self.objects["message"] = self.message

def JsonResponse(content, *args, **kwargs):
    if kwargs.get('mimetype', None) is None:
        kwargs['mimetype'] = "application/json"
    return HttpResponse(content, *args, **kwargs)

def JsonError(error = '', *args, **kwargs):
    result = {"success": False, "msg": error }
    return JsonResponse(simplejson.dumps(result, cls=ExtJSONEncoder), *args, **kwargs)

def JsonSuccess(context=None, *args, **kwargs):
    if not context: context = {}
    context.update({'success': True})
    return JsonResponse(simplejson.dumps(context, cls=ExtJSONEncoder), *args, **kwargs)

def JsonSerialize(content):
    return simplejson.dumps(content, cls=ExtJSONEncoder)

def user_passes_test(test_func, login_url=None):
    """
    Decorator for views that checks that the user passes the given test,
    get an extjs error. The test should be a callable
    that takes the user object and returns True if the user passes.
    """
    if not login_url:
        from django.conf import settings
        login_url = settings.LOGIN_URL

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            rsp = {"success" : False, 'errorMsg': 'not connected', 'notConnected': True}
            result = simplejson.dumps(rsp, cls=ExtJSONEncoder)
            return JsonResponse(result)
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorator

def JsonResponseNotFound(*args, **kwargs):
    """Send Http404 with json response
    """
    result = {"success": False, "reason": "not found" }
    return HttpResponseNotFound(simplejson.dumps(result, cls=ExtJSONEncoder), mimetype='text/javascript', *args, **kwargs)


def extjs_login_required(function=None):
    """
    Decorator for views that checks that the user is logged in.
    """
    actual_decorator = user_passes_test(lambda u: u.is_authenticated())
    if function:
        return actual_decorator(function)
    return actual_decorator

def get_object_or_404_json(*args, **kwargs):
    """Try to get an object or return a JsonResponseNotFound
    """
    try:
        result = get_object_or_404(*args, **kwargs)
    except Http404:
        result = JsonResponseNotFound()
    return result
