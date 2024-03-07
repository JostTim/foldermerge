
function dropHandler(ev) {
    ev.preventDefault();

    if (ev.dataTransfer.items && ev.dataTransfer.items[0].webkitGetAsEntry().isDirectory) {
        var folder = ev.dataTransfer.items[0].getAsFile();
        $('#reference_folder').val(folder.name);
    }
}

function dragOverHandler(ev) {
    ev.preventDefault();
}

function folderChangeHandler(ev) {
    var files = ev.target.files;
    if (files.length) {
        // Assuming single folder selection, take the first file's path
        // Remove the file name (last part of the path) to get the folder path
        var folderPath = files[0].webkitRelativePath.split('/').slice(0, -1).join('/');
        $('#reference_folder').val(folderPath);
    }
}

function removeInputWithAnimation(inputElement) {
    inputElement.style.animation = 'slideUp 0.3s ease-out forwards'; // Apply the slide-up animation
    inputElement.addEventListener('animationend', function () {
        inputElement.remove(); // Remove the element after the animation ends
    });
}

function handleComparedFolderInput(event) {
    const inputList = document.querySelectorAll('.compared_folder');
    const lastInput = inputList[inputList.length - 1];

    // Check if we need to add a new input field
    if (event.target === lastInput && lastInput.value !== '') {
        const newIndex = parseInt(lastInput.name.split('_').pop(), 10) + 1;
        const newInput = document.createElement('input');
        newInput.type = 'text';
        newInput.name = 'compared_folder_' + newIndex;
        newInput.className = 'input-field compared_folder';
        newInput.placeholder = "Enter a compared folder path here";
        newInput.setAttribute('oninput', 'handleComparedFolderInput(event)');
        newInput.setAttribute('onkeypress', 'validatePathInput(event)');
        document.getElementById('compared_folders_list').appendChild(newInput);
    }

    // Check if we need to remove any input fields
    for (let i = 0; i < inputList.length - 1; i++) {
        if (inputList[i].value === '') { //} && inputList[i + 1].value === '') {
            removeInputWithAnimation(inputList[i]);
            // After removing an element, we need to break as the NodeList is live
        }
    }
}

function validatePathInput(event) {
    // Define a regex pattern for allowed characters in paths
    // This example allows letters, numbers, underscores, hyphens, spaces, and slashes
    var regex = /^[^\*:?"<>|]*$/;

    // Check if the current character is allowed
    if (!regex.test(event.key) && event.key !== 'Backspace' && event.key !== 'Tab') {
        // Prevent the character from being input
        event.preventDefault();
    }
}



function concatenateComparedFolders() {
    var comparedFolders = Array.from(document.getElementsByClassName('compared_folder'));
    // Sort inputs by the number in their name attribute
    comparedFolders.sort((a, b) => {
        const numA = parseInt(a.name.split('_')[2], 10);
        const numB = parseInt(b.name.split('_')[2], 10);
        return numA - numB;
    });
    // Join non-empty values with '*' separator
    var concatenatedPaths = comparedFolders
        .map(input => input.value.trim())
        .filter(value => value !== '')
        .join('*');
    document.getElementById('compared_folders').value = concatenatedPaths;
}

document.querySelector('form').addEventListener('submit', function (event) {
    concatenateComparedFolders();
});


function createToast(message) {
    const toast = document.createElement('div');
    toast.classList.add('toast');
    toast.textContent = message;
    toast.onclick = function () {
        toast.parentNode.removeChild(toast);
    };
    setTimeout(function () {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 10000);
    return toast;
}

function showToast(message) {
    const container = document.getElementById('toast-container');
    const toast = createToast(message);
    container.appendChild(toast);
}


document.addEventListener('DOMContentLoaded', function () {
    var comparedFolders = document.querySelectorAll('#compared_folders_list .compared_folder');

    comparedFolders.forEach(function (input) {
        input.addEventListener('input', handleComparedFolderInput);
        input.addEventListener('keypress', validatePathInput);
    });

    if (flashMessages.length > 0) {
        flashMessages.forEach(function (flash) {
            if (flash[0] === 'error') {
                console.log("Showing 1 flash")
                showToast(flash[1]);
            }
        });
    }
});