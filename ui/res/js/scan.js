const DONE = "Done!"
var createPTag = function(content){
    var para = document.createElement("P")
    var txt = document.createTextNode(content)
    para.appendChild(txt)
    return para
}

var scanRepo = function(e) {
    renderModal();
};

const scanRepoForm = document.forms["scan_repo"];
scanRepoForm.addEventListener("submit", scanRepo, true);

function renderModal() {
    //if modal already exists on page, just show it
    okModal = document.getElementById('okModal');
    if(okModal != null){
        okButton.style.display = 'block';
        return
    }
    //else create it
    const modal = `<div class="modal"  id="okModal">
                    <div class="modal-content">
                        <div class="topicHeaderWrapperAccept">
                            <h1 class="topicH1">Scan is under way....</h1>
                        </div>
                        <div id="modal-waterfall">
                              <p>Working hard... </p>
                        </div>
                        <span class="buttonsAccept">
                            <button class="button" id="okButton" >Ok</button>
                        </span>
                    </div>
                    </div>`
    //insert into document
    document.body.insertAdjacentHTML('beforeend', modal);

    okModal = document.getElementById('okModal');
    okModal.style.display = 'block';
    document.getElementById('okButton').onclick = function(){
        okModal.style.display = 'none';
    };
}
