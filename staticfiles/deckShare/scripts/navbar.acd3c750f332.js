function updateNavbar() {
    // gets current path
    let current_path = window.location.pathname.split("/")[1]
    
    if (current_path == ""){
        current_path = "index"
    }
    // Remove active tag from prevously selected button
    let prevActive = document.querySelector('.active')
    if (prevActive){
        prevActive.classList.remove("active");
    }
    
    // Adds active tag to the currently selected button
    let active = document.querySelector(`.${current_path}`);
    if (active){
        active.classList.add("active");
    }
}

document.addEventListener("DOMContentLoaded", function(event) {
	updateNavbar()
});