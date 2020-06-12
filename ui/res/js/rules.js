var deleteRuleButtons = document.getElementsByClassName('deleteRule');
// check no entry exception
checkResultsCount();
// check no rules exception
function checkResultsCount() {
  // get all rules from ui
  var rules = document.getElementsByClassName('ruleEntry');
  // set up rules shown counter
  var resultsCounter = 0;
  // step trough all the rules
  for (var i = 0; i < rules.length; i++) {
    // if rule is shown increase repo shown counter
    if (rules[i].style.display != 'none') {
      resultsCounter++;
    }
  }
  // if rule shown counter is 0 (no rules displayed) show no rules found exception
  if (resultsCounter == 0) {
    document.getElementById('noEntries').style.display = 'block';
  // else hide exception
  } else {
    document.getElementById('noEntries').style.display = 'none';
  }
}
// add expand entry
// get all table rows
var tableRows = document.getElementsByClassName('tableRowContent');
// add action listeners to table rows
for (var i = 0; i < tableRows.length; i++) {
  tableRows[i].addEventListener('mouseover', function(event) {
    // open expand table row
    openExpandTableRow(event.currentTarget);
  });
}
// add action listener to table on mouse leave
document.getElementById('rulesTable').addEventListener('mouseleave', function(event) {
  // close expandTableRow
  openExpandTableRow(null);
});

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
      tableRows[i].style.background = '#f5f5f5'
      for (var j = 0; j < tableRows[i].children.length; j++) {
        tableRows[i].children[j].children[0].style.borderBottomColor = '#f5f5f5'
      }
      // else hide
    } else {
      expandTableRows[i].style.display = 'none';
      tableRows[i].style.background = 'transparent';
      for (var j = 0; j < tableRows[i].children.length; j++) {
        tableRows[i].children[j].children[0].style.borderBottomColor = '#9e9e9e'
      }
    }
  }
}

// delete rule popup
// add action listener to delete rule buttons
var deleteRuleButtons = document.getElementsByClassName('deleteRule');
for (var i = 0; i < deleteRuleButtons.length; i++) {
  deleteRuleButtons[i].addEventListener('click', function(event) {
    // find the'right popup modal
    for (var i = 0; i < deleteRuleButtons.length; i++) {
      if (event.target == deleteRuleButtons[i]) {
        // show popup
        document.getElementsByClassName('deleteRuleModal')[i].style.display = 'block';
      }
    }
  });
}

// add action listener for window (clicking anywhere)
window.addEventListener('click', function(event) {
  // if user clicked in the modal area (area around the popup) hide popup
  var deleteRuleModals = document.getElementsByClassName('deleteRuleModal');
  for (var i = 0; i < deleteRuleModals.length; i++) {
    if (deleteRuleModals[i] == event.target) {
      deleteRuleModals[i].style.display = 'none';
      break;
    }
  }
});

// add action listeners to close delete rule popup buttons
var closeDeleteRuleButtons = document.getElementsByClassName('cancelDeleteRule');
var deleteRuleModals = document.getElementsByClassName('deleteRuleModal');
for (var i = 0; i < closeDeleteRuleButtons.length; i++) {
  closeDeleteRuleButtons[i].addEventListener('click', function(event) {
    // close all popup modals
    for (var i = 0; i < deleteRuleModals.length; i++) {
      deleteRuleModals[i].style.display = 'none';
    }
  });
}


// upload rule popup
// add action listener to upload rule button
document.getElementById('uploadRule').addEventListener('click', function(event) {
  // show popup
  document.getElementById('uploadRuleModal').style.display = 'block';
});


document.getElementById('addrule').addEventListener('click', function(event) {
  // show popup
  document.getElementById('addrulepop').style.display = 'block';
});

window.addEventListener('click', function(event) {
  // if user clicked in the modal area (area around the popup) hide popup
  if (event.target == document.getElementById('addrulepop')) {
    closeAddRule();
  }
});

document.getElementById('cancelAddRule').addEventListener('click', function(event) {
  closeAddRule();
});

// add action listener for window (clicking anywhere)
window.addEventListener('click', function(event) {
  // if user clicked in the modal area (area around the popup) hide popup
  if (event.target == document.getElementById('uploadRuleModal')) {
    closeUploadRule();
  }
});

// add action listener to close upload rule popup
document.getElementById('cancelUploadRule').addEventListener('click', function(event) {
  closeUploadRule();
});

// add action listener for folder name input bar
document.getElementById('file').addEventListener('change', function(event) {
  if (event.target.value != '') {
    document.getElementById('path').innerHTML = event.target.value;
    document.getElementById('startUploadRule').disabled = false;
  }
});

// close upload rule pop up
function closeUploadRule() {
  // hide popup
  document.getElementById('uploadRuleModal').style.display = 'none';
  // reset popup
  document.getElementById('path').innerHTML = 'No File Selected';
  document.getElementById('startUploadRule').disabled = true;
}

function closeAddRule() {
  // hide popup
  document.getElementById('addrulepop').style.display = 'none';
  // reset input
  document.getElementById('regexInput').value = '';
  document.getElementById('catInput').value = '';
  document.getElementById('descInput').value = '';
}
