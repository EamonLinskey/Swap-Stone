document.addEventListener("DOMContentLoaded", function(event) {
	trashCans = document.querySelectorAll('.trash')
	for can in trashCans
		can.onclick = function() {
			console.log(can.id)
		}
});