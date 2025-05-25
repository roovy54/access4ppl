
$(document).ready(function(event) {

  $('#submit').on('click', function(event) {
    // Submitting the form always returns a vague error message
    var heading = $('<div>').addClass('errorHeading').text('ERROR');
    var errorMsg = $('<p>')
      .text('Your form has errors. Please correct them and resubmit.');
    $('#error').html(heading).append(errorMsg).show();
    // Announce the error message for screen readers
    $('#aria-live-region').text('Your form has errors. Please correct them and resubmit.');
    event.preventDefault();
  });
});
