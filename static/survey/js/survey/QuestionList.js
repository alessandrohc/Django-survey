Ext.ns('Survey.Data', 'Survey.UI', 'Survey.Handler');
//------------------------------------------
// datastore
//------------------------------------------
Survey.Data.QuestionListStore = function(){
    return new Ext.data.GroupingStore({
        reader: new Ext.data.JsonReader({
            idProperty: 'id',
            root: 'data',
            totalProperty: 'results',
            fields: ['id', 'survey_id', 'text', 'qstyle', 'qtype', 'required', 'order']
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
        template_url : _baseUrl + 'surveys/{0}/questions',
        setSurvey : function(store, survey_id) {
        	var url = String.format(store.template_url, survey_id);
        	store.proxy.setUrl(url, true);        	
        },
        
    });
};

//------------------------------------------
// handlers
//------------------------------------------
Survey.Handler.RecalculateQuestionOrders = function(grid, survey_id) {
    Ext.Ajax.request({
        url: String.format('{0}surveys/{1}/recalculate_orders', _baseUrl, survey_id),
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
Survey.Handler.DuplicateQuestion = function(grid, survey_id, question_id) {
    Ext.Ajax.request({
        url: String.format('{0}surveys/{1}/questions/{2}/duplicate', _baseUrl, survey_id, question_id),
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

Survey.UI.QuestionListColumnModel = function(sm, checkRequired){
    return ([sm, {
        header: 'text',
        dataIndex: 'text',
        sortable: false,
        width: 120    	
    }, {
        header: 'qstyle',
        dataIndex: 'qstyle',
        sortable: false,
        width: 60    	
    }, {
        header: 'qtype',
        dataIndex: 'qtype',
        sortable: false,
        width: 60    	
    }, checkRequired, {
        header: 'order',
        dataIndex: 'order',
        sortable: false,
        width: 60    	
    }]);
};

Survey.UI.QuestionList = function(){
	var sm = new Ext.grid.CheckboxSelectionModel({
        singleSelect: false,
        listeners: {
            selectionchange: function(sm){
            	if (sm.hasSelection()) {
            		var record = sm.getSelected();
                    Ext.ux.msgBus.publish('question.selected', record.data.survey_id, record.data.id);
            	} else {
                    Ext.ux.msgBus.publish('question.deselected');
            	}
            }
        }
    });
    var checkRequired = new Ext.grid.CheckColumn({
        header: 'required',
        dataIndex: 'required',
        sortable: false,
        width: 40,
        filterable: true,
    });
	
	
    var grid = Ext.ComponentMgr.create({
        xtype: 'grid',
        region:'center',
        disabled: true,
        width:170,
        split: true,
        showBbar: true,
		id:'question-list',
		plugins: [checkRequired],
        tbar: [{
            iconCls: 'silk-arrow-refresh',
            tooltip: gettext('Refresh grid'),
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
                Survey.Handler.RecalculateQuestionOrders(grid, grid.survey_id);
            }
        }, {
            iconCls: 'silk-add',
            tooltip: gettext('Add question'),
            text: gettext('Add question'),
            scope: this,
            handler: function(btn, event){
                var grid = btn.ownerCt.ownerCt;
                var store = grid.getStore();
                var u = new store.recordType({
                	text: gettext('new question'),
                	qtype: 'T'
                });
                grid.store.add(u);
            }
        }, {
        	iconCls: 'silk-page-copy',
        	tooltip: gettext('Duplicate question'),
        	text: gettext('Duplicate'),
        	handler: function(btn, evn) {
                var grid = btn.ownerCt.ownerCt;
                var sm = grid.getSelectionModel();
                if (sm.hasSelection()) {
                	var record = sm.getSelected();
                	Survey.Handler.DuplicateQuestion(grid, grid.survey_id, record.data.id);
                }
        	}
        },{
            iconCls: 'silk-delete',
            tooltip: gettext('Delete question'),
            text: gettext('Delete question'),
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
        cm: new Ext.grid.ColumnModel(Survey.UI.QuestionListColumnModel(sm, checkRequired)),
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
        store: Survey.Data.QuestionListStore(),
        updateData: function(component, survey_id) {
        	var store = component.getStore();
        	component.survey_id = survey_id;
			store.setSurvey(store, survey_id);
            store.load();
            component.setDisabled(false);
        }
    });
    
    Ext.ux.msgBus.subscribe('survey.selected', function(survey_id) {
    	grid.updateData(grid, survey_id);
    });
    
    return grid;
};

