$(document).ready(function() {
    initialiseTables();
    tableLinks();
    toggleTable();
});

function initialiseTables() {
    $("#postHistory").dataTable({
        "pagingType" : "simple_numbers",
        "lengthChange" : false,
        "order": [],
        "language": {
            "emptyTable" : `<div class="centered" style="margin-bottom: 6px">You have not created any blog posts.</div>
                            <div class="centered"><a href="/blog"><button class="btn btn-primary">Blog</button></a>`
        }
    });
    $("#commentHistory").dataTable({
        "pagingType" : "simple_numbers",
        "lengthChange" : false,
        "order": [],
        "language": {
            "emptyTable" : `<div class="centered" style="margin-bottom: 6px">You have not created any comments.</div>
                            <div class="centered"><a href="/blog"><button class="btn btn-primary">Blog</button></a>`
        }
    });
    $("#commentHistory_wrapper").hide();
}

function tableLinks() {
    $(".clickable-row").click(function () {
        window.location = $(this).data("url");
    });
}

function toggleTable() {
    $("#showComments").click(function() {
        $("#postHistory_wrapper").hide();
        $("#commentHistory_wrapper").show();
    })

    $("#showPosts").click(function() {
        $("#postHistory_wrapper").show();
        $("#commentHistory_wrapper").hide();
    })
}