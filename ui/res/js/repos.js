document.addEventListener("DOMContentLoaded", function () {
  initReposDataTable();
});

function initReposDataTable() {
  $('#repos-table').DataTable({
    ...defaultTableSettings,
    order: [[0, "asc"]], // Set default column sorting
    columns: [ // Table columns definition
      {
        data: "url",
        orderSequence: ["asc", "desc"]
      }, {
        data: "lendiscoveries",
        className: "dt-center",
        orderSequence: ["desc", "asc"]
      }, {
        data: "actions"
      }
    ],
    ajax: { // AJAX source info
      url: "/get_repos",
      dataSrc: function (json) {
        // Map json data before sending it to datatable
        return json.map(item => {
          return {
            ...item,
            actions: `
            <div class="btns-container">
              <a class="btn outline-bg" href="/files?url=${item.url}">
                <span class="icon icon-folder_open"></span><span>Files</span>
              </a>
              <a class="btn outline-bg" href="/discoveries?url=${item.url}">
                <span class="icon icon-error_outline"></span><span>Discoveries</span>
              </a>
            </div>`
          }
        })
      }
    },
  });
}

let listOfRepos;
window.onload = function () {
  listOfRepos = document.getElementsByClassName('repo tableRowContent');
  checkFormFilled();
};


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
