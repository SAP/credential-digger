/**
 * Handles repository scan's form and interactions.
 */

/** 
 * Register handlers on document ready event 
 */
document.addEventListener("DOMContentLoaded", function () {
  /** Remove error on input's change. */
  $(document).on('change', '.error', function() {
    // Use jQuery for easier event delegation
    this.classList.remove('error');

    const next = this.nextSibling;
    if(next?.classList?.contains('error-message')) next.remove();

    if(!document.querySelector('.error')) {
      // if there are no errors left, enable submit button
      const submitButton = document.querySelector('#startRepoScan');
      submitButton.disabled = false;
      submitButton.classList.remove('disabled');
    }
  });
});

/** 
 * Initialization of the form's event handlers 
 */
function initScanRepo() {
  const rulesSelect = document.querySelector('#ruleSelector');
  const rulesCheckbox = document.querySelector('#cbAllRules');

  /** 
   * Add listener to start repo scan: when the form is submitted, if it is 
   * valid start the scan
   */
  document.querySelector('#scan_repo').addEventListener('submit', function (e) {
    const formValid = validateForm();
    e.preventDefault();
    if(!formValid) return;

    $.ajax({
      url: '/scan_repo',
      method: 'POST',
      data: $(this).serialize(),
      beforeSend: function() {
        const scanBtn = document.querySelector('#startRepoScan');
        scanBtn.classList.add('disabled');
        scanBtn.disabled = true;
        scanBtn.insertAdjacentHTML('beforeend', '<div class="loaderWrapper"><div class="loader"></div></div>');
      },
      success: function() {
        // close popup and open ok modal
        document.querySelector('#addRepoModal').classList.remove('open');
        
        const scanBtn = document.querySelector('#startRepoScan');
        scanBtn.classList.remove('disabled');
        scanBtn.disabled = false;
        scanBtn.querySelector('.loaderWrapper').remove();

        document.querySelector('#scan_repo')?.reset();
        if($('#repos-table')) $('#repos-table').DataTable().ajax.reload();
        if(document.querySelector('#newScan')) {
          getScan();
          scanInterval = setInterval(getScan, POLLING_INTERVAL);
        }
      },
      statusCode: {
        401: function() {
          addError(document.querySelector('#gitTokenInput'), 'Git token not valid');
          const scanBtn = document.querySelector('#startRepoScan');
          scanBtn.classList.remove('disabled');
          scanBtn.disabled = false;
          scanBtn.querySelector('.loaderWrapper').remove();
        }
      }
    });
  }, true);

  /** 
   * Add listener to repo category selector: uncheck he 'Use all rules' 
   * checkbox when a category is being manually selected
   */
  rulesSelect.addEventListener('change', function () {
    if(rulesSelect.selectedIndex != -1) rulesCheckbox.checked = false;
  });

  /** 
   * Add listener to checkbox that selects all the rules: remove selection of
   * the rules select if this checkbox is checked
   */
  rulesCheckbox.addEventListener('change', function () {
    rulesSelect.selectedIndex = -1;
    rulesSelect.dispatchEvent(new Event('change', { 'bubbles': true }))
  });
}

/**
 * Check if form is filled correctly and handle change
 */
function validateForm() {
  // Get HTML elements
  const cBox = document.querySelector('#cbAllRules');
  const rulesList = document.querySelector('#ruleSelector');
  const repoLink = document.querySelector('#repoLinkInput');
  // Check if repo link is a valid url
  const urlValid = repoLink.value.match(/(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/g);
  // Check whether the form is correctly filled or not
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

/**
 * Add error class and error message to input
 * @param {HTMLNode} input HTML input node
 * @param {String} tooltip Error message to show below the input field
 */
function addError(input, tooltip = '') {
  input.classList.add('error');

  if(!tooltip) return;
  if(!input.nextSibling?.classList?.contains('error-message'))
    input.insertAdjacentHTML('afterend', `<div class="error-message">${tooltip}</div>`);
}
