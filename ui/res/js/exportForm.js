function changeAll() {
  let checkBoxes = document.getElementsByName("check");
  for (let i = 0; i < checkBoxes.length; i++) {
    const cb = checkBoxes[i];
    a_field_id = cb.nextSibling.nextSibling.id;
    a_field_value = document.getElementById(a_field_id).innerHTML;
    if (a_field_value != "(0)") cb.checked = !$("#cbAll").prop("checked");
  }
}

function alternateCheckBoxes() {
  let checkBoxes = document.getElementsByName("check");
  for (let i = 0; i < checkBoxes.length; i++) {
    let cb = checkBoxes[i];
    if (cb.checked) {
      $("#cbAll").prop("checked", false);
      return;
    }
  }
}

/*
    Make sure at least one checkbox is checked
*/
function validateCheckBoxes() {
  let checkBoxes = document.getElementsByName("check");
  for (let i = 0; i < checkBoxes.length; i++) {
    let cb = checkBoxes[i];
    if (cb.checked) {
      document.getElementById("error_msg").hidden = true;
      return true;
    }
  }
  checkbox_All = $("#cbAll").prop("checked");
  document.getElementById("error_msg").hidden = checkbox_All;
  return checkbox_All;
}
