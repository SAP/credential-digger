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
    pageLength: localStorage.hasOwnProperty('sharedPageLength') ? localStorage.getItem("sharedPageLength") : 10,
    processing: false,
    order: [[0, "desc"], [1, "desc"]], // Set default column sorting
    columns: [ // Table columns definition
      {
        data: "scan_active",
        className: 'dt-center scan-status',
        orderSequence: ["asc", "desc"]
      }, {
        data: "last_scan",
        className: 'dt-center last-scan',
        orderSequence: ["desc", "asc"]
      }, {
        data: "url",
        className: "all filename",
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
        document.querySelector('#lenDiscoveries').innerText = json.length;
        document.querySelector('#allDiscoveries').innerText = json.reduce((prev, curr) => prev + curr.lendiscoveries, 0);
        // Map json data before sending it to datatable
        return json.map(item => {
          local_repo = !(item.url.startsWith('http://') || item.url.startsWith('https://'));
          return {
            ...item,
            last_scan: item.last_scan ? timestampToDate(item.last_scan) : 'Never',
            url: `
              <div>
                ${local_repo ?
                `<span class="icon icon-folder_open repo-icon"></span>` :
                `<a target="_blank" href="${item.url}" class="icon icon-github repo-icon"></a>`}
                <span>${item.url}</span>
              </div>`,
            scan_active: item.scan_active ? `
              <span class="icon icon-timelapse warning-color"></span>
            ` : `
              <span class="icon icon-check_circle_outline success-color"></span>`,
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
                <span class="icon icon-delete_outline"></span>
              </button>
            </div>`
          }
        })
      }
    }
  },

    $('#repos-table').on('length.dt', function (e, settings, len) {
      localStorage.setItem('sharedPageLength', len);
    }));

  setInterval(function () {
    $('.dataTable').DataTable().ajax.reload(null, false);
  }, POLLING_INTERVAL);
}

/**
 * Set repository url when deleting a repo
 */
function initDeleteRepo() {
  // Use jQuery for easier event delegation
  $(document).on('click', '.delete-repo-btn', function () {
    const url = this.dataset.url;
    document.querySelector('#deleteRepoModal input[name="repo_url"]').value = url;
  });
}