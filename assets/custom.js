document.addEventListener("DOMContentLoaded", function () {
  // Toggle controls when entering/exiting fullscreen
  document.addEventListener("fullscreenchange", function () {
    const video = document.getElementById("Player");
    if (document.fullscreenElement && document.fullscreenElement === video) {
      video.controls = false;
    } else {
      video.controls = true;
    }
  });
});
