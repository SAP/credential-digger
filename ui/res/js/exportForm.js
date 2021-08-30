function changeAll() {
    let checkBoxes = document.getElementsByName('check');
    for (let i = 0; i < checkBoxes.length; i++) {
        const cb = checkBoxes[i];
        cb.checked = !$('#cbAll').prop('checked');
    }
}

function alternateCheckBoxes() {
    let checkBoxes = document.getElementsByName('check');
    for (let i = 0; i < checkBoxes.length; i++) {
        let cb = checkBoxes[i];
        if (cb.checked) {
            $('#cbAll').prop('checked', false);
            return;
        }
    }
}