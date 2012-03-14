// dynamic load of a server side form
Ext.intercept(Ext.form.Field.prototype, 'initComponent', function() {
    var fl = this.fieldLabel, ab = this.allowBlank;
    if (ab === false && fl) {
        this.fieldLabel = '&nbsp;&nbsp;' + fl + ' <span style="color:red;">*</span>';
    } else if (ab === true && fl) {
        this.fieldLabel = '&nbsp;&nbsp;' + fl;
    }
});

Ext.ux.FieldHelp = Ext.extend(Object, (function(){
    function syncInputSize(w, h) {
        this.el.setSize(w, h);
    }

    function afterFieldRender() {
        if (!this.wrap) {
            this.wrap = this.el.wrap({cls: 'x-form-field-wrap'});
            this.positionEl = this.resizeEl = this.wrap;
            this.actionMode = 'wrap';
            this.onResize = this.onResize.createSequence(syncInputSize);
        }
        this.wrap[this.helpAlign == 'top' ? 'insertFirst' : 'createChild']({
            cls: 'x-form-helptext',
            html: this.helpText
        });
    }

    return {
        constructor: function(t, align) {
            this.helpText = t;
            this.align = align;
        },
        init : function(f) {
            f.helpAlign = this.align;
            f.helpText = this.helpText;
            f.afterRender = f.afterRender.createSequence(afterFieldRender);

        }
    };
})());

