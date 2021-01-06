/**
 * Handles all interactions in the repos page.
*/

/**
 * Register handlers on document ready event
 */
document.addEventListener("DOMContentLoaded", function () {
  if (document.querySelector('#rules-table')) initRulesDataTable();
  initRules();
});

/**
 * Initialize DataTable plugin on the page's table
 */
function initRulesDataTable() {
  $('#rules-table').DataTable({
    ...defaultTableSettings,
    order: [[1, "desc"]], // Set default column sorting
  });
}

/**
 * Handle all interactions of page
 */
function initRules() {
  document.querySelectorAll('.deleteRule').forEach(node => {
    node.addEventListener('click', function() {
      const tr = node.closest('tr');
      const ruleId = node.dataset.ruleid;
      const ruleRegex = tr.querySelector('.rule-regex').textContent;
      document.querySelector('#rule-regex').textContent = ruleRegex;
      document.querySelector('#rule-id').value = ruleId;
    });
  }); 

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