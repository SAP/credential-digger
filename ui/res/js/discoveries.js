const actionsTemplate = `
<div class="btn-group" data-filename="{{filename}}">
  <div class="btn default-btn primary-bg" data-state="false_positive">
    <span class="icon icon-outlined_flag"></span>
    <span>Mark all as FPs</span>
  </div>
  <div class="dropdown-container">
    <div class="dropdown-opener primary-bg">
      <span class="icon icon-keyboard_arrow_down"></span>
    </div>
    <div class="dropdown">
      <div class="btn light-bg danger-color" data-state="new">
        <span class="icon icon-error_outline"></span>
        <span>Mark all as leaks</span>
      </div>
      <div class="btn light-bg warning-color" data-state="addressing">
        <span class="icon icon-timelapse"></span>
        <span>Mark all as addressing</span>
      </div>
      <div class="btn light-bg grey-color" data-state="not_relevant">
        <span class="icon icon-inbox"></span>
        <span>Mark all as not relevant</span>
      </div>
    </div>
  </div>
</div>
`

const defaultTableSettings = {
  responsive: true, // Enable dataTables' responsive features
  pageLength: 10, // Default # of records shown in the table
  language: {
    search: '<span class="icon icon-search dt-icon"></span>',
    paginate: {
      previous: '<span class="icon icon-keyboard_arrow_left dt-icon"></span>',
      next: '<span class="icon icon-keyboard_arrow_right dt-icon"></span>'
    }
  }
}


$(document).ready(function() {
  if (document.querySelector('#listing-table')) initListingDataTable();
  if (document.querySelector('#detail-table'))  initDetailDataTable();
  initButtonGroup();
});