Ext.ux.DjangoForm = Ext.extend(Ext.FormPanel, {
    url: null,
    isLoaded: false,
    baseParamsLoad: null,
    callback: null,
    scope: null,
    border: false,
    custom_config: null,
    default_config: null,
    showButtons: true,
    showLoadMask: true,
    showSuccessMessage: 'The data has been saved.',
    fields: null,
    labelWidth: 160,
    maxFieldWidth: 400,
    monitorValid: true,
    resetOnSave: true,

    initComponent: function(){
        this.items = {
            border: false
        }
        if (this.showButtons) {
            this.resetButton = new Ext.Button({
                hidden: true,
                name: 'reset',
                iconCls: 'icon-cancel',
                text: "Reset",
                scope: this,
                handler: function(args){
                    this.resetForm();
                }
            });
            this.submitButton = new Ext.Button({
                hidden: true,
                name: 'submit',
                iconCls: 'icon-accept',
                text: "Submit",
                scope: this,
                formBind: true,
                handler: function(args){
                    this.submitForm();
                }
            });

            this.buttonAlign = 'left';
            this.buttons = [
                this.resetButton, '->', this.submitButton
            ];
        }

        this.getDefaultButton = function(name){
        
        }
        this.gotFormCallback = function(response, options){
            var res = Ext.decode(response.responseText);
            this.default_config = res;
            this.removeAll();

            /* save the fields */
            var fields = this.fields = {};
            Ext.each(res.items, function (field) {
                if (field.width && field.width > this.maxFieldWidth) {
                    field.width = this.maxFieldWidth;
                }
                if (field.helpText) {
                    Ext.apply(field, {plugins: [new Ext.ux.FieldHelp(field.helpText)]});
                }
                fields[field.name] = field;
            }, this);

            if (this.custom_config) {
                // add custom form config to this formpanel
                var newconf = this.custom_config.createDelegate(this, [this])();
                for (var i = 0; i < newconf.items.length; i++) {
                    this.addField(newconf.items[i]);
                }
                
                // auto add hidden fields from django form if needed
                for (var i = 0; i < this.default_config.length; i++) {
                    if (this.default_config[i].xtype == 'hidden') {
                        this.addField(this.default_config[i]);
                    }
                }
                //this.default_config = res;
            }
            else {
                if (this.intro) {
                    this.add({
                        html: this.intro,
                        style: 'padding-bottom:10px;padding-top:10px;font-size:14px',
                        border: false
                    });
                }
                if (this.startItems) {
                    this.add(this.startItems);
                }
                if (res.layout && res.layout.length > 0) {
                    Ext.each(res.layout, function (fieldset) {
                        if (fieldset[1] && fieldset[1] instanceof Object) {
                            /* complex field formatting: [[title, {fields: [f1, f2, ..]}], [title, {fields: [f1, f2, ..]}] */
                            var fs_fields = [];
                            if (fieldset[1].description) {
                                fs_fields[fs_fields.length] = {
                                    html: fieldset[1].description,
                                    bodyCssClass: 'x-panel-fieldset-info',
                                    //style: 'padding-bottom:10px',
                                    border: true
                                };
                            }
                            Ext.each(fieldset[1].fields, function (field) {
                                fs_fields[fs_fields.length] = fields[field];
                            }, this);
                            this.addField({
                                xtype: 'fieldset',
                                title: fieldset[0],
                                items: fs_fields
                            });
                        } else {
                            /* simple field list: [field, field, field, ..] */
                            var fs_fields = [];
                            Ext.each(fieldset, function (field) {
                                this.addField(fields[field]);
                            }, this);
                        }
                    }, this); 
                } else {
                    //  Ext.apply(this, this.default_config);
                    Ext.iterate(this.fields, function (name, field) {
                        this.addField(field);
                    }, this);
                }
            }

            if (this.showButtons) {
                this.submitButton.setText(res.buttons.submit || this.submitButton.text);
                this.resetButton.setText(res.buttons.reset || this.resetButton.text);
                this.submitButton.setVisible(true);
                this.resetButton.setVisible(true);
            }

            this.doLayout();

            if (this.showLoadMask) {
                this.loadMask.hide();
            }

            //finally callback your function when ready
            if (this.callback) {
                this.callback.createDelegate(this.scope, [this])();
            }
        }
        
        var o = {}
        if (this.baseParamsLoad) 
            Ext.apply(o, this.baseParamsLoad);
        
        Ext.ux.DjangoForm.superclass.initComponent.apply(this, arguments);

        this.on('render', function () {
            if (!this.isLoaded && this.showLoadMask && this.ownerCt.body) {
                this.loadMask = new Ext.LoadMask(this.ownerCt.body, {msg:"Please wait..."});
                this.loadMask.show();
            }
        }, this);
        
        this.addEvents('submitSuccess', 'submitError');
        
        Ext.Ajax.request({
            url: this.url,
            params: o,
            method: 'GET',
            scope: this,
            success: this.gotFormCallback,
            failure: this.gotFormCallback
        });
    },
    addField: function(cfg) {
        if (cfg.xtype && cfg.xtype == 'fileuploadfield') {
            this.getForm().fileUpload = true;
        }
        return this.add(Ext.ComponentMgr.create(cfg));
    },
    submitSuccess: function(){
        this.fireEvent('submitSuccess');
        if (this.showSuccessMessage) {
            Ext.Msg.show({
                title: 'Success',
                msg: this.showSuccessMessage,
                buttons: Ext.Msg.OK,
                icon: Ext.MessageBox.INFO
            });
        }
        if (this.resetOnSave) {
            this.resetForm();
        }
    },
    submitError: function(msg){
    
        this.fireEvent('submitError', msg);
        Ext.Msg.show({
            title: 'Error',
            msg: 'Invalid: <br>' + msg + '<br>',
            buttons: Ext.Msg.OK,
            icon: Ext.MessageBox.WARNING
        });
    },
    validResponse: function(form, action){
        this.submitButton.enable();
        this.resetButton.enable();

        if (action && action.result && action.result.success) {
            this.submitSuccess();
        }
        else {
            this.submitError(action && action.result && action.result.msg || 'erreur');
            
        }
        
    },
    invalid: function(){
        //    console.log('invalid: ', this.getForm().getValues());
        Ext.Msg.show({
            title: 'Error',
            msg: 'Invalid: please check all form fields are filled in & correct.',
            buttons: Ext.Msg.OK,
            icon: Ext.MessageBox.WARNING
        });
    },
    resetForm: function(){
        this.getForm().reset();
    },
    submitForm: function(){
        //console.log('submitForm');
        if (this.getForm().isValid()) {
            this.submitButton.disable();
            this.resetButton.disable();

            this.getForm().submit({
                scope: this,
                success: this.validResponse,
                failure: this.validResponse
            });
        }
        else {
            // console.log('invalid form!');
            // var items = this.getForm().items.items;
            // for (f in items) {
            // console.log(f, items[f], items[f].isValid());
            // }
            this.invalid()
        }
    }
    
});




Ext.ux.DjangoField = function(config){
    //  console.log(config);
    //         console.log(this);
    var items = config.django_form.default_config;
    
    for (var i = 0; i < items.length; i++) {
        if (items[i].name == config.name) {
        
            var bConfig = items[i];
            // prevent infinite loop
            
            if (config.xtype2) {
                config.xtype = config.xtype2
            }
            else {
                delete config.xtype
            }
            
            Ext.apply(bConfig, config);
            // console.log(bConfig); 
            
            return Ext.ComponentMgr.create(bConfig);
        }
    }
}



Ext.reg("DjangoForm", Ext.ux.DjangoForm);

Ext.reg("DjangoField", Ext.ux.DjangoField);

