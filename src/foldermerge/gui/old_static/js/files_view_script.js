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
    var hoverTimer;
    var mouse_in_hint = false;
    var show_delay = 200; // milliseconds

    hintTargets.forEach(function (hintTarget) {

        function ShowHintAfter1sec(e) {
            console.log("timeout 1sec");

            var matchesValue = hintTarget.getAttribute('data-matches-uuids');
            if (matchesValue === null || JSON.parse(matchesValue).length === 0) {
                return;
            };
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/file_hint', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function () {
                if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
                    moveHintBox(e)
                    hintBox.innerHTML = this.responseText;
                }
            };
            xhr.send(JSON.stringify({ 'uuids': matchesValue }));
        };

        hintTarget.addEventListener('mouseenter', function (e) {
            clearTimeout(hoverTimer);
            console.log("mouse in")

            hoverTimer = setTimeout(function () { ShowHintAfter1sec(e); }, show_delay); // Wait for 1 second before showing the hint
        });

        hintTarget.addEventListener('mouseleave', function (e) {
            console.log("mouse exits")
            clearTimeout(hoverTimer);
            if (!hintBox.contains(e.relatedTarget)) {
                hideHintBox();
            }
        });

        hintTarget.addEventListener('mousemove', function (e) {
            console.log("mouse move reset_timer")
            clearTimeout(hoverTimer);
            if (!mouse_in_hint) {
                hoverTimer = setTimeout(function () { ShowHintAfter1sec(e); }, show_delay); // Reset timer if mouse moves
            }
        });

    });

    function moveHintBox(e) {
        var mouseX = e.pageX;
        var mouseY = e.pageY;
        hintBox.style.display = 'block';
        hintBox.style.top = (mouseY + 5) + 'px';
        hintBox.style.left = (mouseX + 5) + 'px';
    }

    function hideHintBox() {
        hintBox.style.display = 'none';
    }

    hintBox.addEventListener('mouseenter', function () {
        mouse_in_hint = true;
        console.log("mouse entered hint")
        clearTimeout(hoverTimer);
    });

    hintBox.addEventListener('mouseleave', function () {
        mouse_in_hint = false;
        console.log("mouse left hint")
        hideHintBox();
    });

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

function copyToClipboard(target) {
    const path = target.innerText;
    const separator = path.includes('/') ? '/' : '\\';
    const dirname = path.substring(0, path.lastIndexOf(separator) + 1);
    navigator.clipboard.writeText(dirname).then(function () {
        console.log('Path copied to clipboard successfully!');
        target.classList.add('flashing');
        setTimeout(function () {
            target.classList.remove('flashing');
        }, 50);

    }, function (err) {
        console.error('Unable to copy to clipboard', err);
    });
}
