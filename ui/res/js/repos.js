/**
 * Handles all interactions in the repos page.
 */

/**
 * Register handlers on document ready event
 */
document.addEventListener("DOMContentLoaded", function () {
  initReposDataTable();
  initScanRepo();
  initDeleteRepo();
  initModals();
});

/**
 * Initialize DataTable plugin on the page's table
 */
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
            actions: `
            <div class="btns-container">
              <div class="btn-group">
                <a class="btn outline-bg" href="/files?url=${item.url}">
                  <span class="icon icon-folder_open"></span><span>Files view</span>
                </a>
                <div class="dropdown-container">
                  <div class="dropdown-opener outline-bg">
                    <span class="icon icon-keyboard_arrow_down"></span>
                  </div>
                  <div class="dropdown">
                    <a class="btn outline-bg" href="/discoveries?url=${item.url}">
                      <span class="icon icon-error_outline"></span><span>Discoveries view</span>
                    </a>
                  </div>
                </div>
              </div>
              <button class="btn danger-bg modal-opener delete-repo-btn" data-url="${item.url}" data-modal="deleteRepoModal">
                <span class="icon icon-delete_outline"></span><span>Delete Repo</span>
              </button>
            </div>`
          }
        })
      }
    },
  });
}

/**
 * Set repository url when deleting a repo
 */
function initDeleteRepo() {
  // Use jQuery for easier event delegation
  $(document).on('click', '.delete-repo-btn', function() {
    const url = this.dataset.url;
    document.querySelector('#deleteRepoModal input[name="repo_url"]').value = url;
  });
}