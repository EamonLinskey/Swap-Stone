document.addEventListener("DOMContentLoaded", function(event) {
	document.querySelector('.updateCollection').onclick = function() {
		location.href="profile/updateCollection"
	}

	document.querySelector('.wishList').onclick = function() {
		location.href="profile/wishList"
	}

	document.querySelector('.matches').onclick = function() {
		location.href="profile/matches"
	}

	document.querySelector('.generous').onclick = function() {
		location.href="profile/generous"
	}

});