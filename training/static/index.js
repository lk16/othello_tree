
let board_children = {};
let board_turn = "black";

function check_bot_to_move() {
    console.log(board_turn);
    if (board_turn == "black" && $('select[name=black_player]').val() == "bot") {
        return true;
    }

    if (board_turn == "white" && $('select[name=white_player]').val() == "bot") {
        return true;
    }

    return false;
}

function bot_maybe_move(board_id) {
    if (!check_bot_to_move()) {
        return;
    }

    $.ajax({
        url: 'api/bot-moves/' + board_id,
        dataType: 'json'
    }).done(function (data) {
        update_board(data.id);
    });
}


function update_board(board_id) {
    $.ajax({
        url: 'api/boards/' + board_id,
        dataType: 'json',
    }).done(function (data) {
        board_children = data.children;
        board_turn = data.turn;
        $("#board").attr('src', 'svg/boards/' + data.id);
        bot_maybe_move(data.id);
    });
}

$(document).ready(function (_e) {

    update_board('initial');

    $('#board').mousedown(function (e) {

        if (check_bot_to_move()) {
            return;
        }

        var posX = e.pageX - $(this).offset().left;
        var posY = e.pageY - $(this).offset().top;

        var field_width = $(this).width() / 8;
        var field_height = $(this).height() / 8;

        var field_id = 8 * Math.floor(posY / field_width) + Math.floor(posX / field_height);

        if (field_id in board_children) {
            update_board(board_children[field_id].id);
        }
    });

    $('#new_game').click(function (_e) {
        update_board('initial');
    });

    $('#xot_game').click(function (_e) {
        update_board('xot');
    });
});
