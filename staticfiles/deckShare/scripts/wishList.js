document.addEventListener('DOMContentLoaded', function(event) {

	trashCans = document.querySelectorAll('.trash')
	deleteForm = document.getElementById('deleteForm')
	submitForm = document.getElementById('submitForm')
	
	submitForm.onsubmit = function () {
		console.log("message")
		console.log(document.querySelector(".message"))
		document.querySelector(".message").innerHTML = "Please wait a moment while we find matches <img class='loading' src='/static/deckShare/images/loadingGear.svg' alt='Please Wait'> <div> This may take up to 30 seconds</div>"
	}

	for(let can of trashCans){
		can.onclick = function ()  {
			document.getElementById("deckToDelete").value = can.id
			deleteForm.submit()
		}
	}

});