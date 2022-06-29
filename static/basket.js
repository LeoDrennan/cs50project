$(document).ready(function() {
    totalCost();
});

function totalCost() {
    $(".quantitySelect").on("change", function () {
        $.ajax({
            type : "POST",
            url : "/basket_change",
            dataType: "json",
            contentType : "application/json",
            data : JSON.stringify ({
                quantity : $(this).val(),
                product_id : this.id
            }),
        })
        .done(function(data){
            document.getElementById("output").innerHTML = "£" + data + ".00";
        });
    });
}