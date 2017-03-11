// var current_pay = $('#current_pay').val();
var ca_fica_emp = 0.062;
var ca_fica_medi_emp = 0.0145;
var ca_state_tax = 0.06;
var federal_tax =  0.11125;

$(document).ready(function(){

  // CURRENT PAY FROM RATE * HOURS
  $("#hours").keyup(function(){
  var current_pay_total = this.value * $("#rate").val();
  $("#current_pay").val(current_pay_total); 
	  
  });
  
  // NAV MENU
$("#nav_menu").change(function(){
	picked = $("#nav_menu option:selected").text();
	if(picked === "profile"){
		window.location.href = "http://localhost:5000/myhome/";
	}
	else{
		window.location.href = "http://localhost:5000/logout/";
	}
})
  
}); 