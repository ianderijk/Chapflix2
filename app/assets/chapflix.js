/**
 * Clientside callbacks for playback.
 *
 * The video reports its position several times a second. Handling that in the
 * browser keeps the server out of the loop until something meaningful happens:
 * a pause to record, the countdown ticking over a whole second, or the end.
 */

const COUNTDOWN_SECONDS = 10;
const END_OF_PLAYBACK_SECONDS = 1;

function noUpdate() {
  return window.dash_clientside.no_update;
}

function secondsRemaining(event, playRequest) {
  return playRequest.duration - event["target.currentTime"];
}

function countdownFor(event, playRequest) {
  if (playRequest.media_type !== "show") {
    return null;
  }
  const remaining = secondsRemaining(event, playRequest);
  if (remaining > COUNTDOWN_SECONDS) {
    return null;
  }
  return {
    play_id: playRequest.play_id,
    seconds: Math.max(0, Math.ceil(remaining)),
  };
}

function isSameCountdown(current, next) {
  if (!current || !next) {
    return !current && !next;
  }
  return current.play_id === next.play_id && current.seconds === next.seconds;
}

function pausedAt(event, playRequest) {
  if (secondsRemaining(event, playRequest) < END_OF_PLAYBACK_SECONDS) {
    return noUpdate();
  }
  return {
    file_key: playRequest.file_key,
    seconds: event["target.currentTime"],
  };
}

function trackPlayback(event, playRequest, countdown) {
  if (!event || !playRequest) {
    return [noUpdate(), noUpdate(), noUpdate()];
  }
  switch (event.type) {
    case "pause":
      return [pausedAt(event, playRequest), noUpdate(), noUpdate()];
    case "ended":
      return [noUpdate(), noUpdate(), { play_id: playRequest.play_id }];
    case "timeupdate": {
      const next = countdownFor(event, playRequest);
      const changed = !isSameCountdown(countdown, next);
      return [noUpdate(), changed ? next : noUpdate(), noUpdate()];
    }
    default:
      return [noUpdate(), noUpdate(), noUpdate()];
  }
}

function isUpNextVisible(countdown, upNext, dismissed) {
  if (!countdown || !upNext || !upNext.selection) {
    return false;
  }
  if (upNext.play_id !== countdown.play_id) {
    return false;
  }
  return !dismissed || dismissed.play_id !== countdown.play_id;
}

function renderUpNext(countdown, upNext, dismissed) {
  if (!isUpNextVisible(countdown, upNext, dismissed)) {
    return ["up-next", "", ""];
  }
  const count =
    countdown.seconds > 0 ? `Starting in ${countdown.seconds}…` : "Starting…";
  return ["up-next up-next--visible", upNext.title, count];
}

function dismissUpNext(nClicks, countdown) {
  if (!nClicks || !countdown) {
    return noUpdate();
  }
  return { play_id: countdown.play_id };
}

window.dash_clientside = Object.assign({}, window.dash_clientside, {
  chapflix: { trackPlayback, renderUpNext, dismissUpNext },
});
