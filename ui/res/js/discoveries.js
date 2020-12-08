$(document).ready(function() {
  console.log("test");
  $('#discoveriesTable').DataTable({
    responsive: true,
    ajax: {
      url: "/discoveries-data",
      data: { url: document.querySelector('#repo-url').innerText },
      dataSrc: ''
    },
    columns: [
      { data: "file_name" },
      { data: "new" },
      { data: "false_positives" },
      { data: "addressing" },
      { data: "not_relevant" }
    ]
  });
});

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