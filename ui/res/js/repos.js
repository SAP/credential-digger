// add search action listener
document.getElementById('search').addEventListener('input', function(event) {
  search(this.value);
});

// add repo pop up
// add action listener to add repo button
document.getElementById('addRepo').addEventListener('click', function(event) {
  // show popup
  document.getElementById('addRepoModal').style.display = 'block';
});

// add action listener for window (clicking anywhere)
window.addEventListener('click', function(event) {
  // if user clicked in the modal area (area around the popup) hide popup
  if (event.target == document.getElementById('addRepoModal')) {
    closeAddRepo();
  }
});

// add action listener to close add repo popup
document.getElementById('cancelAddRepo').addEventListener('click', function(event) {
  // close popup
  closeAddRepo();
});

// add action listener to start repo scan
document.getElementById('startRepoScan').addEventListener('click', function(event) {
  // close popup
  document.getElementById('addRepoModal').style.display = 'none';
  // show loading popup
});

// add action listener to repo url input
document.getElementById('repoLinkInput').addEventListener('input', function(event) {
  // check if form is correctly filled
  checkFormFilled();
});

// add action listener to repo scan config selector
document.getElementById('configSelector').addEventListener('change', function(event) {
  // check if forenameFolderModalrm is correctly filled
  checkFormFilled();
});

// check if form is filled correctly and handle change
function checkFormFilled() {
  // get post repo scan button and form values
  var postAddRepoButton = document.getElementById('startRepoScan');
  var repoLink = document.getElementById('repoLinkInput').value;
  var config = document.getElementById('configSelector').value;
  // check if repo link is a valid url
  var urlValid = repoLink.match(/(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/g);
  // enable submit button if url is valid and config is set
  if (urlValid && config != '') {
    postAddRepoButton.disabled = false;
    postAddRepoButton.classList.remove('disabledButton');
    // else disable submit
  } else {
    postAddRepoButton.disabled = true;
    postAddRepoButton.classList.add('disabledButton');
  }
}

// close add repo pop up
function closeAddRepo() {
  // hide popup
  document.getElementById('addRepoModal').style.display = 'none';
  // reset input
  document.getElementById('repoLinkInput').value = '';
  document.getElementById('ruleSelector').value = '';
  document.getElementById('configSelector').checked = false;
  checkFormFilled();
}
