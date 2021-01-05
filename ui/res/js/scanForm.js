document.addEventListener("DOMContentLoaded", function () {
  // Use jQuery for easier event delegation
  $(document).on('change', '.error', function() {
    this.classList.remove('error');

    const next = this.nextSibling;
    if(next?.classList?.contains('error-message')) next.remove();

    if(!document.querySelector('.error')) {
      const submitButton = document.querySelector('#startRepoScan');
      submitButton.disabled = false;
      submitButton.classList.remove('disabled');
    }
  });
});

function initScanRepo() {
  const rulesSelect = document.querySelector('#ruleSelector');
  const rulesCheckbox = document.querySelector('#cbAllRules');

  // add action listener to start repo scan
  document.querySelector('#scan_repo').addEventListener('submit', function (e) {
    const formValid = validateForm();
    if(!formValid) {
      e.preventDefault();
      return;
    }

    // close popup
    document.querySelector('#addRepoModal').classList.remove('open');
    // open ok modal
    document.querySelector("#okModal").classList.add('open');
  }, true);

  // add action listener to repo category selector
  rulesSelect.addEventListener('change', function () {
    // Uncheck the 'Use all rules' checkbox when a category is being manually selected.
    if(rulesSelect.selectedIndex != -1) rulesCheckbox.checked = false;
  });

  // add action listener to checkbox that selects all the rules
  rulesCheckbox.addEventListener('change', function () {
    // Select no category if this checkbox is 'Active'
    rulesSelect.selectedIndex = -1;
    rulesSelect.dispatchEvent(new Event('change', { 'bubbles': true }))
  });
}

/**
 * Check if form is filled correctly and handle change
 */
function validateForm() {
  // get HTML elements
  const cBox = document.querySelector('#cbAllRules');
  const rulesList = document.querySelector('#ruleSelector');
  const repoLink = document.querySelector('#repoLinkInput');
  // check if repo link is a valid url
  const urlValid = repoLink.value.match(/(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/g);
  // check whether the form is correctly filled or not.
  let formValid = true;
  if (urlValid == null) {
    formValid = false;
    addError(repoLink, 'The URL you have provided is invalid.');
  }
  if (!cBox.checked && rulesList.selectedIndex == -1) {
    formValid = false;
    addError(rulesList, 'Please select a category first.');
  }

  if(!formValid) {
    const submitButton = document.querySelector('#startRepoScan');
    submitButton.disabled = true;
    submitButton.classList.add('disabled');
  }
  return formValid;
}

function addError(input, tooltip = '') {
  input.classList.add('error');

  if(!tooltip) return;
  if(!input.nextSibling?.classList?.contains('error-message'))
    input.insertAdjacentHTML('afterend', `<div class="error-message">${tooltip}</div>`);
}
