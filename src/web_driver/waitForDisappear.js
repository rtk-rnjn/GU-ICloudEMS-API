
function waitForElementToDisappearByClassString(classString, timeout, callback) {
    const observer = new MutationObserver(() => {
        const element = document.querySelector(`.${classString}`);
        if (!element) {
            observer.disconnect();
            callback();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    setTimeout(() => {
        observer.disconnect();
        callback();
    }, timeout);
}

waitForElementToDisappearByClassString('swal2-buttonswrapper swal2-loading', 10000, () => {
    console.log('Element with class "swal2-buttonswrapper swal2-loading" has disappeared!');
});


window.addEventListener('load', () => {
    console.log('Page has loaded!');
});

document.addEventListener('DOMContentLoaded', () => {
    console.log('Document has loaded!');
});


function waitForTablesAndDelay(tableTag, count, delay, callback) {
    const tables = document.getElementsByTagName(tableTag);

    if (tables.length === count) {
        callback(tables);
    }
}
  
const tableTag = "table";
const tableCount = 3;
const delayAfterTables = 3700;

waitForTablesAndDelay(tableTag, tableCount, delayAfterTables, (tables) => {
    console.log("All tables have appeared:", tables);
    setTimeout(() => {
        console.log("Additional delay of 3.7 seconds has passed.");
    }, delayAfterTables);
});
