$(document).ready(function () {
  var drawButtons = $(".embody-get-drawing");
  var imageContainer = $(".embody-image-container");
  var progressBarContainer = $(".progress");
  var progressBar = $("#image-loading-progress");

  // With sockets
  function initConnection(socket) {
    socket.on("success", function (msg) {
      console.log(msg);
    });

    socket.on("progress", function (data) {
      progressBar.width(100 * (data.done / data.from) + "%");
    });

    socket.on("end", function (img) {
      // kill connection
      socket.emit("end");
      socket.disconnect();

      // Draw image to statistic -page
      var source = img.path;
      d = new Date();
      imageContainer.attr(
        "src",
        "/static/embody_drawings/" + source + "?" + d.getTime()
      );

      // Remove progress bar
      progressBarContainer.addClass("hidden");
      progressBar.width("0%");
    });
  }

  drawButtons.click(function (event) {
    event.preventDefault();

    // Init socket
    var socket = io.connect(getDrawingURI);
    initConnection(socket);

    var pageId = this.dataset.value.split("-")[0];
    var embodyId = this.dataset.value.split("-")[1];

    socket.emit("draw", { page: pageId, embody: embodyId });
    progressBarContainer.removeClass("hidden");

    scrollTo("plotted-image");
  });

  function scrollTo(hash) {
    $("html, body").animate(
      {
        scrollTop: $("#" + hash).offset().top - 250,
      },
      500
    );
  }
});
