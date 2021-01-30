
let board = {};
let mode = "game";
let training = {
    openings: [],
    opening_id: 0,
    step_id: 0,
    mistakes: {},
};

function shuffle_array(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function update_board(board_id, mistakes = '') {
    $.ajax({
        url: 'api/boards/' + board_id,
        dataType: 'json'
    }).done(function (data) {
        board = data;
        $("#board").attr('src', 'svg/boards/' + data.id + '?mistakes=' + mistakes);
    });
}

$(document).ready(function (e) {

    update_board('initial');

    $('#board').mousedown(function (e) {
        let posX = e.pageX - $(this).offset().left;
        let posY = e.pageY - $(this).offset().top;

        let field_width = $(this).width() / 8;
        let field_height = $(this).height() / 8;

        let field_id = 8 * Math.floor(posY / field_width) + Math.floor(posX / field_height);

        if (field_id in board.children) {
            if (mode == "game") {
                update_board(board.children[field_id].id);
            }
            if (mode == "training") {
                best_field_id = training.openings[training.opening_id][training.step_id].best_child;
                if (field_id == best_field_id) {
                    console.log(training.openings[training.opening_id].length);
                    if (training.step_id < training.openings[training.opening_id].length - 1) {
                        training.step_id += 1;
                    } else if (training.opening_id < training.openings.length) {
                        training.opening_id += 1;
                        training.step_id = 0;
                    } else {
                        // we've gone through all openings
                        return;
                    }

                    update_board(training.openings[training.opening_id][training.step_id].board);
                    training.mistakes = {};

                } else {
                    if (field_id in training.mistakes) {
                        return;
                    }
                    training.mistakes[field_id] = true;
                    mistakes = Object.keys(training.mistakes).join(',');
                    update_board(board.id, mistakes);
                }
            }
        }
    });

    $('#new_game').click(function (e) {
        update_board('initial');
    });

    $('#xot_game').click(function (e) {
        update_board('xot');
    });

    $('#training').click(function (e) {
        $.ajax({
            url: 'api/openings',
            dataType: 'json'
        }).done(function (data) {
            shuffle_array(data);
            training.openings = data;
            mode = "training";
            training.opening_id = 0;
            training.move_id = 0;
            update_board(data[0][0].board);
        });
    });
});
