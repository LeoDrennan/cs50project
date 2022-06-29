$(document).ready(function() {
    mealCounter();
    carouselCounter();
});

function mealCounter() {
    $(".mealOption").click(function() {
        var checkboxes = $("input:checkbox:checked").length;
        document.getElementById("selected").innerHTML = checkboxes + "/" + totalMeals;
        if (checkboxes == totalMeals) {
            document.getElementById("mealSubmit").disabled = false;

        } else {
            document.getElementById("mealSubmit").disabled = true;
        }
    });
}

function carouselCounter() {
    var totalPages = $(".carousel-item").length;
    document.getElementById("pages").innerHTML = "1/" + totalPages;

    $("#menuCarousel").on("slid.bs.carousel", function() {
        var currentPage = $("div.active").index() + 1;
        document.getElementById("pages").innerHTML = currentPage + "/" + totalPages;
    });
}