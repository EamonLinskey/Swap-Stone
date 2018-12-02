document.addEventListener('DOMContentLoaded', function(event) {

	if ( window.history.replaceState ) {
        window.history.replaceState( null, null, window.location.href );
    }

	
	friendsForm = document.getElementById('friendsForm')
	addFriendsBtns = document.querySelectorAll('.addFriends')
	requestFriendsBtns = document.querySelectorAll('.acceptFriends')


	for(let button of requestFriendsBtns){
		button.onclick = function ()  {
			document.getElementById("requestFriend").value = button.id
			document.getElementById("acceptFriend").value = ""
			friendsForm.submit()
		}
	}

	for(let button of acceptFriendsBtns){
		button.onclick = function ()  {
			document.getElementById("acceptFriend").value = button.id
			document.getElementById("requestFriend").value = ""
			friendsForm.submit()
		}
	}

});