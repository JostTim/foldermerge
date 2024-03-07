function submitFormWithValue(folder_selection, file_selection) {
    console.log(folder_selection)
    console.log(file_selection)
    document.getElementById('folder_selection_field').value = folder_selection;
    document.getElementById('files_selection_field').value = file_selection;
    document.querySelector('.vertical_display_container').submit();
}