/// Global Vars

var beerArr = null;

/// Event Listeners -->
window.addEventListener("DOMContentLoaded", async function () {
    if (this.window.sessionStorage.beerArr != undefined) {
        beerArr = JSON.parse(window.sessionStorage.beerArr);
    }
})


// verifies if all required fields are completed
function validateEntries() {
    const distrib = window.document.querySelector("#distributor"),
        whoTaking = window.document.getElementById('taking'),
        whereGoing = window.document.getElementById('going'),
        dateTaken = window.document.getElementById('dateTaken'),
        invalidInput = '1px solid red',
        currDate = new Date();
    let invalidEntry = false;

    // rewrite this as a for loop over array of the variables
    if(whoTaking.value === ''){
        invalidEntry = true;
        whoTaking.style.border = invalidInput;
    } else {
        whoTaking.style.border = '';
    }
    if(whereGoing.value === '' && whereGoing.type != 'hidden'){
        invalidEntry = true;
        whereGoing.style.border = invalidInput;
    } else {
        whereGoing.style.border = '';
    }
    if(dateTaken.value === '' || new Date(dateTaken.value) > currDate) {
        invalidEntry = true;
        dateTaken.style.border = invalidInput;
    } else {
        dateTaken.style.border = '';
    }
    if(distrib.value === '') {
        invalidEntry = true;
        distrib.style.border = invalidInput;
    } else if (distrib.value.toLowerCase() == 'other' && document.querySelector("#vendorOther").value == '') {
        invalidEntry = true;
        distrib.style.border = invalidInput;
        document.querySelector("#vendorOther").style.border = invalidInput;
    } else {
        distrib.style.border = '';
    }

    const beersTable = document.querySelector("#beers");
    for (let row of beersTable.rows) {
        if (row.cells[1].tagName != 'TH') {
            let unitSize = row.cells[1].firstElementChild.firstElementChild,
                quant = row.cells[2].firstElementChild;
            if (unitSize.value == 'default' && quant.value != '') {
                invalidEntry = true;
                unitSize.style.border = invalidInput;
            } else if (quant.value < 0) {
                invalidEntry = true;
                quant.style.border = invalidInput;
            } else {
                unitSize.style.border = '';
                quant.style.border = '';
            }
        }
    }

    return invalidEntry;
}

// calls validateEntries function then gets data from form and sends to server. resets all inputs after submission
async function submitButtonClicked() {
    if(validateEntries() === true) {
        setMessage(false,'Please fill out entire form before submitting',10000);
        return
    }
    const subObj = new Object();
    try {
        subObj.employeeName = window.document.getElementById('taking').value;
        subObj.destination = window.document.getElementById('going').value;
        subObj.dateTaken = window.document.getElementById('dateTaken').value;
        subObj.vendor = getVendorSubmitted();
        subObj.beersTaken = getBeersSubmitted();
        const resp = await fetch("/", {
            method: "post",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify(subObj)
        })
        const rJson = await resp.json()
        setMessage(true, rJson.status_message, 10000);
        
        resetInputs();
    }
    catch (err) {
        setMessage(false, err.toString(), 10000)
    };
}

async function downloadReport(btnElement) {
    let payload;
    if (btnElement.parentElement.id == "filterByDate") {
        const fromDate = document.querySelector('#fromDate');
        const toDate = document.querySelector('#toDate');
        payload = JSON.stringify({"fromDate": fromDate.value, "toDate": toDate.value})
    } else {
        const dists = document.getElementsByName("distribFilter");
        let tempArr = new String();
        dists.forEach((d) => {
            if (d.checked) {
                tempArr = tempArr + "," + d.id;
            }
        })
        payload = JSON.stringify({"distributors": tempArr});
    }
    toggleLoading(btnElement);
    await fetch('/downloadReport', {
        method:'post',
        headers: {"Content-Type":"application/json"},
        body: payload
    })
    .then((resp) => {
        if (!resp.ok) {
            const rJson = resp.json();
            return Promise.reject(`Failed to download file ${rJson.status_message}`);
        } else {
            return resp.blob();
        }
    })
    .then(resp => {
        const aElement = document.createElement('a');
        aElement.setAttribute('download','Utepils_Removals_Report.xlsx');
        const href = URL.createObjectURL(resp);
        aElement.href = href;
        aElement.setAttribute('target', '_blank');
        aElement.click();
        URL.revokeObjectURL(href);
        toggleLoading(btnElement);
    })
    .catch((err) => {
        toggleLoading(btnElement);
        setMessage(false, `Failed to download file\nError: ${JSON.stringify(err, Object.getOwnPropertyNames(err))}`)
    })
}

