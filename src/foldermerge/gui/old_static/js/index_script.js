function removeInputWithAnimation(inputElement) {
    var folder_id = parse_compared_folder_number(inputElement);
    var container = document.getElementById('container@compared_folder_' + folder_id);
    console.log(folder_id);
    container.classList.add("delete_ongoing"); // Apply the slide-up animation
    container.classList.remove("first_compared_folder");
    container.classList.remove("no_animation_input");
    container.addEventListener('animationend', function () {
        container.remove(); // Remove the element after the animation ends
        // document.getElementById('compared_folder_' + folder_id).remove();
        // document.getElementById('blobs@compared_folder_' + folder_id).remove();
        // document.getElementById('container@compared_folder_' + folder_id).remove();
    });
}

function parse_compared_folder_number(folder) {
    var folder_id = folder.id
    if (folder.id.includes("@")) {
        folder_id = folder_id.split("@")[1]
    }
    return parseInt(folder_id.split('_').pop(), 10);
}

function create_compared_folder_field(folder_int_id) {

    var compared_folders_list = document.getElementById('compared_folders_list');

    var container = document.createElement('div');
    container.className = "margin_container";
    container.id = "container@compared_folder_" + folder_int_id;

    var textarea = document.createElement('textarea');
    textarea.id = 'input@compared_folder_' + folder_int_id;
    textarea.className = 'editable-path compared_folder';
    textarea.setAttribute('contenteditable', 'true');
    textarea.setAttribute('placeholder', 'Enter a compared folder path here');
    textarea.setAttribute('spellcheck', 'false');
    // textarea.setAttribute('oninput', 'handleComparedFolderInput(event)');
    // textarea.setAttribute('onkeypress', 'validatePathInput(event)');
    textarea.addEventListener('input', handleComparedFolderInput);
    textarea.addEventListener('keypress', validatePathInput);

    var hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.className = 'compared_folder_hidden_val';
    hiddenInput.name = 'compared_folder_' + folder_int_id;
    hiddenInput.id = 'compared_folder_' + folder_int_id;

    var hiddenRootInput = document.createElement('input');
    hiddenRootInput.type = 'hidden';
    hiddenRootInput.className = 'compared_folder_rel_root_val';
    hiddenRootInput.name = 'rel_root@compared_folder_' + folder_int_id;
    hiddenRootInput.id = 'rel_root@compared_folder_' + folder_int_id;

    var blobsContainer = document.createElement('div');
    blobsContainer.id = 'blobs@compared_folder_' + folder_int_id;
    blobsContainer.className = 'blobs-container';

    textarea.addEventListener('blur', on_input_blur);
    blobsContainer.addEventListener('click', on_input_focus);

    container.appendChild(textarea);
    container.appendChild(hiddenInput);
    container.appendChild(hiddenRootInput);
    container.appendChild(blobsContainer);

    compared_folders_list.appendChild(container);
};

