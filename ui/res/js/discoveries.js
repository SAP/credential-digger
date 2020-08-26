//var categoryToggleButtons = [];
//var discoveries = [];
//var requests = [];
var filterFPs = false;

// It is mandatory to wait for the window to load before executing the
// scripts 
window.onload = function () {
  filterFPs = sessionStorage.getItem('filterFPs');
  if (filterFPs == true) {
    toggleFPs();
  }
};

var tableRows = document.getElementsByClassName('tableRowContent');
// add action listeners to table rows
for (var i = 0; i < tableRows.length; i++) {
  tableRows[i].addEventListener('mouseover', function (event) {
    // open expand table row
    openExpandTableRow(event.currentTarget);
  });
}

function openExpandTableRow(tr) {
  // get all hidden expand table rows
  var expandTableRows = document.getElementsByClassName('expandTableRow');
  // get all table rows
  var tableRows = document.getElementsByClassName('tableRowContent');
  // step trough all expand table rows
  for (var i = 0; i < expandTableRows.length; i++) {
    // show if mouseover
    if (tr == tableRows[i]) {
      expandTableRows[i].style.display = 'table-cell';
      tableRows[i].style.background = '#f5f5f5';
      /*
      var markedSnippet = discovery[i].Snippet.replace(discovery[i].Content, '<span class="highlightedCode">' + discovery[i].Content + '</span>')
      document.getElementsByClassName('snippetCodeCell')[i].innerHTML = markedSnippet;
      // load additional data for snippet row
      setSnippetRow(document.getElementsByClassName('expandTableRow')[i], discovery[i]);
      */
    } else {
      // hide if not mouseover
      expandTableRows[i].style.display = 'none';
      tableRows[i].style.background = 'transparent';
    }
  }
}


// delete repo popup
// add action listener to delete repo button
document.getElementById('deleteRepo').addEventListener('click', function (event) {
  // show popup
  document.getElementById('deleteRepoModal').style.display = 'block';
});
// add action listener for window (clicking anywhere)
window.addEventListener('click', function (event) {
  // if user clicks in the modal area (area around the popup) hide popup
  if (event.target == document.getElementById('deleteRepoModal')) {
    document.getElementById('deleteRepoModal').style.display = 'none';
  }
});
document.getElementById('cancelDeleteRepo').addEventListener('click', function (event) {
  // hide popup
  document.getElementById('deleteRepoModal').style.display = 'none';
});


// New scan
// add action listener to scan repo button
document.getElementById('newScan').addEventListener('click', function (event) {
  // Show popup
  document.getElementById('addRepoModal').style.display = 'block';
});
// Add action listener for window (clicking anywhere)
window.addEventListener('click', function (event) {
  // if user clicks in the modal area (area around the popup) hide popup
  if (event.target == document.getElementById('addRepoModal')) {
    closeAddRepo();
  }
});
// add action listener to close scan repo popup
document.getElementById('cancelAddRepo').addEventListener('click', function (event) {
  // close popup
  closeAddRepo();
});
// add action listener to start repo scan
document.getElementById('startRepoScan').addEventListener('click', function (event) {
  // close popup
  document.getElementById('addRepoModal').style.display = 'none';
  // show loading popup
});
// add action listener to repo scan config selector
document.getElementById('cbAllRules').addEventListener('change', function (event) {
  // check if form is correctly filled
  var config = document.getElementById('cbAllRules').value;
  var postAddRepoButton = document.getElementById('startRepoScan');
  if (config != '') {
    postAddRepoButton.disabled = false;
    postAddRepoButton.classList.remove('disabledButton');
    // else disable submit
  } else {
    postAddRepoButton.disabled = true;
    postAddRepoButton.classList.add('disabledButton');
  }
});
// close scan repo pop up
function closeAddRepo() {
  // hide popup
  document.getElementById('addRepoModal').style.display = 'none';
  // reset input
}

var allDiscoveries = document.getElementsByClassName('discoveryEntry');
// Show/hide fp flag
function switchFilter() {
  //Swap the value of the filtering FLAG
  filterFPs = filterFPs ^ 1;
  //Store the flag's value as long as the session is still running
  sessionStorage.setItem('filterFPs', filterFPs);
  // Change color
  document.getElementById('showFPs').style.backgroundColor = '#0000ff';
  // Filter discoveries
  toggleFPs();
}

function toggleFPs() {
  let countDiscoveries = 0;
  for (let i = 0; i < allDiscoveries.length; i++) {
    // If the discovery is not new, hide its row and the expandable one
    if (allDiscoveries[i].children[2].valueOf().innerText == 'false_positive') {
      allDiscoveries[i].style.display = filterFPs ? 'none' : '';
      countDiscoveries++;
    }
  }
  document.getElementById('showFPs').innerHTML = filterFPs ? 'Show FPs' : 'Hide FPs';
  document.getElementById('discoveriesCounter').innerHTML = filterFPs ?
    `${allDiscoveries.length} discoveries found (${countDiscoveries} false positives are hidden)` :
    `${allDiscoveries.length} discoveries found`;
}
