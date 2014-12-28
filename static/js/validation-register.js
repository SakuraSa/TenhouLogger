$(function () {
    var inputUsername = $('input[name="username"]');
    var inputPassword = $('input[name="password"]');
    var inputPasswordConfirm = $('input[name="password_confirm"]');
    
    inputUsername.blur(function(){
        inputUsername.attr("disabled","disabled");
        var username = inputUsername.val();
        $.get('/api/get_username_availability?username=' + username, function (data, status) {
            var result = JSON.parse(data);
            if(result['availability']) {
                inputUsername.removeAttr("disabled");
                inputUsername.addClass('has-success');
            }
        })
    });
});