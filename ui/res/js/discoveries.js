/**
 * Handles all interactions in the discoveries pages (files listing, file 
 * detail and discoveries).
 */

/**
 * Register handlers on document ready event
 */
document.addEventListener("DOMContentLoaded", function () {
  if (document.querySelector('#files-table')) initFilesDataTable();
  if (document.querySelector('#discoveries-table')) initDiscoveriesDataTable();
  if (document.querySelector('#addRepoModal')) initScanRepo();
  initUpdateDiscoveries();
  initUpdateScanning();
});

/**
 * Initialize DataTable plugin on the files listing page's table
 */
function initFilesDataTable() {
  const repoUrl = document.querySelector('#repo-url').innerText;
  $('#files-table').DataTable({
    ...defaultTableSettings,
    pageLength: localStorage.hasOwnProperty('sharedPageLength') ? localStorage.getItem("sharedPageLength") : 10,
    order: [[1, "desc"]], // Set default column sorting
    columns: [ // Table columns definition
      {
        data: "file_name",
        className: "filename",
        orderSequence: ["asc", "desc"]
      }, {
        data: "new",
        className: "dt-center",
        orderSequence: ["desc", "asc"]
      }, {
        data: "false_positives",
        className: "dt-center",
        orderSequence: ["desc", "asc"]
      }, {
        data: "addressing",
        className: "dt-center",
        orderSequence: ["desc", "asc"]
      }, {
        data: "not_relevant",
        className: "dt-center",
        orderSequence: ["desc", "asc"]
      }, {
        data: "actions",
        orderable: false
      }
    ],
    ajax: { // AJAX source info
      url: "/get_files",
      data: { url: repoUrl },
      dataSrc: function (json) {
        document.querySelector('#discoveriesCounter').innerText = json
          .reduce((prev, curr) => prev + curr.tot_discoveries, 0);
        // Map json data before sending it to datatable
        return json.map(item => {
          return {
            ...item,
            file_name: `
            <a href="/discoveries?url=${repoUrl}&file=${encodeURIComponent(item.file_name)}">
              ${item.file_name}
            </a>`,
            actions: discoveriesBtnGroupTemplate("Mark all as")
          }
        });
      }
    }
  });

  $('#files-table').on('length.dt', function (e, settings, len) {
    localStorage.setItem('sharedPageLength', len);
  });
}

/**
 * Initialize DataTable plugin on the file detail and discoveries page's table
 */
function initDiscoveriesDataTable() {
  const repoUrl = document.querySelector('#repo-url').innerText;
  const filename = document.querySelector('#file-name').innerText;
  $('#discoveries-table').DataTable({
    ...defaultTableSettings,
    pageLength: localStorage.hasOwnProperty('sharedPageLength') ? localStorage.getItem("sharedPageLength") : 10,
    serverSide: true,
    order: [[3, "asc"]], // Set default column sorting
    columns: [ // Table columns definition
      {
        data: null,
        defaultContent: "",
        orderable: false
      }, {
        data: "category",
        className: "dt-center nowrap",
      }, {
        data: "snippet",
        className: "snippet",
      }, {
        data: "state",
        className: "dt-center nowrap",
      }, {
        data: "tot",
        orderable: false,
        className: "dt-center nowrap",
      }, {
        data: "occurrences",
        className: "none"
      }, {
        data: "actions",
        orderable: false
      }
    ],
    searchCols: [null, null, null, { search: 'new' }, null, null, null],
    ajax: { // AJAX source info
      url: "/get_discoveries",
      data: {
        url: repoUrl,
        ...filename && { file: filename }
      },
      dataSrc: function (json) {
        return json.data.map(item => {
          // Map json data before sending it to datatable
          const details = `
          <div>
          <table>
            <thead>
              <tr>
                ${filename ? '' : '<th>File</th>'}
                <th class="hash">Commit hash</th><th class="dt-center">Line number</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${item.occurrences.slice(0, 10).map(i => `
                <tr>
                  ${filename ? "" : `<td class="filename"><span>${i.file_name}</span></td>`}
                  <td class="hash">${i.commit_id}</td>
                  <td class="dt-center">${i.line_number}</td>
                  <td>
                    <a class="btn btn-light grey-color" target="_blank" href="${repoUrl}/blob/${i.commit_id}/${i.file_name}#L${i.line_number}">
                      <span class="icon icon-github"></span>
                      <span class="btn-text">Show on GitHub</span>
                    </a>
                  </td>
                </tr>
              `).join('\n')}
              ${item.occurrences.length > 10 ? `
              <tr><td colspan="${filename ? 3 : 4}">and ${item.occurrences.length - 10} more...<td></tr>
              ` : ""}
            </tbody>
          </table><div>`;

          return {
            ...item,
            state: states[item.state],
            snippet: encodeHTML(item.snippet),
            tot: item.occurrences.length,
            occurrences: details,
            actions: discoveriesBtnGroupTemplate('Mark as')
          }
        })
      }
    },
    initComplete: function () {
      var column = this.api().columns(3);
      var select = $('<select><option value=""></option></select>')
        .on('change', function () {
          var val = $.fn.dataTable.util.escapeRegex($(this).val());
          column.search(val).draw();
        });

      select.append(`
        <option value="all">all</option>
        <option value="new" selected>leak</option>
        <option value="false_positive">false positive</option>
        <option value="addressing">addressing</option>
        <option value="not_relevant">not relevant</option>
      `);

      $('#discoveries-table_filter').after(
        `<div class="filter-state">
          <span class="icon icon-filter_list"></span>
          <span>State:</span>
          <div id="select-filter-container"></div>
        </div>`);
      $('#select-filter-container').append(select);
    }
  },

    $('#discoveries-table').on('length.dt', function (e, settings, len) {
      localStorage.setItem('sharedPageLength', len);
    })
  );
}

