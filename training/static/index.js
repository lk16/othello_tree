$(document).ready(function (e) {

    $('#board').click(function (e) {
        var posX = e.pageX - $(this).offset().left;
        var posY = e.pageY - $(this).offset().top;

        var field_width = $(this).width() / 8;
        var field_height = $(this).height() / 8;

        var field_id = 8 * Math.floor(posY / field_width) + Math.floor(posX / field_height);
        console.log(field_id);
    });
});
