


$( document ).ready( function() {
    $('#embody-file-input, .custom-file-input').change(function(filename) {

        var label = $(this).next('.custom-file-label');

        //replace the "Choose a file" label
        $.each($(this).prop("files") ,function (index, value) {
            if (index === 0) {
                label.html(value.name)
            } else {
                label.append(', ' + value.name)
            }
        })

        $('.submit-file').prop("disabled", false);
    })
})
