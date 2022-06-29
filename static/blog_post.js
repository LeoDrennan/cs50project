$(document).ready(function() {
    commentVoting();
    editComment();
    dropdown();
});

function commentVoting() {
    $(".voting-buttons").on("click", ".vote-button", function () {
        $.ajax({
            type : "POST",
            url : "/blog/AJAX_post",
            dataType: "json",
            contentType : "application/json",
            data : JSON.stringify ({
                commentID : $(this).val(),
                voteType : this.id
            }),
        })
        .done(function(data){
            // Upvote
            if (data.voteStatus == 1) {
                document.getElementById("buttons-" + data.commentID).innerHTML = `
                <span id="upvote-undo"><button class="btn btn-primary btn-sm vote-button" id="remove-upvote" value="${data.commentID}">Revert-U</button></span>
                <span id="karma">${data.karma}</span>
                <span id="downvote-button"><button class="btn btn-primary btn-sm vote-button" id="downvote" value="${data.commentID}">Downvote</button></span>
                `;
            // Downvote
            } else if (data.voteStatus == -1) {
                document.getElementById("buttons-" + data.commentID).innerHTML = `
                <span id="upvote-button"><button class="btn btn-primary btn-sm vote-button" id="upvote" value="${data.commentID}">Upvote</button></span>
                <span id="karma">${data.karma}</span>
                <span id="downvote-undo"><button class="btn btn-primary btn-sm vote-button" id="remove-downvote" value="${data.commentID}">Revert-D</button></span>
                `;
            // Removal of upvote or downvote
            } else {
                document.getElementById("buttons-" + data.commentID).innerHTML = `
                <span id ="upvote-button"><button class="btn btn-primary btn-sm vote-button" id="upvote" value="${data.commentID}">Upvote</button></span>
                <span id="karma">${data.karma}</span>
                <span id="downvote-button"><button class="btn btn-primary btn-sm vote-button" id="downvote" value="${data.commentID}">Downvote</button></span>
                `;
            }
        });
    });
}

function editComment() {
    $(".edit-comment").click(function() {
        var commentID = $(this).val();
        var url = window.location.href;
        var content = document.getElementById("body-" + commentID).innerHTML;
        document.getElementById("body-" + commentID).innerHTML = `
        <form action="${url}" method="post">
            <input type="hidden" name="type" value="edit">
            <input type="hidden" name="comment_id" value=${commentID}>
            <textarea class="form-control" id="content" name="content" rows="3">${content}</textarea>
            <span class="edit-buttons">
                <button class="btn btn-primary btn-sm" id="submitEdit" type="submit">Confirm Changes</button>
                <a href="${url}"><button class="btn btn-primary btn-sm" id="cancelEdit" type="button" onclick="return confirm('Are you sure you want to discard your changes?')">Cancel</button></a>
            </span>
        </form>
        `;
        $("#buttons-" + commentID).hide();
        $(".author-buttons").hide();
    });
}

function dropdown() {
    $("#collapseUp").hide();
    $("#collapseDown").click(function() {
        $("#collapseUp").show();
        $("#collapseDown").hide();
    });
    $("#collapseUp").click(function() {
        $("#collapseUp").hide();
        $("#collapseDown").show();
    });
}