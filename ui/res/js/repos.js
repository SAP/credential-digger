/**
 * @description An enum-like type to represent errors.
 * - URL: The URL is invalid.
 * - CATEGORY: The user must select one category.
 */
const Errors = Object.freeze({ "URL": 1, "CATEGORY": 2 });
let listOfRepos;
window.onload = function () {
  listOfRepos = document.getElementsByClassName('repo tableRowContent');
};

checkFormFilled();
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
document.getElementById('cancelAddRepo').addEventListener('click', closeAddRepo);

// add action listener to start repo scan
document.getElementById('startRepoScan').addEventListener('click', function () {
  // close popup
  document.getElementById('addRepoModal').style.display = 'none';
  // show loading popup
});

// add action listener to repo category selector
document.getElementById('ruleSelector').addEventListener('change', function () {
  //Disable the 'Use all rules' checkbox when a category is being manually selected.
  document.getElementById('cbAllRules').checked = false;
  checkFormFilled();
});

// add action listener to repo url input
document.getElementById('repoLinkInput').addEventListener('input', checkFormFilled);

// add action listener to checkbox that selects all the rules
document.getElementById('cbAllRules').addEventListener('change', function () {
  //Select no category if this checkbox is 'Active'
  document.getElementById('ruleSelector').selectedIndex = -1;
  checkFormFilled();
});


/**
 * Check if form is filled correctly and handle change
 */

function checkFormFilled() {
  // get HTML elements
  let cBox = document.getElementById('cbAllRules');
  let rulesList = document.getElementById('ruleSelector');
  let repoLinkContainer = document.getElementById('repoLinkInput');
  let repoLink = repoLinkContainer.value;
  // check if repo link is a valid url
  let urlValid = repoLink.match(/(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/g);
  // check whether the form is correctly filled or not.
  if (urlValid || cBox.checked || rulesList.selectedIndex != -1) {
    editForm(true);
  }
  if (urlValid == null) {
    editForm(false, Errors.URL, 'The URL you have provided is invalid.');
  }
  if (!cBox.checked && rulesList.selectedIndex == -1) {
    editForm(false, Errors.CATEGORY, 'Please select a category first.');
  }

}

/**
 * A function to enable/disable the scan button and highlight alarming sections.
 * @param {boolean} enable Takes two possible values
 * - True: Enables the button
 * - False: Disables the button
 * @param {enum} err Represents the type of error
 * - URL: The URL is invalid.
 * - CATEGORY: The user must select one category.
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

/**
 * Searches for repos that have an URL that contains the __text__ argument.
 * @param {string} text This argument is used to find all the repos that have an URL that matches its value.
 * @param {boolean} hideNotMatching If set to __false__, the matching repos will not be removed from the UI.
 * @returns Returns an object that has two attributes
 * -  __text__: Equals the textual value that has been used to perform the search
 * -  __indices__: An array that contains the indices of the matching repos. These indices can be used to access
 *                the repo from the __listOfRepos__ array.
 */
function search(text, hideNotMatching = true) {
  let listOfMatches = {
    text: text,
    indices: []
  };
  text = text.toLowerCase();
  for (let i = 0; i < listOfRepos.length; i++) {
    let element = listOfRepos[i];
    if (!element.textContent.toLowerCase().includes(text)) {
      if (hideNotMatching) { element.style.display = 'none'; }
    }
    else {
      element.style.display = '';
      listOfMatches.indices.push(i);
    }
  }
  return listOfMatches;
}