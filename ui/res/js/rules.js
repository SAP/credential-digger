document.addEventListener("DOMContentLoaded", function () {
  if (document.querySelector('#rules-table')) initRulesDataTable();
  initRules();
});

function initRulesDataTable() {
  $('#rules-table').DataTable({
    ...defaultTableSettings,
    order: [[1, "desc"]], // Set default column sorting
  });
}

function initRules() {
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
      document.querySelector('#noEntries').style.display = 'block';
    // else hide exception
    } else {
      document.querySelector('#noEntries').style.display = 'none';
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

  // add action listener for folder name input bar
  document.querySelector('#file').addEventListener('change', function(event) {
    if (event.target.value != '') {
      // replace the C:\fakepath\ from the prefix of the path and retrieve the file name only.
      var path = event.target.value.replace(/^.*\\/,"");
      document.querySelector('#path').innerHTML = path;
      document.querySelector('#startUploadRule').disabled = false;
    }
  });

}