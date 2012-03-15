Ext.ns('Survey.Data', 'Survey.UI', 'Survey.Handler');
//------------------------------------------
// datastore
//------------------------------------------
Survey.Data.ChoiceListStore = function(){
    return new Ext.data.GroupingStore({
        reader: new Ext.data.JsonReader({
            idProperty: 'id',
            root: 'data',
            totalProperty: 'results',
            fields: ['id', 'survey_id', 'question_id', 'text',  'order']
        }),
        writer: new Ext.data.JsonWriter({
            encode: true
        }),
        sortInfo: {
            field: 'order',
            direction: 'ASC' // or 'DESC' (case sensitive for local sorting)
        },
        autoLoad: false,
        remoteSort: true,
        restful: true,
        proxy: new Ext.data.HttpProxy({
            url: '/',
            method: 'GET'
        }),
        template_url : _baseUrl + 'surveys/{0}/questions/{1}/choices',
        setQuestion : function(store, survey_id, question_id) {
        	var url = String.format(store.template_url, survey_id, question_id);
        	store.proxy.setUrl(url, true);        	
        }
        
    });
};

//------------------------------------------
//handlers
//------------------------------------------
Survey.Handler.RecalculateChoiceOrders = function(grid, survey_id, question_id) {
    Ext.Ajax.request({
        url: String.format('{0}surveys/{1}/questions/{2}/choices/recalculate_orders', _baseUrl, survey_id, question_id),
        failure: function(result, request){
        },
        success: function(result, request){
            if (result.status != 200) {
                return;
            }
        	grid.getStore().reload();
        }
    });
}
//------------------------------------------
//ui
//------------------------------------------

Survey.UI.ChoiceListColumnModel = function(sm){
    return ([sm, {
        header: 'text',
        dataIndex: 'text',
        sortable: false,
        width: 120,
        editor: {
        	xtype: 'textfield',
            allowBlank: false
        }
    }, {
        header: 'order',
        dataIndex: 'order',
        sortable: false,
        width: 60,
        editor:{ 
        	xtype: 'numberfield',
            allowBlank: true
        }
    }]);
};

Survey.UI.ChoiceList = function(){
	var sm = new Ext.grid.CheckboxSelectionModel({
        singleSelect: false,
        listeners: {
            selectionchange: function(sm){
            	if (sm.hasSelection()) {
            		var record = sm.getSelected();
                    Ext.ux.msgBus.publish('choice.selected', record.data.question_id, record.data.id);
            	}
            }
        }
    });
    var grid = Ext.ComponentMgr.create({
        xtype: 'editorgrid',
        region:'east',
        width:400,
        disabled: true,
        split: true,
        collapsible: true,
		id:'choice-list',
        tbar: [{
            iconCls: 'silk-arrow-refresh',
            text: gettext('Refresh'),
            scope: this,
            handler: function(btn, ev){
                var grid = btn.ownerCt.ownerCt;
                grid.getStore().reload();
            }
        }, {
            iconCls: 'silk-table-gear',
            tooltip: gettext('Recalculate orders'),
            text: gettext('Recalculate orders'),
            scope: this,
            handler: function(btn, event) {
                var grid = btn.ownerCt.ownerCt;
                Survey.Handler.RecalculateChoiceOrders(grid, grid.survey_id, grid.question_id);
            }
        }, {
            iconCls: 'silk-add',
            tooltip: gettext('Add choice'),
            text: gettext('Add choice'),
            scope: this,
            handler: function(btn, event){
                var grid = btn.ownerCt.ownerCt;
                var store = grid.getStore();
                var u = new store.recordType({
                	text: gettext('new choice'),
                });
                grid.store.add(u);
            }
        }, {
            iconCls: 'silk-delete',
            tooltip: gettext('Delete choice'),
            text: gettext('Delete choice'),
            scope: this,
            handler: function(btn, evn){
                Ext.Msg.show({
                    title: gettext('Confirmation'),
                    msg: gettext('Confirm delete?'),
                    buttons: Ext.Msg.YESNOCANCEL,
                    fn: function(b, text){
                        if (b == 'yes') {
                            var grid = btn.ownerCt.ownerCt;
                            var sm = grid.getSelectionModel();
                            if (sm.hasSelection()) {
                                grid.store.remove(sm.getSelections());
                            }
                        }
                    },
                    icon: Ext.MessageBox.WARNING
                });
                
            }
        }],
        loadMask: false,
        sm: sm,
        cm: new Ext.grid.ColumnModel(Survey.UI.ChoiceListColumnModel(sm)),
        view: new Ext.grid.GroupingView({
            hideGroupedColumn: false,
            forceFit: true,
            groupTextTpl: '{text} ({[values.rs.length]} {[values.rs.length > 1 ? "éléments" : "élement"]})'
        }),
        listeners: {
            rowdblclick: function(grid, index, e){
                var sm = grid.getSelectionModel();
                if (sm.hasSelection()) {
                    var record = sm.getSelected();
                }
            }
        },
        store: Survey.Data.ChoiceListStore(),
        updateData: function(component, survey_id, question_id) {
        	component.survey_id = survey_id;
        	component.question_id = question_id;
        	var store = component.getStore();
			store.setQuestion(store, survey_id, question_id);
            store.load();
        }
    });
    
    Ext.ux.msgBus.subscribe('question.selected', function(survey_id, question_id) {
    	grid.setDisabled(false);
    	grid.updateData(grid, survey_id, question_id);
    });
    Ext.ux.msgBus.subscribe('question.deselected', function() {
    	grid.setDisabled(true);
    });
    
    return grid;
};

