/**
 * URL: The URL is invalid.
 * CATEGORY: The user must select one category.
 */
const Errors = Object.freeze({ "URL": 1, "CATEGORY": 2 });

// add search action listener
document.getElementById('search').addEventListener('input', function () {
  search(this.value);
});

// add repo pop up
// add action listener to add repo button
document.getElementById('addRepo').addEventListener('click', function () {
  // show popup
  document.getElementById('addRepoModal').style.display = 'block';
});

// add action listener for window (clicking anywhere)
window.addEventListener('click', function (event) {
  // if user clicked in the modal area (area around the popup) hide popup
  if (event.target == document.getElementById('addRepoModal')) {
    closeAddRepo();
  }
});

// add action listener to close add repo popup
document.getElementById('cancelAddRepo').addEventListener('click', closeAddRepo());

// add action listener to start repo scan
document.getElementById('startRepoScan').addEventListener('click', function () {
  // close popup
  document.getElementById('addRepoModal').style.display = 'none';
  // show loading popup
});

document.getElementById('ruleSelector').addEventListener('change', checkFormFilled);

// add action listener to repo url input
document.getElementById('repoLinkInput').addEventListener('input', checkFormFilled);

// add action listener to repo scan config selector
document.getElementById('cbAllRules').addEventListener('change', checkFormFilled);


/**
 * Check if form is filled correctly and handle change
 */

function checkFormFilled() {
  // get post repo scan button and form values
  let cBox = document.getElementById('cbAllRules');
  let rulesList = document.getElementById('ruleSelector');
  let repoLinkContainer = document.getElementById('repoLinkInput');
  let repoLink = repoLinkContainer.value;
  // check if repo link is a valid url
  let urlValid = repoLink.match(/(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/g);
  // enable submit button if url is valid
  if (urlValid || cBox.checked || rulesList.selectedIndex != -1) {
    editForm(true);
  }
  if (urlValid == null) {
    editForm(false, Errors.URL, 'The URL you have provided is invalid.');
    return;
  }
  if (cBox.checked == true || rulesList.selectedIndex == -1) {
    editForm(false, Errors.CATEGORY, 'Please select a category first.');
    return;
  }

}

/**
 * A function to enable/disable the scan button and highlight alarming sections.
 * @param {boolean} enable 
 * True: Enables the button | False: Disables the button
 * @param {string} tooltip 
 * (Optional) Shows an error message when the mouse hovers on the disabled button
 */
function editForm(enable, err, tooltip = '') {
  let postAddRepoButton = document.getElementById('startRepoScan');
  let repoLinkContainer = document.getElementById('repoLinkInput');
  let rulesList = document.getElementById('ruleSelector');
  postAddRepoButton.disabled = !enable;
  postAddRepoButton.title = tooltip;
  if (enable) {
    postAddRepoButton.classList.remove('disabledButton');
    repoLinkContainer.style.border = '1px solid black';
    rulesList.style.border = '1px solid black';
  } else {
    postAddRepoButton.classList.add('disabledButton');
    switch (err) {
      case Errors.URL:
        repoLinkContainer.style.border = '2px solid red';
        break;
      case Errors.CATEGORY:
        rulesList.style.border = '2px solid red';
        break;
    }
  }
}

// close add repo pop up
function closeAddRepo() {
  // hide popup
  document.getElementById('addRepoModal').style.display = 'none';
  // reset input
  document.getElementById('repoLinkInput').value = '';
  document.getElementById('ruleSelector').value = '';
  document.getElementById('cbAllRules').checked = false;
  document.getElementById('cbSnippetModel').checked = false;
  document.getElementById('cbAllRules').checked = false;
}

