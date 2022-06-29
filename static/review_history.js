$(document).ready(function() {
    initialiseTables();
    tableLinks();
});

function initialiseTables() {
    $("#reviewHistory").dataTable({
        "pagingType" : "simple_numbers",
        "lengthChange" : false,
        "order": [],
        "language": {
            "emptyTable" : `<div class="centered" style="margin-bottom: 6px">You have created no reviews.</div>`
        }
    });
}

function tableLinks() {
    $(".clickable-row").click(function () {
        window.location = $(this).data("url");
    });
}