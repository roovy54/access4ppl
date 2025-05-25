
$(document).ready(function(event) {

  $('a[href="cheatsheet.html"]').on('click', function(event) {
    showModal();
    event.preventDefault();
  });

  // handle click on X or Ok button in modal dialog
  $('#modalContent button').on('click', function() { 
    console.log('you clicked a button');     
    hideModal();     
  });

  // handle keyboard interaction for modal
  $(document).on('keydown', function(event) {
    if (event.key === 'Escape') {
      hideModal();
    }
  });

  function showModal() {
    var winWidth = $(window).width();
    var winHeight = $(window).height();
    var modalSize = 400;
    var modalLeft = ((winWidth - modalSize) / 2) + 'px';
    var modalTop = ((winHeight - modalSize) / 2) + 'px';

    $('#modalContent')
      .css({
        'top': modalTop,
        'left': modalLeft
      })
      .show();

    $('#modalMask').show();
    // Set focus to the modal
    $('#modalContent').attr('tabindex', '-1').focus();
  }

  function hideModal() {
    $('#modalContent').hide(); 
    $('#modalMask').hide();
  }
});
