document.addEventListener("DOMContentLoaded", function () {
  if (document.querySelector('.btn-group')) initButtonGroup();
  if (document.querySelector('.modal')) initModals();
});

/**
 * Handle opening and closing of the dropdown in button groups
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
 * Handle opening and closing of modals
 * 
 * Usage:
 *  - Add class `modal` and an id to the modal element 
 *  - Add class `modal-opener` and attribute `data-modal="MODAL-ID"` to the 
 *    button that opens the modal
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
    }
  });
}