function initListingDataTable() {
  const repoUrl = document.querySelector('#repo-url').innerText;
  $('#listing-table').DataTable({
    ...defaultTableSettings,
    ajax: { // AJAX source info
      url: "/get_discoveries_data",
      data: { url: repoUrl },
      dataSrc: function(json) { // Map json data before sending it to datatable
        return json.map(item => {
          return {
            ...item,
            file_name: `<a href="/discoveries?url=${repoUrl}&file=${item.file_name}">${item.file_name}</a>`,
            actions: actionsTemplate.replace("{{filename}}", item.file_name)
          }
        })
      }
    },
    order: [[0, "asc"]], // Set default column sorting
    columns: [ // Table columns definition
      { 
        data: "file_name",
        className: "filename",
        orderSequence: ["asc", "desc"]
      }, { 
        data: "new", // Mapping to the source json
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
    initComplete: function(settings, json) {
      const totalDiscoveries = json.reduce((sum, currItem) => 
         sum + currItem.tot_discoveries, 0)
      document.querySelector('#discoveriesCounter').innerText = totalDiscoveries;
    }
  });
}

function initDetailDataTable() {
  const repoUrl = document.querySelector('#repo-url').innerText;
  const fileName = document.querySelector('#file-name').innerText;
  $('#detail-table').DataTable({
    ...defaultTableSettings,
    ajax: { // AJAX source info
      url: "/get_discoveries_data",
      data: { 
        url: repoUrl,
        file: fileName
      },
      dataSrc: function(json) {
        return json.map(item => {
          return {
            ...item,
            actions: actionsTemplate
          }
        })
      }
    },
    order: [[2, "desc"]], // Set default column sorting
    columns: [ // Table columns definition
      // { 
      //   data: "file_name",
      //   className: "filename"
      // }, { 
      //   data: "new", // Mapping to the source json
      //   className: "dt-center"
      // }, { 
      //   data: "false_positives",
      //   className: "dt-center"
      // }, { 
      //   data: "addressing",
      //   className: "dt-center"
      // }, { 
      //   data: "not_relevant",
      //   className: "dt-center"
      // }, { 
      //   data: "actions",
      // }
    ],
    initComplete: function(settings, json) {
      const totalDiscoveries = json.reduce((sum, currItem) => 
         sum + currItem.tot_discoveries, 0)
      document.querySelector('#discoveriesCounter').innerText = totalDiscoveries;
    }
  });
}

function initButtonGroup() {
  const repoUrl = document.querySelector('#repo-url').innerText;
  // Only have one button group active at a time
  var activeBtnGroup = null;

  // Toggle button dropdown when clicking on the opener
  $(document).on('click', '.btn-group .dropdown-opener, .btn-group .dropdown, .btn-group.active .default-btn', function() {
    const parent = this.closest('.btn-group');
    const dropdownOpen = parent.classList.contains('active');
    if(dropdownOpen) {
      parent.classList.remove('active');
      activeBtnGroup = null;  
    } else {
      if(activeBtnGroup) activeBtnGroup.classList.remove('active');
      parent.classList.add('active');
      activeBtnGroup = parent;
    }
  });

  // Close button dropdown when clicking outside of the button
  document.addEventListener('click', e => {
    if(!activeBtnGroup || activeBtnGroup.contains(e.target)) return;
    activeBtnGroup.classList.remove('active');
    activeBtnGroup = null;
  });

  // Update discovery group
  $(document).on('click', '.btn-group .btn', function() {
    const filename = this.closest('.btn-group').dataset.filename;
    const state = this.dataset.state;
    $.ajax({
      url: 'update_discovery_group',
      method: 'POST',
      data: {
        state: state,
        url: repoUrl,
        file: filename
      }, 
      success: function() {
        $('#listing-table').DataTable().ajax.reload();
      }
    })
  });
}

// delete repo popup
// add action listener to delete repo button
document.getElementById('deleteRepo').addEventListener('click', function (event) {
  // show popup
  document.getElementById('deleteRepoModal').style.display = 'block';
});
// add action listener for window (clicking anywhere)
window.addEventListener('click', function (event) {
  // if user clicks in the modal area (area around the popup) hide popup
  if (event.target == document.getElementById('deleteRepoModal')) {
    document.getElementById('deleteRepoModal').style.display = 'none';
  }
  if (event.target == document.getElementById('addRepoModal')) {
    closeAddRepo();
  }

});

document.getElementById('cancelDeleteRepo').addEventListener('click', function (event) {
  // hide popup
  document.getElementById('deleteRepoModal').style.display = 'none';
});

document.getElementById('cancelAddRepo').addEventListener('click', closeAddRepo);

// New scan
// add action listener to scan repo button
document.getElementById('newScan').addEventListener('click', function (event) {
  // Show popup
  document.getElementById('addRepoModal').style.display = 'block';
  document.getElementById('repoLinkInput').value = window.name;
  checkFormFilled();
});
document.getElementById('startRepoScan').addEventListener('click', function () {
  // close popup
  document.getElementById('addRepoModal').style.display = 'none';
});
var allDiscoveries = document.getElementsByClassName('discoveryEntry');
// Show/hide fp flag
function switchFilter() {
  // Swap the value of the filtering FLAG
  filterFPs = filterFPs ^ 1;
  // Store the flag's value as long as the session is still running
  sessionStorage.setItem('filterFPs', filterFPs);
  // Change color
  document.getElementById('showFPs').style.backgroundColor = '#0000ff';
  // Filter discoveries
  toggleFPs();
}

// add action listener to checkbox that selects all the rules
document.getElementById('cbAllRules').addEventListener('change', function () {
  //Select no category if this checkbox is 'Active'
  document.getElementById('ruleSelector').selectedIndex = -1;
  checkFormFilled();
});

// add action listener to repo category selector
document.getElementById('ruleSelector').addEventListener('change', function () {
  //Disable the 'Use all rules' checkbox when a category is being manually selected.
  document.getElementById('cbAllRules').checked = false;
  checkFormFilled();
});

/** LEGACY FUNCTIONS STILL TO IMPLEMENT */

// let filterFPs = false;
// // The list of the categories to skip while filtering.
// let categoriesToSkip = [];
// // It is mandatory to wait for the window to load before executing the
// // scripts
// window.onload = function () {
//   filterFPs = sessionStorage.getItem('filterFPs');
//   if (filterFPs == true) {
//     toggleFPs();
//   }
// };

// var tableRows = document.getElementsByClassName('tableRowContent');
// // add action listeners to table rows
// for (var i = 0; i < tableRows.length; i++) {
//   tableRows[i].addEventListener('mouseover', function (event) {
//     // open expand table row
//     openExpandTableRow(event.currentTarget);
//   });
// }

// function openExpandTableRow(tr) {
//   // get all hidden expand table rows
//   var expandTableRows = document.getElementsByClassName('expandTableRow');
//   // get all table rows
//   var tableRows = document.getElementsByClassName('tableRowContent');
//   // step trough all expand table rows
//   for (var i = 0; i < expandTableRows.length; i++) {
//     // show if mouseover
//     if (tr == tableRows[i]) {
//       expandTableRows[i].style.display = 'table-cell';
//       tableRows[i].style.background = '#f5f5f5';
//     } else {
//       // hide if not mouseover
//       expandTableRows[i].style.display = 'none';
//       tableRows[i].style.background = 'transparent';
//     }
//   }
// }

// function toggleFPs() {
//   let countDiscoveries = 0;
//   for (let i = 0; i < allDiscoveries.length; i++) {
//     // If the discovery is not new, hide its row and the expandable one
//     if (allDiscoveries[i].children[2].valueOf().innerText == 'false_positive') {
//       allDiscoveries[i].style.display = filterFPs ? 'none' : '';
//       countDiscoveries++;
//     }
//   }
//   document.getElementById('showFPs').innerHTML = filterFPs ? 'Show FPs' : 'Hide FPs';
//   document.getElementById('discoveriesCounter').innerHTML = filterFPs ?
//     `${allDiscoveries.length} discoveries found (${countDiscoveries} false positives are hidden)` :
//     `${allDiscoveries.length} discoveries found`;
// }



// // A self-invoking function to assign functions to the filtering buttons
// (function catFilteringInit() {
//   let filteringButtons = document.getElementsByClassName('categoryToggle');
//   for (let i = 0; i < filteringButtons.length; i++) {
//     let buttonsContainer = filteringButtons[i];
//     buttonsContainer.onclick = clickedButton => {
//       let button = clickedButton.target;
//       const category = button.innerText;
//       const indexOfCat = categoriesToSkip.indexOf(category);
//       if (indexOfCat > -1) {
//         // Disable the filter
//         categoriesToSkip.splice(indexOfCat, 1);
//         button.style.background = 'white';
//       }
//       else {
//         // Enable the filter
//         categoriesToSkip.push(category);
//         button.style.background = 'dodgerblue';
//       }
//       filterCategories();
//     };
//   }

// }());

// /**
//  * A function to filter the discoveries based on their categories.
//  */
// function filterCategories() {
//   // No categories to filter
//   if (categoriesToSkip.length == 0) {
//     for (let i = 0; i < allDiscoveries.length; i++) {
//       let discovery = allDiscoveries[i];
//       discovery.style.display = '';
//     }
//   }
//   else {
//     for (let i = 0; i < allDiscoveries.length; i++) {
//       let discovery = allDiscoveries[i];
//       /**
//        * Ninja code : skip is a boolean. it is set to true if this discovery will be ignored
//        * false, otherwise.
//        */
//       const skip = (categoriesToSkip.indexOf(discovery.children[0].valueOf().innerText) == -1);
//       discovery.style.display = skip ? 'none' : '';
//     }
//   }

// }