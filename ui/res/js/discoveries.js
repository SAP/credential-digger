document.addEventListener("DOMContentLoaded", function () {
  if (document.querySelector('#files-table')) initFilesDataTable();
  if (document.querySelector('#discoveries-table')) initDiscoveriesDataTable();
  initUpdateDiscoveries();
  initNewScan();
});

function initFilesDataTable() {
  const repoUrl = document.querySelector('#repo-url').innerText;
  $('#files-table').DataTable({
    ...defaultTableSettings,
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
    },
    initComplete: function (settings, json) {
      const totalDiscoveries = json.reduce((sum, currItem) =>
        sum + currItem.tot_discoveries, 0)
      document.querySelector('#discoveriesCounter').innerText = totalDiscoveries;
    }
  });
}

function initDiscoveriesDataTable() {
  const repoUrl = document.querySelector('#repo-url').innerText;
  const filename = document.querySelector('#file-name').innerText;
  $('#discoveries-table').DataTable({
    ...defaultTableSettings,
    order: [[3, "desc"]], // Set default column sorting
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
        className: "dt-center nowrap",
      }, {
        data: "occurrences",
        className: "none"
      }, {
        data: "actions",
        orderable: false
      }
    ],
    ajax: { // AJAX source info
      url: "/get_discoveries",
      data: {
        url: repoUrl,
        ...filename && { file: filename }
      },
      dataSrc: function (json) {
        return json.map(item => {
          // Map json data before sending it to datatable
          const details = `
          <div>
          <table>
            <thead>
              <tr>
                ${filename ? '': '<th>File</th>'}
                <th class="hash">Commit hash</th><th class="dt-center">Line number</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${item.occurrences.slice(0,10).map(i => `
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
    initComplete: function (settings, json) {
      const totalDiscoveries = json.reduce((sum, currItem) =>
        sum + currItem.occurrences.length, 0)
      document.querySelector('#discoveriesCounter').innerText = totalDiscoveries;
    }
  });
}

function initUpdateDiscoveries() {
  const repoUrl = document.querySelector('#repo-url').innerText;

  // Update discovery group
  $(document).on('click', '.btn-group .btn', function () {
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
      beforeSend: function() {
        datatable.processing(true);
      },
      success: function () {
        datatable.ajax.reload();
      }
    })
  });
}

function initNewScan() {
  // add action listener to checkbox that selects all the rules
  document.querySelector('#cbAllRules').addEventListener('change', function () {
    //Select no category if this checkbox is 'Active'
    document.querySelector('#ruleSelector').selectedIndex = -1;
    checkFormFilled();
  });

  // add action listener to repo category selector
  document.querySelector('#ruleSelector').addEventListener('change', function () {
    //Disable the 'Use all rules' checkbox when a category is being manually selected.
    document.querySelector('#cbAllRules').checked = false;
    checkFormFilled();
  });
}