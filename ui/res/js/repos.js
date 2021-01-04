document.addEventListener("DOMContentLoaded", function () {
  initReposDataTable();
  initAddRepo();
  initDeleteRepo();
  initModals();
});

let listOfRepos;
window.onload = function () {
  listOfRepos = document.getElementsByClassName('repo tableRowContent');
  checkFormFilled();
};

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
        data: "actions",
        orderable: false
      }
    ],
    ajax: { // AJAX source info
      url: "/get_repos",
      dataSrc: function (json) {
        // Map json data before sending it to datatable
        return json.map(item => {
          return {
            ...item,
            actions: reposActionsTemplate(item.url)
          }
        })
      }
    },
  });
}

function initAddRepo() {
  // add action listener to start repo scan
  document.querySelector('#startRepoScan').addEventListener('click', function () {
    // close popup
    document.querySelector('#addRepoModal').classList.remove('open');
    // show loading popup
  });

  // add action listener to repo category selector
  document.querySelector('#ruleSelector').addEventListener('change', function () {
    //Disable the 'Use all rules' checkbox when a category is being manually selected.
    document.querySelector('#cbAllRules').checked = false;
    checkFormFilled();
  });

  // add action listener to repo url input
  document.querySelector('#repoLinkInput').addEventListener('input', checkFormFilled);

  // add action listener to checkbox that selects all the rules
  document.querySelector('#cbAllRules').addEventListener('change', function () {
    //Select no category if this checkbox is 'Active'
    document.querySelector('#ruleSelector').selectedIndex = -1;
    checkFormFilled();
  });
}

function initDeleteRepo() {
  $(document).on('click', '.delete-repo-btn', function() {
    const url = this.dataset.url;
    document.querySelector('#deleteRepoModal input[name="repo_url"]').value = url;
  });
}