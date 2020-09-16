
/**
 * @description An enum-like type to represent errors.
 * - URL: The URL is invalid.
 * - CATEGORY: The user must select one category.
 */
const Errors = Object.freeze({ "URL": 1, "CATEGORY": 2 });

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