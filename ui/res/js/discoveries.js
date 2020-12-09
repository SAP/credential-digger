const buttonGroupTemplate = `
<div class="btn-group danger">
  <div class="btn default-btn">Mark all as FPs</div>
  <label class="dropdown-container">
    <div class="dropdown-opener"></div>
    <div class="dropdown">
      <div class="btn light">Mark all as addressing</div>
      <div class="btn light">Mark all as not relevant</div>
    </div>
  </label>
</div>`

$(document).ready(function() {
  const repoUrl = document.querySelector('#repo-url').innerText;
  $('#discoveriesTable').DataTable({
    responsive: true, // Enable dataTables' responsive features
    pageLength: 25, // Default # of records shown in the table
    ajax: { // AJAX source info
      url: "/discoveries-data",
      data: { url: repoUrl },
      dataSrc: function(json) {
        return json.map(item => {
          return {
            ...item,
            file_name: `<a href="/discoveries?url=${repoUrl}&file=${item.file_name}">${item.file_name}</a>`
          }
        })
      }
    },
    order: [[1, "desc"]], // Set default column sorting
    columns: [ // Table columns definition
      { 
        data: "file_name",
        className: "filename"
      }, { 
        data: "new", // Mapping to the source json
        className: "dt-center"
      }, { 
        data: "false_positives",
        className: "dt-center"
      }, { 
        data: "addressing",
        className: "dt-center"
      }, { 
        data: "not_relevant",
        className: "dt-center"
      }, { 
        data: null,
        defaultContent: buttonGroupTemplate
      }
    ],
  });

  initButtonGroup();
});

function initButtonGroup() {
  // Only have one button group active at a time
  var activeBtnGroup = null;

  // Toggle button dropdown when clicking on the opener
  document.addEventListener('click', e => {
    if(!e.target.matches('.btn-group .dropdown-opener, .btn-group .dropdown .btn')) return;
    const parent = e.target.closest('.btn-group');
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