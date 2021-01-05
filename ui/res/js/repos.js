document.addEventListener("DOMContentLoaded", function () {
  initReposDataTable();
  initScanRepo();
  initDeleteRepo();
  initModals();
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

function initDeleteRepo() {
  // Use jQuery for easier event delegation
  $(document).on('click', '.delete-repo-btn', function() {
    const url = this.dataset.url;
    document.querySelector('#deleteRepoModal input[name="repo_url"]').value = url;
  });
}