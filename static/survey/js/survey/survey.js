Ext.ns('Survey.Data', 'Survey.UI', 'Survey.Handler');

Ext.onReady(function() {
	Ext.QuickTips.init();
	Ext.ux.msgBus = new Ext.ux.MessageBus();


	Ext.Ajax.on('beforerequest', function (conn, options) {
		   if (!(/^http:.*/.test(options.url) || /^https:.*/.test(options.url))) {
		     if (typeof(options.headers) == "undefined") {
		       options.headers = {'X-CSRFToken': Ext.util.Cookies.get('csrftoken')};
		     } else {
		       options.headers.extend({'X-CSRFToken': Ext.util.Cookies.get('csrftoken')});
		     }                        
		   }
		}, this);
		
	var viewport = new Ext.Viewport({
		layout : 'fit',
		items : [ {
			layout : 'border',
			border : false,
			items : [ Survey.UI.SurveyList(), {
				layout:'border',
				region:'center',
				items:[Survey.UI.QuestionList(), Survey.UI.SurveyDetail()]
			}, {
				layout : 'border',
				region:'east',
				width:700,
				split: true,
				items : [ Survey.UI.QuestionDetails(), Survey.UI.ChoiceList() ]
			}]
		} ]
	});
});