window.onload = function(){
  var ver_code_input = $("input#ver_code");
  var image = $("img#ver_image");
  var container = $("<div></div>");
  container.append(image);
  ver_code_input.popover({
    trigger:"manual",
    title:"验证码",
    html:true,
    placement:"top",
    content:container.html()
  });
  ver_code_input.focus(function () {
    ver_code_input.popover('show');
  });
  ver_code_input.blur(function () {
    ver_code_input.popover('hide');
  });
};