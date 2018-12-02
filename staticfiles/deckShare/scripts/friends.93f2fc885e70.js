document.addEventListener('DOMContentLoaded', function(event) {

	if ( window.history.replaceState ) {
        window.history.replaceState( null, null, window.location.href );
    }

	friendsForm = document.getElementById('friendsForm')
	deleteFriendsBtns = document.querySelectorAll('.deleteFriends')
	acceptFriendsBtns = document.querySelectorAll('.acceptFriends')


	for(let button of deleteFriendsBtns){
		button.onclick = function ()  {
			document.getElementById("deleteFriend").value = button.id
			document.getElementById("acceptFriend").value = ""
			friendsForm.submit()
		}
	}

	for(let button of acceptFriendsBtns){
		button.onclick = function ()  {
			document.getElementById("acceptFriend").value = button.id
			document.getElementById("deleteFriend").value = ""
			friendsForm.submit()
		}
	}

});