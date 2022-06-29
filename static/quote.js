$(document).ready(function() {
    var peopleSlider = document.getElementById("people");
    var mealsSlider = document.getElementById("meals");
    var peopleOutput = document.getElementById("peopleOutput");
    var mealsOutput = document.getElementById("mealsOutput");
    peopleOutput.innerHTML = peopleSlider.value;
    mealsOutput.innerHTML = mealsSlider.value;

    peopleSlider.oninput = function() {
        peopleOutput.innerHTML = this.value;
    }

    mealsSlider.oninput = function() {
        mealsOutput.innerHTML = this.value;
    }
});

$(document).ready(function() {
    $(".slider").on("change", function () {
        $.ajax({
            type : "POST",
            url : "/AJAX_quote",
            dataType: "json",
            contentType : "application/json",
            data : JSON.stringify ({
                peopleValue : $("#people").val(),
                mealsValue : $("#meals").val()
            }),
        })
        .done(function(data){
            document.getElementById("quote").innerHTML = "Your weekly price: £" + data +".00";
        });
    });
});