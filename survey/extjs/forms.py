from django import forms
from django.utils.text import capfirst

CHAR_PIXEL_WIDTH = 8
CHAR_PIXEL_HEIGHT = 15

import utils
import simplejson
from django.forms.forms import BoundField
from django.forms import fields


class ExtJsForm(object):
    """
        .add a as_extjs method to forms.Form or forms.ModelForm; this method returns a formpanel json config, with all fields, buttons and logic
        .add a as_extjsfields method that returns only the field list. useful if you want to customise the form layout
        .add a html_errorlist to return form validations error for an extjs window
    """
    @classmethod
    def register(self, cls):
        cls.as_extjsfields = self.as_extjsfields
        cls.as_extjs = self.as_extjs
        cls.as_extjsdata = self.as_extjsdata
        cls.html_errorlist = self.html_errorlist
        # default submit handler
        handler_submit = "function(btn) {this.findParentByType(this.form_xtype).submitForm()}"
        handler_reset = "function(btn) {this.findParentByType(this.form_xtype).resetForm()}"
        cls.ext_baseConfig = {
        }

    @staticmethod
    def as_extjs(self,):
        config = ""
        config_dict = self.ext_baseConfig
        if getattr(self, 'ext_config', None):
            config_dict.update(self.ext_config)
        config_dict['items'] = self

        submit = "Submit"
        reset = "Reset"

        if hasattr(self, "Meta"):
            if hasattr(self.Meta, "model"):
                submit = "Save %s" % capfirst(self.Meta.model._meta.verbose_name)
            if hasattr(self.Meta, "fields"):
                config_dict['layout'] = self.Meta.fields
            if hasattr(self.Meta, "fieldsets"):
                config_dict['layout'] = self.Meta.fieldsets
            submit = getattr(self.Meta, "submit", submit)
            reset = getattr(self.Meta, "reset", reset)

        config_dict['buttons'] = {'submit': submit, 'reset': reset}
        
        return simplejson.dumps(config_dict, cls=utils.ExtJSONEncoder)

    @staticmethod
    def html_errorlist(self):
        html = ''
        for field, err in self.errors.items():
            html += '<br><b>%s</b> : %s' % (field, err.as_text())
        return html

    @staticmethod
    def as_extjsfields(self, includes=[], excludes=[]):
        """Return fields of Form in dict
        """
        if excludes:
            raise NotImplementedError()
        result = {}

        for name, field in self.fields.items():
            if name in includes:
                if isinstance(field, dict):
                    field['title'] = name
                else:
                    field.name = name
                # Bound fields with data
                bf = BoundField(self, field, name)
                # loads/dumps is ugly but almost resilient
                result[name] = simplejson.loads(simplejson.dumps(bf, cls=utils.ExtJSONEncoder))
        return result

    @staticmethod
    def as_extjsdata(self,):
        """Give form data only
        """
        result = {}
        if not self.is_bound and isinstance(self, forms.ModelForm):
            initial_data = {}
            for name, field in self.fields.items():
                bf = BoundField(self, field, name)
                # TODO : factorise
                if not bf.form.is_bound:
                    data = bf.form.initial.get(bf.name, bf.field.initial)
                    if callable(data):
                        data = data()
                    # temp hack for Checkbox
                    if not data and isinstance(bf.field, fields.BooleanField):
                        data = bf.data
                else:
                    data = bf.data
                initial_data[bf.name] = data
            result["data"] = initial_data
            result["success"] = True
        elif self.is_valid():
            result["data"] = self.cleaned_data
            result["success"] = True
        else:
            result["errors"] = self.errors
            result["success"] = False
        return simplejson.dumps(result, cls=utils.ExtJSONEncoder,
                                ensure_ascii=False)
