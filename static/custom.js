console.log('js file loading')

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

  // Attach pause handler, retry until video element exists
  function attachPauseHandler() {
    const video = document.getElementById("Player");
    if (video) {
      console.log("Attaching pause handler");
      video.addEventListener("pause", function () {
        const progress = video.currentTime;
        console.log("Paused at:", progress);
        const input = document.getElementById("VideoProgressInput");
        if (input) {
          input.value = progress;
          input.dispatchEvent(new Event("input", { bubbles: true }));
        }
      });
    } else {
      console.log("Video element not found, retrying...");
      setTimeout(attachPauseHandler, 500);
    }
  }

  attachPauseHandler();
});


console.log('js file loaded')