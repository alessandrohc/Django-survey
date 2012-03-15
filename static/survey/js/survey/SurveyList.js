Ext.ns('Survey.Data', 'Survey.UI', 'Survey.Handler');
//------------------------------------------
// datastore
//------------------------------------------
Survey.Data.SurveyListStore = function(){
    return new Ext.data.GroupingStore({
        reader: new Ext.data.JsonReader({
            idProperty: 'id',
            root: 'data',
            totalProperty: 'results',
            fields: ['id', 'title', 'slug', 'opens', 'closes']
        }),
        writer: new Ext.data.JsonWriter({
            encode: true
        }),
        sortInfo: {
            field: 'id',
            direction: 'ASC' // or 'DESC' (case sensitive for local sorting)
        },
        autoLoad: true,
        remoteSort: true,
        restful: true,
        proxy: new Ext.data.HttpProxy({
            url: _baseUrl + 'surveys',
            method: 'GET'
        })
    });
};
//------------------------------------------
// ui
//------------------------------------------
Survey.UI.SurveyDetail = function() {
    var form = Ext.ComponentMgr.create({
        xtype: 'dynform',
        region: 'south',
        height:200,
        split: true,
        disabled: true,
        title: gettext('Details'),
        autoScroll: true,
        id: 'survey-details'
    });
    Ext.ux.msgBus.subscribe('survey.selected', function(survey_id) {
        var url = String.format('{0}surveys/{1}.form',  _baseUrl, survey_id);
        params = {
        };
        form.setDisabled(false);
        form.updateData(form, survey_id, url, params);
    });
    Ext.ux.msgBus.subscribe('survey.deselected', function() {
    	form.setDisabled(true);
    });
    
    return form;
}


Survey.UI.SurveyListColumnModel = function(){
    return ([{
        header: 'title',
        dataIndex: 'title',
        sortable: true,
        width: 60
    }]);
};

Survey.UI.SurveyList = function(){
    return {
        xtype: 'grid',
        region:'west',
        width:170,
        split: true,
        showBbar: true,
		id:'survey-list',
        tbar: [{
            iconCls: 'silk-arrow-refresh',
            text: gettext('Refresh'),
            tooltip: 'Rafraichir',
            scope: this,
            handler: function(btn, ev){
                var grid = btn.ownerCt.ownerCt;
                grid.getStore().reload();
            }
        }, {
            iconCls: 'silk-add',
            tooltip: gettext('Add survey'),
            text: gettext('Add survey'),
            scope: this,
            handler: function(btn, event){
                var grid = btn.ownerCt.ownerCt;
                var store = grid.getStore();
                var u = new store.recordType({
                	title: gettext('new survey'),
                	slug: gettext('new-survey'),
                	opens: '2009-01-01',
                	closes: '2014-01-01'
                });
                grid.store.add(u);
            }
        }, {
            iconCls: 'silk-delete',
            tooltip: gettext('Delete survey'),
            text: gettext('Delete survey'),
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
        sm: new Ext.grid.RowSelectionModel({
            singleSelect: true,
            listeners: {
                selectionchange: function(sm){
                	if (sm.hasSelection()) {
                		var record = sm.getSelected();
                        Ext.ux.msgBus.publish('survey.selected', record.data.id);
                	}
                	
                }
            }
        }),
        cm: new Ext.grid.ColumnModel(Survey.UI.SurveyListColumnModel()),
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
        store: Survey.Data.SurveyListStore()
    };
};

