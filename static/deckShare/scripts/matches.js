document.addEventListener('DOMContentLoaded', function(event) {

	if ( window.history.replaceState ) {
        window.history.replaceState( null, null, window.location.href );
    }

	let friendsForm = document.getElementById('friendsForm')
	let requestFriendsBtns = document.querySelectorAll('.requestFriends')
	let acceptFriendsBtns = document.querySelectorAll('.acceptFriends')
	let prevBtn = document.querySelector('.prevPage')
	let nextBtn = document.querySelector('.nextPage')

	// Get page number from url
	let splitUrl = window.location.pathname.split("/")
	let pageNum = parseInt(splitUrl.pop())


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

	prevBtn.onclick = function ()  {
		pageNum --;
		splitUrl.push(pageNum.toString())
		let url = splitUrl.join("/")
		window.location.replace(url)
	}

	nextBtn.onclick = function ()  {
		pageNum ++;
		splitUrl.push(pageNum.toString())
		let url = splitUrl.join("/")
		window.location.replace(url)
	}


});