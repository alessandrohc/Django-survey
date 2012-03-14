__all__ = ('register', )

class AlreadyRegistered(Exception):
    """
    An attempt was made to register a model for MPTT more than once.
    """
    pass

registry = []

def register(form, ):
    """
    Sets the given model class up for Modified Preorder Tree Traversal.
    """
    from django.utils.translation import ugettext as _

    from forms import ExtJsForm

    if form in registry:
        raise AlreadyRegistered(
            _('The form %s has already been registered.') % form.__name__)
    registry.append(form)

    # Add tree options to the model's Options
    form.handler_submit = "function(btn) {console.log(this, btn);this.findParentByType(this.form_xtype).submitForm()}"
    form.handler_reset = "function(btn) {console.log(this, btn);this.findParentByType(this.form_xtype).resetForm()}"
    form.ext_baseConfig = {}

    # Add tree methods for form instances
    setattr(form, 'as_extjsfields', ExtJsForm.as_extjsfields)
    setattr(form, 'as_extjs', ExtJsForm.as_extjs)
    setattr(form, 'as_extjsdata', ExtJsForm.as_extjsdata)
    setattr(form, 'html_errorlist', ExtJsForm.html_errorlist)
