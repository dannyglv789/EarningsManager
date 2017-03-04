// var current_pay = $('#current_pay').val();
var ca_fica_emp = 0.062;
var ca_fica_medi_emp = 0.0145;
var ca_state_tax = 0.06;
var federal_tax =  0.11125;

$(document).ready(function(){

  // REGULAR PAY FROM RATE * HOURS
  $("#reg_hours").keyup(function(){
  var regular_period = this.value * $("#reg_rate").val();
  $("#reg_period").val(regular_period.toFixed(2)); 
	  
  });
  
  // OVERTIME PAY FROM RATE * HOURS
  $("#ov_hours").keyup(function(){
  var ov_period = this.value * $("#ov_rate").val();
  $("#ov_period").val(ov_period.toFixed(2)); 
	  
  });
  
    
}); 