
let board = {};
let mode = "game";
let training = {
    openings: [],
    opening_id: 0,
    step_id: 0,
    mistakes: {},
    flawless: true,
    total_openings: 0,
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

function update_training_stats() {
    let done = training.total_openings - training.openings.length;
    let total = training.total_openings;
    let ratio = Math.floor(100 * done / total);

    let text = "Training: " + done + " / " + total + " = " + ratio + "%";
    $('.training-stats-wrapper').text(text);
}

$(document).ready(function (e) {

    $('.training-stats-wrapper').hide();
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
                if (training.openings.length == 0) {
                    return;
                }

                best_field_id = training.openings[training.opening_id][training.step_id].best_child;
                if (field_id == best_field_id) {

                    if (training.step_id < training.openings[training.opening_id].length - 1) {
                        // more steps remain in this opening
                        training.step_id += 1;
                    }

                    else {
                        // this opening is over, next one

                        if (training.flawless) {
                            // no mistakes, remove opening from openings list
                            training.openings.splice(training.opening_id, 1);

                            // wrap around if this was the last opening
                            training.opening_id = training.opening_id % training.openings.length;

                            update_training_stats();
                        }
                        else {
                            // mistakes were made, don't remove, wrap around if necessary
                            training.opening_id = (training.opening_id + 1) % training.openings.length;
                        }
                        training.step_id = 0;
                        training.flawless = true;
                    }

                    if (training.openings.length == 0) {
                        return;
                    }

                    update_board(training.openings[training.opening_id][training.step_id].board);
                    training.mistakes = {};

                } else {
                    if (field_id in training.mistakes) {
                        return;
                    }
                    training.mistakes[field_id] = true;
                    training.flawless = false;
                    mistakes = Object.keys(training.mistakes).join(',');
                    update_board(board.id, mistakes);
                }
            }
        }
    });

    $('#new_game').click(function (e) {
        update_board('initial');
        $('.training-stats-wrapper').hide();
        mode = "game";
    });

    $('#xot_game').click(function (e) {
        update_board('xot');
        $('.training-stats-wrapper').hide();
        mode = "game";
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
            training.flawless = true;
            training.total_openings = data.length;
            update_training_stats();
            update_board(data[0][0].board);
        });
        $('.training-stats-wrapper').show();
    });
});