function getVendorSubmitted() {
    const distrib = document.querySelector('#distributor');
    if (distrib.value.toLowerCase() == 'other') {
        return document.querySelector("#vendorOther").value;
    } else {
        return distrib.value;
    }
}

function getBeersSubmitted() {
    let submittedArr = new Array();
    const beersTable = document.querySelector("#beers");
    for (let row of beersTable.rows) {
        if (row.cells[1].tagName != 'TH') {
            let unitSize = row.cells[1].firstElementChild.firstElementChild,
            quant = row.cells[2].firstElementChild;
            if (unitSize.value != '' && quant.value > 0) {
                let beersObj = new Object();
                let beerName = row.cells[0].firstElementChild.firstElementChild.value + "-" + unitSize.value.slice(-2);
                beersObj[beerName] = {
                    "quantity": quant.value,
                    "size": unitSize.value
                }
                submittedArr.push(beersObj);
            }
        }
    }
    return submittedArr;
}

function getAdminBeerConfig() {
    let selectArr = document.querySelectorAll("#beerConfig .unit-select");
    let unitObj = new Object();
    selectArr.forEach((ele) => {
        console.log(ele.previousElementSibling.hasChildNodes());
        let beerName = ele.previousElementSibling.innerText;
        if (beerName == "") {
            beerName = ele.previousElementSibling.firstChild.value;
        }
        if (beerName == "") {
            throw new Error("Could not find newly added beer name. Please contact developer");
        }
        unitObj[beerName] = new Object();
        unitObj[beerName].active = ele.nextElementSibling.firstElementChild.checked;
        for (let i = 0; i < ele.childElementCount; i++) {
            ele.querySelectorAll("label").forEach((checkLabel) => {
                if (checkLabel.previousElementSibling.checked) {
                    unitObj[beerName][checkLabel.getAttribute('for')] = checkLabel.innerText;
                }
            })
        }
    })
    return unitObj;
}

async function saveConfig(btnElement) {
    let subObj = new Object();
    let distribArr = new Array();
    const distribTable = document.querySelector('#distribConfig');
    
    for (let i = 1, row; row=distribTable.rows[i]; i++) {
        if (row.cells[0].childElementCount > 0) {
            distribArr.push(row.cells[0].firstElementChild.value)
        } else {
            distribArr.push(row.cells[0].innerText)
        }
    }
    
    try {
        subObj.beerList = getAdminBeerConfig();
    } catch (error) {
        setMessage(false, error.message, 20000);
        return;
    }
    subObj.distributorList = distribArr;
    toggleLoading(btnElement);
    try {
        const resp = await fetch("/admin/saveConfig", {
            method: "post",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify(subObj)
        })
        const rJson = await resp.json();
        setMessage(rJson.success, rJson.status_message, 10000);
    } catch(err) {
        setMessage(false, err.toString(), 10000);
    } finally {
        toggleLoading(btnElement);
    }
}

// reset all inputs after submission
function resetInputs(success) {
    document.querySelector("#mainForm").reset();
    const goingInput = document.querySelector('#going'),
          otherInput = document.querySelector("#vendorOther");
    if (goingInput.type != 'text') {
        goingInput.type == 'text';
        goingInput.previousElementSibling.hidden = false;
    }
    if (otherInput.type != 'hidden') {
        otherInput.previousElementSibling.hidden = true;
        otherInput.type = 'hidden';
    }
    const tbl = document.querySelector("#beers");
    for (let i = tbl.rows.length - 1; i > 1; i--) {
        tbl.deleteRow(i)
    }
}

function setMessage(success, message, msgTimeout = 10000) {
    const msg = window.document.getElementById('message');
    if(success) {
        msg.innerText = message;
        msg.style.background = "hsla(120, 100%, 25%, 0.25)";
    } else {
        const msg = window.document.getElementById('message');
        msg.innerText = message;
        msg.style.background = "hsla(0, 100%, 50%, 0.25)";
    }
    if (msg.style.display == "none") {
        msg.style.display = "";
    }
    window.setTimeout(function(){
        msg.style.display = "none";
        },msgTimeout);
        window.scrollTo({top:0, left:0, behavior: 'smooth'});
}

