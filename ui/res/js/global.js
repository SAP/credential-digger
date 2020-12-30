document.addEventListener("DOMContentLoaded", function () {
  if (document.querySelector('.btn-group')) initButtonGroup();
});

function initButtonGroup() {
  // Only have one button group active at a time
  var activeBtnGroup = null;

  // Toggle button dropdown when clicking on the opener
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
  $(document).on('click', function (e) {
    if (!activeBtnGroup || activeBtnGroup.contains(e.target)) return;
    activeBtnGroup.classList.remove('active');
    activeBtnGroup = null;
  });
}