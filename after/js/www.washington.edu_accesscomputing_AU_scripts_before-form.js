
$(document).ready(function(event) {

  $('#submit').on('click', function(event) {
    // Submitting the form always returns a vague error message
    var heading = $('<div>').addClass('errorHeading').text('ERROR');
    var errorMsg = $('<p>')
      .text('Your form has errors. Please correct them and resubmit.');
    $('#error').html(heading).append(errorMsg).show();

    // Announce the error message to assistive technologies
    var liveRegion = $('<div aria-live="assertive" style="position:absolute; left:-9999px;">Your form has errors. Please correct them and resubmit.</div>');
    $('body').append(liveRegion);
    setTimeout(function() {
      liveRegion.remove();
    }, 1000);

    event.preventDefault();
  });
});