function addNewBeerRow() {
    const path = window.location.pathname;
    let tbl = document.querySelector(path == "/admin" ? '#beerConfig' : "#beers" );
    let row = tbl.insertRow(-1);
    let cell1 = row.insertCell(0);
    let cell2 = row.insertCell(1);
    let cell3 = row.insertCell(2);
    switch (path) {
        case "/admin":
            const chkBoxElement = row.previousElementSibling.cells[1];
            cell1.innerHTML = '<input type="text" placeholder="Enter Beer Name">';
            cell2.innerHTML = chkBoxElement.cloneNode(true).innerHTML;
            cell2.classList.add("unit-select");
            cell3.innerHTML = '<input class="valign-override" type="checkbox"><button class="danger-btn" style="margin-left:1rem" onclick="removeTableRow(this)">Remove</button>';
            let newCheckBoxes = cell2.querySelectorAll('input[type=checkbox]');
            newCheckBoxes.forEach((box) => {
                if (box.checked) {
                    box.checked = false;
                }
            })
            cell1.firstElementChild.focus();
            break;
        case "/":
            cell1.innerHTML = tbl.rows[1].cells[0].cloneNode(true).innerHTML;
            cell2.innerHTML = tbl.rows[1].cells[1].cloneNode(true).innerHTML;
            cell3.innerHTML = tbl.rows[1].cells[2].cloneNode(true).innerHTML;

            let selEle = cell1.firstElementChild.firstElementChild;
            selEle.value = "";
            selEle.setAttribute('name', `beer${tbl.rows.length - 1}`)
            selEle.setAttribute('id', `beer${tbl.rows.length - 1}`)

            unitEle = cell2.firstElementChild.firstElementChild;
            unitEle.setAttribute('name', `unit${tbl.rows.length - 1}`)
            unitEle.setAttribute('id', `unit${tbl.rows.length - 1}`)
            unitEle.innerHTML = "";
            
            quantEle = cell3.firstElementChild;
            quantEle.value = "";
            quantEle.setAttribute('name', `quant${tbl.rows.length - 1}`)
            
            selEle.focus();
            break;
        default:
            break;
    }
}

function removeTableRow(target) {
    let tbl = target.parentNode.parentNode.parentNode.parentNode;
    tbl.deleteRow(target.parentNode.parentNode.rowIndex);
}

function addDistributorRow() {
    let tbl = document.querySelector('#distribConfig');
    let row = tbl.insertRow(-1);
    let cell1 = row.insertCell(0);
    let cell2 = row.insertCell(1);
    cell1.innerHTML = '<input type="text" placeholder="Enter Name">';
    cell2.innerHTML = '<button class="danger-btn" onclick="removeDistribRow(this)">Remove</button>';
    cell1.firstElementChild.focus();
}

function toggleReportSection() {
    const reportSection = document.querySelector("#reportSection");
    if (reportSection.hidden) {
        reportSection.hidden = false;
        reportSection.nextElementSibling.hidden = false;
    } else {
        reportSection.hidden = true;
        reportSection.nextElementSibling.hidden = true;
    }
}

function toggleLoading(targetElement) {
    targetElement.nextElementSibling.hidden ? targetElement.nextElementSibling.hidden = false : targetElement.nextElementSibling.hidden = true;
    targetElement.hidden ? targetElement.hidden = false : targetElement.hidden = true;
}

function togglePulled(sourceEle) {
    const goingInput = document.querySelector('#going'),
        otherInput = document.querySelector("#vendorOther");
    sourceEle.value.toLowerCase() === 'taproom' ? goingInput.previousElementSibling.hidden = true : goingInput.previousElementSibling.hidden = false;
    sourceEle.value.toLowerCase() === 'taproom' ? goingInput.type = 'hidden' : goingInput.type = 'text';

    sourceEle.value.toLowerCase() === 'other' ? otherInput.previousElementSibling.hidden = false : otherInput.previousElementSibling.hidden = true;
    sourceEle.value.toLowerCase() === 'other' ? otherInput.type = 'text' : otherInput.type = 'hidden';
}

function setUnitOptions(sourceEle) {
    let unitSel = sourceEle.parentElement.parentElement.nextElementSibling.firstElementChild.firstElementChild;
    unitSel.innerHTML = '<option value="">Select size</option>';
    const br = JSON.parse(window.sessionStorage.beerArr);
    Object.entries(br[sourceEle.value]['units']).forEach(([unit, val]) => {
        if (unit != undefined && val != undefined && isObjEmpty(val) === false) {
            let tempNode = document.createElement('option');
            tempNode.value = unit;
            tempNode.text = val;
            unitSel.appendChild(tempNode);
        };
    })
    unitSel.value = "";
}

function isObjEmpty(obj) {
    return Object.keys(obj).length === 0;
}

function toggleReportFilter(sourceEle) {
    let eleDistrib = document.querySelector("#filterByDistrib");
    let eleDate = document.querySelector("#filterByDate");
    if (sourceEle.id == "radioDistrib") {
        eleDistrib.style.display = "";
    } else {
        eleDistrib.style.display = 'none';
    }
    if (sourceEle.id == "radioDate") {
        eleDate.style.display = "";
    } else {
        eleDate.style.display = 'none';
    }
}