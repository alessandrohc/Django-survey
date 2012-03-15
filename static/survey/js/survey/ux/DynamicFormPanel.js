Ext.ns("Ext.ux");
Ext.ux.DynamicFormPanel = Ext.extend(Ext.form.FormPanel, {
    object_id: 0,
    autoBack: false,
    reloadAfterSubmit: true,
	cancelLabel:'Cancel',
    url: '/',
    
    initComponent: function(){
        this.addEvents('success', 'failure', 'cancel', 'afterupdatefields');
        var defaultConfig = {};
        Ext.applyIf(this, defaultConfig);
        var config = {
            listeners: {
            	show: function(panel) {
            		panel.doLayout(true, true);
            	}
            }
        }
        
        Ext.apply(this, config);
        Ext.apply(this.initialConfig, config);
        Ext.ux.DynamicFormPanel.superclass.initComponent.apply(this, arguments);
    },
    resetData: function(form){
        form.getForm().reset();
    },
    updateFields: function(formDescription){
        var form = this;
        form.removeAll(true);
        Ext.each(formDescription.items, function(item){
            if (item.xtype == 'datefield') {
                item.format = 'd/m/Y'
            }
            if (item.xtype == 'textarea') {
                item.anchor = '-20';
                item.height = 200;
            }
            form.add(Ext.ComponentMgr.create(item));
        }, this);
        
        form.add(form.getButtons());
        
		form.doLayout();
        this.fireEvent('afterupdatefields', this);
    },
    getButtons: function() {
    	return {
    		xtype:'panel',
            buttonAlign: 'center',
            buttons: [{
                text: 'Valider',
                formBind: true,
                handler: function(btn, e){
                    var form = btn.findParentByType('dynform');
                    if (form.getForm().isValid()) {
                        var id = form.object_id;
                        params = form.params;
                        form.findBy(function(item){
                            if (item.xtype == 'multiselect') {
                                var values = item.getValue();
                                item.setDisabled(true);
								if (values) {
									params[item.name] = values.split(",");
								}
                            }
                            return false;
                        }, this);
                        
                        form.getForm().submit({
                            url: form.url,
                            method: 'POST',
                            waitMsg: 'Transmission des informations...',
                            success: function(fp, o){
                            	if (form.reloadAfterSubmit) {
                            		form.loadData(form, form.object_id);
                            	}
                            	if (form.autoBack) {
                            		Ext.History.back();
                            	}
                                form.fireEvent('success', fp, o);
                            },
                            failure: function(fp, o){
                                form.fireEvent('failure', fp, o);
                            },
                            params: params
                        });
                    }
                }
            }, {
                text: this.cancelLabel,
                handler: function(btn, e){
                    var form = btn.findParentByType('dynform');
                    form.resetData(form);
                	if (form.autoBack) {
                		Ext.History.back();
                	}
                    form.fireEvent('cancel');
                }
            }]
    	}
    },
    
    loadData: function(form, object_id){
        this.object_id = object_id;
        form.removeAll(true);
        Ext.Ajax.request({
            url: this.url,
			method: 'GET',
			params: this.params,
            failure: function(result, request){
                form.resetData(form);
            },
            success: function(result, request){
                if (result.status != 200) {
                    form.resetData(form);
                    return;
                }
                var json = Ext.decode(result.responseText);
                var formDescription = json.data.form;
                if (typeof(formDescription) == typeof('string')) {
                    var formDescription = Ext.decode(formDescription);
				} 
                form.updateFields(formDescription);
            }
        });
    },
    updateData: function(component, object_id, url, params){
        component.object_id = object_id;
        component.url = url;
		component.params = params;
        component.loadData(component);
    },
	refresh: function() {
		this.loadData(this);
	},
	loadFromDescription: function(description) {
		this.resetData(this);
        if (typeof(formDescription) == typeof('string')) {
            var formDescription = Ext.decode(formDescription);
        } 
        this.updateFields(formDescription);
	}
});
Ext.reg('dynform', Ext.ux.DynamicFormPanel);
