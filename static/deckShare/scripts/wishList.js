document.addEventListener('DOMContentLoaded', function(event) {

	trashCans = document.querySelectorAll('.trash')
	deleteForm = document.getElementById('deleteForm')
	
	for(let can of trashCans){
		can.onclick = function ()  {
			document.getElementById("deckToDelete").value = can.id
			deleteForm.submit()
		}
	}
		
});