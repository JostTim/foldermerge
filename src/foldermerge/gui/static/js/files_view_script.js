document.querySelectorAll('.folder').forEach(function (folder) {

    folder.classList.toggle('open', true);
    // content = this.nextElementSibling.style.display = 'block'
    /* Change true to false and 'none' to 'block' to be unfolded or folder by default */

    folder.addEventListener('click', function () {
        this.classList.toggle('open');
    });
});