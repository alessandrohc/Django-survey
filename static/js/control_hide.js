// Desenvolvido por: Alex Sandro
// alex@fabricaditial.com.br
(function($) {
  // ----------------------------------------------------
  function is_valid() { // se a seleção é válida.
	var bool = {"S":true,"R":true,"C":true};
	return bool[$("#id_qtype").val()]
  }
  OnInit = function() { // mostra ou oculta de forma instantanea.
	if (is_valid()) {
	  $('#choices-group').css({"opacity": 1.0});
	  $('#choices-group').show();
	} else {
	  $('#choices-group').css({"opacity": 0.0});
	  $('#choices-group').hide();
	}
  }
  OnSelect = function() { // aplica o efeito de transição show/hide.
	if (is_valid()) {
		$('#choices-group').show(); // show - permite visualizar a animação.
		$('#choices-group').animate({
		  opacity: 1.0,
		}, 300, function() {
		  // Animation complete.
		});
	  } else {
		$('#choices-group').animate({
		   opacity: 0.0,
		 }, 300, function() {
		  $(this).hide(); // hide - iniativa os controles.
		 });
	}
  }
  $(document).ready(function() {
	  $("#id_qtype").change( OnSelect );
	  OnInit(); //primeira verificação.
  });
  // ----------------------------------------------------
})(django.jQuery);