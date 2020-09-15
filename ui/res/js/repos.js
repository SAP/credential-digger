
let listOfRepos;
window.onload = function () {
  listOfRepos = document.getElementsByClassName('repo tableRowContent');
  checkFormFilled();
};

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