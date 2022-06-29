$(document).ready(function() {
    initialiseTables();
    tableLinks();
    toggleTable();
});

function initialiseTables() {
    $("#shopOrders").dataTable({
        "pagingType" : "simple_numbers",
        "lengthChange" : false,
        "order": [],
        "language": {
            "emptyTable" : `<div class="centered" style="margin-bottom: 6px">You have not purchased anything from our shop.</div>
                            <div class="centered"><a href="/shop"><button class="btn btn-primary">Shop</button></a>`
        }
    });
    $("#foodOrders").dataTable({
        "pagingType" : "simple_numbers",
        "lengthChange" : false,
        "order": [],
        "language": {
            "emptyTable" : `<div class="centered" style="margin-bottom: 6px">You have not purchased any of our meals.</div>
                            <div class="centered"><a href="/quote"><button class="btn btn-primary">Get started</button></a>`
        }
    });
    $("#foodOrders_wrapper").hide();
}

function tableLinks() {
    $(".clickable-row").click(function () {
        window.location = $(this).data("url");
    });
}

function toggleTable() {
    $("#showFood").click(function() {
        $("#shopOrders_wrapper").hide();
        $("#foodOrders_wrapper").show();
    })

    $("#showShop").click(function() {
        $("#shopOrders_wrapper").show();
        $("#foodOrders_wrapper").hide();
    })
}