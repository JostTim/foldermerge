document.querySelectorAll('.folder').forEach(function (folder) {

    folder.classList.toggle('open', true);
    // content = this.nextElementSibling.style.display = 'block'
    /* Change true to false and 'none' to 'block' to be unfolded or folder by default */

    folder.addEventListener('click', function () {
        this.classList.toggle('open');
    });
});

document.addEventListener('DOMContentLoaded', function () {
    var hintTargets = document.querySelectorAll('.hint-target');
    var hintBox = document.getElementById('hintBox');

    hintTargets.forEach(function (hintTarget) {

        hintTarget.addEventListener('mouseenter', function (e) {
            var matchesValue = hintTarget.getAttribute('data-matches-uuids');
            console.log(matchesValue)
            if (matchesValue === null || JSON.parse(matchesValue).length === 0) {
                return;
            };
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/file_hint', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function () {
                if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                    hintBox.innerHTML = this.responseText;
                    hintBox.style.display = 'block';
                }
            };
            xhr.send(JSON.stringify({ 'uuids': matchesValue }));
        });

        hintTarget.addEventListener('mouseleave', function () {
            hintBox.style.display = 'none';
        });

        hintTarget.addEventListener('mousemove', function (e) {
            moveHintBox(e);
        });

    });

    function moveHintBox(e) {
        var mouseX = e.pageX;
        var mouseY = e.pageY;
        hintBox.style.top = (mouseY + 10) + 'px';
        hintBox.style.left = (mouseX + 10) + 'px';
    }

    var AddInfoButtons = document.querySelectorAll('.toggle-info-button');
    AddInfoButtons.forEach(function (InfoButton) {

        function open_details(e) {

            var next = e.target.parentNode.parentNode.nextElementSibling;
            var isopen = e.target.classList.contains('open')
            while (next && next.classList.contains('additional-info')) {
                if (isopen) {
                    next.style.display = '';
                }
                else {
                    next.style.display = 'none';
                }

                next = next.nextElementSibling;
            }
            e.target.classList.toggle('open');
        };

        InfoButton.addEventListener('click', open_details);
        InfoButton.classList.toggle('open', false);
        InfoButton.dispatchEvent(new Event('click'));

    });


});