function handleComparedFolderInput(event) {
    const inputList = document.querySelectorAll('.compared_folder');
    const lastInput = inputList[inputList.length - 1];

    // Check if we need to add a new input field
    if (event.target === lastInput && lastInput.value.trim() !== '') {
        var newInput = create_compared_folder_field(parse_compared_folder_number(lastInput) + 1);
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
    var regex = /^[^\*?"<>|]*$/;

    // Check if the current character is allowed
    if (!regex.test(event.key) && event.key !== 'Backspace' && event.key !== 'Tab') {
        // Prevent the character from being input
        event.preventDefault();
    }
}

function concatenateComparedFolders() {

    var comparedFolders = Array.from(document.getElementsByClassName('margin_container'));


    // var comparedFolders = Array.from(document.getElementsByClassName('compared_folder_hidden_val'));
    // Sort inputs by the number in their name attribute
    comparedFolders.sort((a, b) => {
        const numA = parseInt(a.id.split('_')[2], 10);
        const numB = parseInt(b.id.split('_')[2], 10);
        return numA - numB;
    });
    // Join non-empty values with '*' separator

    function get_elements(folder_container) {
        var compared_folder = folder_container.getElementsByClassName('compared_folder_hidden_val')[0].value.trim()
        var root_folder = folder_container.getElementsByClassName('compared_folder_rel_root_val')[0].value.trim()

        if (compared_folder !== '') {
            results_comparedFolders.push(compared_folder);
            results_rootFolders.push(root_folder);
        }
    }

    var results_comparedFolders = Array()
    var results_rootFolders = Array()

    comparedFolders.forEach(get_elements);

    document.getElementById('compared_folders').value = results_comparedFolders.join('*');
    document.getElementById('compared_rel_roots').value = results_rootFolders.join('*');
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

    var ref_folder = document.getElementById("input@reference_folder");
    ref_folder.addEventListener('keypress', validatePathInput);

    // render blobs if fields are pre-filled
    comparedFolders.forEach(function (inputElement) {
        var event = new Event('blur');
        inputElement.dispatchEvent(event);
    });
    var event = new Event('blur');
    ref_folder.dispatchEvent(event);

    if (flashMessages.length > 0) {
        flashMessages.forEach(function (flash) {
            if (flash[0] === 'error') {
                console.log("Showing 1 flash")
                showToast(flash[1]);
            }
        });
    }
});

const editable_inputs = document.querySelectorAll('.editable-path');

editable_inputs.forEach(AddInputListeners);

function AddInputListeners(input_container) {

    var input_id = input_container.id.split("@")[1];
    var blobsContainer = document.getElementById('blobs@' + input_id);

    input_container.addEventListener('blur', on_input_blur);
    blobsContainer.addEventListener('click', on_input_focus);
}

function on_input_blur() {
    var input_container = this;
    var input_id = input_container.id.split("@")[1];

    var blobsContainer = document.getElementById('blobs@' + input_id);
    var hiddenInput = document.getElementById(input_id);

    var pathValue = input_container.value.trim();
    console.log(pathValue);

    // Update the hidden field with the raw path
    hiddenInput.value = pathValue;

    var hiddenroot = document.getElementById('rel_root@' + input_id);

    if (hiddenroot != null) {
        hiddenroot.value = "";
    }


    // Split the path into segments
    var pathSegments = pathValue.split(/[\\/]+/).filter(Boolean);

    var slash_char = "";
    if (pathValue.includes("/")) {
        slash_char = "/"
    }
    else if (pathValue.includes("\\")) {
        slash_char = "\\"
    }

    // Clear existing blobs
    blobsContainer.innerHTML = '';

    pathSegments.forEach(function (segment, index) {
        var blob = document.createElement('span');
        blob.className = 'blob';
        blob.textContent = segment;
        blob.joinedPath = pathSegments.slice(0, index + 1).join(slash_char);
        blob.input_id = input_id
        blob.position = index
        blob.addEventListener('click', on_blob_click);
        if (blobsContainer.innerHTML != '') {
            var slash = document.createElement('span');
            slash.textContent = slash_char;
            slash.className = 'slash';
            blobsContainer.appendChild(slash);
        }
        blobsContainer.appendChild(blob);
    });

    // Hide the editable path and show the blobs container
    if (input_container.value.trim() != "") {
        var container = document.getElementById('container@' + input_id);
        if (container != null) {
            container.classList.add("no_animation_input");
        }

        input_container.style.display = 'none';
        blobsContainer.style.display = 'block';
    }
}

function on_input_focus() {
    var blobsContainer = this;
    var input_container = document.getElementById('input@' + blobsContainer.id.split("@")[1]);
    blobsContainer.style.display = 'none';
    input_container.style.display = 'block';
    input_container.focus();
}

function on_blob_click(event) {
    var blob = this;
    console.log(blob.joinedPath);

    var hiddenroot = document.getElementById('rel_root@' + blob.input_id);

    if (hiddenroot != null) {

        hiddenroot.value = blob.joinedPath;

        var blob_container = document.getElementById('blobs@' + blob.input_id);
        var blobs = blob_container.querySelectorAll('.blob');
        blobs.forEach(function (b) {
            b.classList.remove('selected');
        });
        blobs.forEach(function (b) {
            if (b.position <= blob.position) {
                b.classList.add('selected');
            }
        });
    }
    event.stopPropagation();
}