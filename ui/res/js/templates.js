const states = {
  new: "leak",
  false_positive: "false positive",
  addressing: "addressing",
  not_relevant: "not relevant"
}

const defaultTableSettings = {
  responsive: true,
  pageLength: 10, // Default # of records shown in the table
  language: {
    search: '<span class="icon icon-search dt-icon"></span>',
    paginate: {
      previous: '<span class="icon icon-keyboard_arrow_left dt-icon"></span>',
      next: '<span class="icon icon-keyboard_arrow_right dt-icon"></span>'
    }
  }
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

const reposActionsTemplate = url => `
<div class="btns-container">
  <div class="btn-group">
    <a class="btn outline-bg" href="/files?url=${url}">
      <span class="icon icon-folder_open"></span><span>Files view</span>
    </a>
    <div class="dropdown-container">
      <div class="dropdown-opener outline-bg">
        <span class="icon icon-keyboard_arrow_down"></span>
      </div>
      <div class="dropdown">
        <a class="btn outline-bg" href="/discoveries?url=${url}">
          <span class="icon icon-error_outline"></span><span>Discoveries view</span>
        </a>
      </div>
    </div>
  </div>
  <button id="deleteRepo" class="btn danger-bg">
    <span class="icon icon-delete_outline"></span><span>Delete Repo</span>
  </button>
</div>`;