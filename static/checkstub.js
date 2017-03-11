// var current_pay = $('#current_pay').val();
var ca_fica_emp = 0.062;
var ca_fica_medi_emp = 0.0145;
var ca_state_tax = 0.06;
var federal_tax =  0.11125;

$(document).ready(function(){

/*
	// FICA SOCIAL SECURITY
   $( "#current_pay" ).keyup(function() {
  var fica_total = this.value * ca_fica_emp;
  $("#fica_social_total").val(fica_total.toFixed(2));
 
	// FICA MEDICARE 
  var fica_medi_total = this.value * ca_fica_medi_emp;
  $("#fica_medi_total").val(fica_medi_total.toFixed(2));
  
   // STATE TAX 
  var state_tax_total = this.value * ca_state_tax;
  $("#state_tax").val(state_tax_total.toFixed(2));
  
   // FEDERAL TAX
  var fed_tax_total = this.value * federal_tax;
  $("#federal_tax").val(fed_tax_total.toFixed(2));
  
  // TOTAL
  var our_total = this.value - 0;
  $("#total").val(our_total.toFixed(2));
  
  // DEDUCTIONS
  var deductions = fica_medi_total + fica_total + fed_tax_total + state_tax_total;
  $("#deductions").val(deductions.toFixed(2));
  
  // NET PAY
  var net = this.value - deductions;
  $("#net_pay").val(net.toFixed(2));
});
   
*/

  // CURRENT PAY FROM RATE * HOURS
  $("#hours").keyup(function(){
  var current_pay_total = this.value * $("#rate").val();
  $("#current_pay").val(current_pay_total); 
	  
  });
  
/*
  // YTD GROSS
  $("#ytd_num").click(function(){
  var ytd_gross_total = this.value * $("#total").val();
  var ytd_deductions_total = this.value * $("#deductions").val();
  var ytd_net_total = this.value * $("#net_pay").val()
  $("#ytd_gross").val(ytd_gross_total.toFixed(2));
  $("#ytd_deductions").val(ytd_deductions_total.toFixed(2));
  $("#ytd_net").val(ytd_net_total.toFixed(2));

  })
*/
  
$("#nav_menu").change(function(){
	picked = $("#nav_menu option:selected").text();
	console.log(picked)
	if(picked === "profile"){
		window.location.href = "http://localhost:5000/myhome/";
	}
	else{
		window.location.href = "http://localhost:5000/logout/";
	}
})
  
}); 