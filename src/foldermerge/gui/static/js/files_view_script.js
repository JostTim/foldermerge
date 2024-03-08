document.querySelectorAll('.folder').forEach(function (folder) {

    folder.classList.toggle('open', true);
    // content = this.nextElementSibling.style.display = 'block'
    /* Change true to false and 'none' to 'block' to be unfolded or folder by default */

    folder.addEventListener('click', function () {
        this.classList.toggle('open');
    });
});

document.addEventListener('DOMContentLoaded', function() {
    var hintTargets = document.querySelector('.hint-target');
    var hintBox = document.getElementById('hintBox');

    hintTargets.forEach(function (hintTarget){

        hintTarget.addEventListener('mouseenter', function(e) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/hint', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                    hintBox.innerHTML = this.responseText;
                    hintBox.style.display = 'block';
                }
            };
            xhr.send(JSON.stringify({ 'id': 'example' }));
        });

        hintTarget.addEventListener('mouseleave', function() {
            hintBox.style.display = 'none';
        });
    
        hintTarget.addEventListener('mousemove', function(e) {
            moveHintBox(e);
        });

    });
    
    function moveHintBox(e) {
        var mouseX = e.pageX;
        var mouseY = e.pageY;
        hintBox.style.top = (mouseY + 10) + 'px';
        hintBox.style.left = (mouseX + 10) + 'px';
    }
});