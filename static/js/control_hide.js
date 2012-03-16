// 
(function($) {
  // ----------------------------------------------------
  function is_valid() { // se a seleção é válida.
	var bool = {"S":true,"R":true,"C":true};
	return bool[ $("#id_qtype").val() ]
  }
  OnInit = function() { // mostra ou oculta de forma instantanea.
	if (is_valid()) {
	  $('#choices-group').css({"opacity": 1.0});
	} else {
	  $('#choices-group').css({"opacity": 0.0});;
	}
  }
  OnSelect = function() { // aplica o efeito de trasição show/hide.
	if (is_valid()) {
		$('#choices-group').animate({
		  opacity: 1.0,
		}, 300, function() {
		  // Animation complete.
		});
		
	  } else {
		$('#choices-group').animate({
		   opacity: 0.0,
		 }, 300, function() {
		   // Animation complete.
		 });
	}
  }
  $(document).ready(function() {
	  $("#id_qtype").change( OnSelect );
	  OnInit(); //primeira verificação.
  });
  // ----------------------------------------------------
})(django.jQuery);