/**
 * Event handler for update discoveries' button
 */
function initUpdateDiscoveries() {
  $(document).on('click', '.btn-group .btn', function () {
    const repoUrl = document.querySelector('#repo-url').innerText;
    const state = this.dataset.state;
    let filename, snippet;
    const datatable = $('.dataTable').DataTable();

    if (document.querySelector("#files-table")) {
      filename = this.closest('tr').querySelector('.filename').innerText;
    } else {
      filename = document.querySelector("#file-name").innerText;
      snippet = this.closest('tr')?.querySelector('.snippet')?.innerHTML;
    }

    $.ajax({
      url: 'update_discovery_group',
      method: 'POST',
      data: {
        state: state,
        url: repoUrl,
        ...filename && { file: filename },
        ...snippet && { snippet: decodeHTML(snippet) }
      },
      beforeSend: function () {
        datatable.processing(true);
      },
      success: function () {
        datatable.ajax.reload(null, false);
      }
    })
  });
}

/**
 * Periodically get updates on the scanning status if scanning
 */
function initUpdateScanning() {
  // Get status only if scanning when loading the page
  if (!document.querySelector('#newScan.disabled')) return;
  scanInterval = setInterval(getScan, POLLING_INTERVAL);
}

let scanInterval = null;
const getScan = function () {
  const repoUrl = document.querySelector('#repo-url').innerText;
  $.ajax({
    url: '/get_scan_status',
    data: { url: repoUrl },
    success: function (json) {
      const btn = document.querySelector('#newScan');
      if (json.scanning) {
        btn.disabled = true;
        btn.classList.add('disabled');
        btn.classList.add('warning-bg');
        btn.classList.remove('primary-bg');
        btn.innerHTML = `
          <span class="icon icon-timelapse"></span><span>Scanning...</span>`;
      } else {
        clearInterval(scanInterval);
        btn.disabled = false;
        btn.classList.remove('disabled');
        btn.classList.remove('warning-bg');
        btn.classList.add('primary-bg');
        btn.innerHTML = `
          <span class="icon icon-refresh"></span><span>Rescan</span>`;
        if ($('#discoveries-table, #files-table')) $('.dataTable').DataTable().ajax.reload();
      }
    }
  })
}

/**
 * Mapping of possible states of a discovery in the format "key-description".
 */
const states = {
  new: "leak",
  false_positive: "false positive",
  addressing: "addressing",
  not_relevant: "not relevant"
}

const discoveriesBtnGroupTemplate = mark => `
<div class="btn-group">
  <div class="btn primary-bg" data-state="false_positive">
    <span class="icon icon-outlined_flag"></span>
    <span>${mark} FPs</span>
  </div>
  <div class="dropdown-container">
    <div class="dropdown-opener primary-bg">
      <span class="icon icon-keyboard_arrow_down"></span>
    </div>
    <div class="dropdown">
      <div class="btn light-bg danger-color" data-state="new">
        <span class="icon icon-error_outline"></span>
        <span>${mark} leak</span>
      </div>
      <div class="btn light-bg warning-color" data-state="addressing">
        <span class="icon icon-timelapse"></span>
        <span>${mark} addressing</span>
      </div>
      <div class="btn light-bg grey-color" data-state="not_relevant">
        <span class="icon icon-inbox"></span>
        <span>${mark} not relevant</span>
      </div>
    </div>
  </div>
</div>`;