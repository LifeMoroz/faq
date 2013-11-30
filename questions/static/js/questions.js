// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// get django CSRF token from cookies
var csrftoken = getCookie('csrftoken');

// ASK overlay form open
$('#ask_form_button').click(function () {
    var form_data = $('form#ask_form').serialize();

    $.post('/ask', form_data, function (data) {
            if (data.status == 'ok') {
                window.location.replace(data.url);
            } else {
                $('#ask_form_html').html(data.html);
                $("#question_tags").tagit({availableTags: all_tags, autocomplete: {delay: 0, minLength: 2}});
            }
        }
    );
});


// AJAX vote api
$('.votelink').click(function (e) {
    e.preventDefault();
    var url = $(this).data('link');
    var rating = $(this).parent('.vote-buttons').find('.rating-value');

    $.ajax({
        url: url,
        type: 'post',
        dataType:  'json',
        data: {'csrfmiddlewaretoken': csrftoken},
        success: function (data) {
            if (data.status == 'success' && data.action != 'vote')
                location.reload();

            if (data.action == 'vote') {
                rating.html(data['rating']);
                noty({text: data['message'],
                    type: data['status'],
                    'layout':'topLeft',
                    'timeout': 500,
                    closeWith: ['hover', 'click']})
            }
        },
        error: function(data) {
               noty({text: 'Action not permitted for you',
                   type: 'error',
                   'layout':'topLeft',
                   'timeout': 5000,
                   closeWith: ['hover', 'click']})
        }});
});

$('.message').bind('closed.bs.alert', function () {
    var url = $(this).data('dismiss_url');
    $.post(url, {'csrfmiddlewaretoken': csrftoken}, function (data) {
        if (data.status == 'ok')
            console.log('Message dismissed!');
        console.log(data);
    });
});
