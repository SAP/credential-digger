// Interval for polling scanning status in repos datatable
POLLING_INTERVAL = 5000;

/**
 * Default dataTables object settings for all tables
 */
const defaultTableSettings = {
  responsive: true,
  processing: true,
  pageLength: 10, // Default # of records shown in the table
  language: {
    search: '<span class="icon icon-search dt-icon"></span>',
    paginate: {
      previous: '<span class="icon icon-keyboard_arrow_left dt-icon"></span>',
      next: '<span class="icon icon-keyboard_arrow_right dt-icon"></span>'
    },
    loadingRecords: '&nbsp;',
    processing: '<div class="loaderWrapper"><div class="loader"></div></div>'
  }
}

document.addEventListener("DOMContentLoaded", function () {
  if (document.querySelector('.modal')) initModals();
  initButtonGroup();
});

/**
 * Handle opening and closing of the dropdown in button groups,
 */
function initButtonGroup() {
  // Only have one button group active at a time
  var activeBtnGroup = null;

  // Toggle button dropdown when clicking on the opener
  // (use jquery to easier handling of event delegation for dynamic elements)
  $(document).on('click', '.btn-group .dropdown-opener, .btn-group .dropdown, .btn-group.active .default-btn', function () {
    const parent = this.closest('.btn-group');
    const dropdownOpen = parent.classList.contains('active');
    if (dropdownOpen) {
      parent.classList.remove('active');
      activeBtnGroup = null;
    } else {
      if (activeBtnGroup) activeBtnGroup.classList.remove('active');
      parent.classList.add('active');
      activeBtnGroup = parent;
    }
  });

  // Close button dropdown when clicking outside of the button
  document.addEventListener('click', function (e) {
    if (!activeBtnGroup || activeBtnGroup.contains(e.target)) return;
    activeBtnGroup.classList.remove('active');
    activeBtnGroup = null;
  });
}

/**
 * Handle opening and closing of modals.
 * 
 * Usage:
 *  - Add class `modal` and an id to the modal element 
 *  - Add class `modal-opener` and attribute `data-modal="MODAL-ID"` to the 
 *    button that opens the modal
 *  - Add class `modal-closer` to the button that closes the modal
 */
function initModals() {
  // Event listener to open modal
  $(document).on('click', '.modal-opener', function () {
    const modalId = this.dataset.modal;
    document.querySelector('#' + modalId).classList.add('open');
  });

  // Even listener to close modal (`.modal-closer` or click outside of modal)
  window.addEventListener('click', function (e) {
    const nodeClass = e.target.classList;
    if (nodeClass.contains('modal') || nodeClass.contains('modal-closer')) {
      const modal = e.target.closest('.modal');
      modal.classList.remove('open');
      modal.querySelector('form')?.reset();
      modal.querySelectorAll('input, select, textarea, checkbox').forEach(node => {
        node.dispatchEvent(new Event('change', { bubbles: true }))
      });
    }
  });
}

$.fn.dataTable.ext.errMode = 'throw';
/**
 * Register DataTable's `processing()` plugin on all tables.
 * 
 * See: https://datatables.net/plug-ins/api/processing()
 */
jQuery.fn.dataTable.Api.register('processing()', function (show) {
  return this.iterator('table', function (ctx) {
    ctx.oApi._fnProcessingDisplay(ctx, show);
  });
});

/**
 * Handle the logout button
 */

$(window).ready(function () {
  if (document.cookie.indexOf('logged_in') != -1) {
    logout_button = document.createElement('a');
    logout_button.className = "headerItem headerLink"
    logout_button.href = "/logout"
    logout_button.innerHTML = "Logout"
    document.getElementById('topRightButtons').appendChild(logout_button);
    $('#topRightButtons').show();
  }
  else {
    if ($('#login_div').length) {
      $('#topRightButtons').hide();
    }
  }
});