
let board_children = {};

function update_board(board_id) {
    $.ajax({
        url: 'api/board/' + board_id,
        dataType: 'json'
    }).done(function (data) {
        board_children = data.children;
        $("#board").attr('src', 'svg/board/' + data.id);
    })
}

$(document).ready(function (e) {

    update_board('initial');

    $('#board').mousedown(function (e) {
        var posX = e.pageX - $(this).offset().left;
        var posY = e.pageY - $(this).offset().top;

        var field_width = $(this).width() / 8;
        var field_height = $(this).height() / 8;

        var field_id = 8 * Math.floor(posY / field_width) + Math.floor(posX / field_height);

        if (field_id in board_children) {
            update_board(board_children[field_id].id);
        }
    });

    $('#new_game').click(function (e) {
        update_board('initial');
    });

    $('#xot_game').click(function (e) {
        update_board('xot');
    });
});
