$(document).ready(function() {
    initialiseTables();
    tableLinks();
});

function initialiseTables() {
    $("#blogPosts").dataTable({
        "pagingType" : "simple_numbers",
        "lengthChange" : false,
        "order": [],
        "language": {
            "emptyTable" : `<div class="centered" style="margin-bottom: 6px">There are no blog posts at this time.</div>`
        }
    });
}

function tableLinks() {
    $(".clickable-row").click(function () {
        window.location = $(this).data("url");
    });
}