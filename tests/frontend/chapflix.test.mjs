import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import vm from "node:vm";

const NO_UPDATE = Symbol("no_update");
const SOURCE = readFileSync(
  new URL("../../app/assets/chapflix.js", import.meta.url),
  "utf8",
);

/**
 * Values created inside the vm sandbox have the sandbox's prototypes, which
 * strict deep equality treats as different, so copy them into this realm.
 */
function toLocalRealm(value) {
  if (Array.isArray(value)) {
    return Array.from(value, toLocalRealm);
  }
  if (value === null || typeof value !== "object") {
    return value;
  }
  return JSON.parse(JSON.stringify(value));
}

function loadChapflix() {
  const window = { dash_clientside: { no_update: NO_UPDATE } };
  vm.runInNewContext(SOURCE, { window });
  return Object.fromEntries(
    Object.entries(window.dash_clientside.chapflix).map(([name, fn]) => [
      name,
      (...args) => toLocalRealm(fn(...args)),
    ]),
  );
}

const { trackPlayback, renderUpNext, dismissUpNext } = loadChapflix();
const PLAY_ID = 1700000000000;
const EPISODE = {
  play_id: PLAY_ID,
  file_key: 74,
  media_type: "show",
  duration: 1325,
};

function at(type, position) {
  return { type, "target.currentTime": position };
}

test("no countdown while more than ten seconds remain", () => {
  const [, countdown] = trackPlayback(at("timeupdate", 1300), EPISODE, null);
  assert.equal(countdown, NO_UPDATE);
});

test("countdown starts ten seconds before the end", () => {
  const [, countdown] = trackPlayback(at("timeupdate", 1315), EPISODE, null);
  assert.deepEqual(countdown, { play_id: PLAY_ID, seconds: 10 });
});

test("countdown rounds partial seconds up", () => {
  const [, countdown] = trackPlayback(at("timeupdate", 1316.4), EPISODE, null);
  assert.deepEqual(countdown, { play_id: PLAY_ID, seconds: 9 });
});

test("countdown only updates when the whole second changes", () => {
  const current = { play_id: PLAY_ID, seconds: 9 };
  const [, countdown] = trackPlayback(
    at("timeupdate", 1316.6),
    EPISODE,
    current,
  );
  assert.equal(countdown, NO_UPDATE);
});

test("seeking back out of the window clears the countdown", () => {
  const current = { play_id: PLAY_ID, seconds: 5 };
  const [, countdown] = trackPlayback(at("timeupdate", 600), EPISODE, current);
  assert.equal(countdown, null);
});

test("countdown never goes negative", () => {
  const [, countdown] = trackPlayback(at("timeupdate", 1330), EPISODE, null);
  assert.deepEqual(countdown, { play_id: PLAY_ID, seconds: 0 });
});

test("films never count down", () => {
  const film = { ...EPISODE, media_type: "film" };
  const [, countdown] = trackPlayback(at("timeupdate", 1320), film, null);
  assert.equal(countdown, NO_UPDATE);
});

test("pauses are recorded against the file", () => {
  const [paused] = trackPlayback(at("pause", 42), EPISODE, null);
  assert.deepEqual(paused, { file_key: 74, seconds: 42 });
});

test("the pause fired by reaching the end is not recorded", () => {
  const [paused] = trackPlayback(at("pause", 1324.8), EPISODE, null);
  assert.equal(paused, NO_UPDATE);
});

test("the end of playback is reported for the current playback", () => {
  const [, , ended] = trackPlayback({ type: "ended" }, EPISODE, null);
  assert.deepEqual(ended, { play_id: PLAY_ID });
});

test("events before anything plays are ignored", () => {
  assert.deepEqual(trackPlayback(at("timeupdate", 1), null, null), [
    NO_UPDATE,
    NO_UPDATE,
    NO_UPDATE,
  ]);
});

const UP_NEXT = {
  play_id: PLAY_ID,
  selection: {},
  title: "The Simpsons · S4 E4",
};

test("up next shows the queued episode and seconds left", () => {
  const countdown = { play_id: PLAY_ID, seconds: 8 };
  assert.deepEqual(renderUpNext(countdown, UP_NEXT, null), [
    "up-next up-next--visible",
    "The Simpsons · S4 E4",
    "Starting in 8…",
  ]);
});

test("up next says starting at zero", () => {
  const countdown = { play_id: PLAY_ID, seconds: 0 };
  assert.equal(renderUpNext(countdown, UP_NEXT, null)[2], "Starting…");
});

test("up next stays hidden once dismissed for this playback", () => {
  const countdown = { play_id: PLAY_ID, seconds: 8 };
  const dismissed = { play_id: PLAY_ID };
  assert.equal(renderUpNext(countdown, UP_NEXT, dismissed)[0], "up-next");
});

test("a dismissal from an earlier playback doesn't hide up next", () => {
  const countdown = { play_id: PLAY_ID, seconds: 8 };
  const dismissed = { play_id: PLAY_ID - 1 };
  assert.equal(
    renderUpNext(countdown, UP_NEXT, dismissed)[0],
    "up-next up-next--visible",
  );
});

test("up next stays hidden when there's no next episode", () => {
  const countdown = { play_id: PLAY_ID, seconds: 8 };
  const empty = { ...UP_NEXT, selection: null };
  assert.equal(renderUpNext(countdown, empty, null)[0], "up-next");
});

test("up next stays hidden when queued for an earlier playback", () => {
  const countdown = { play_id: PLAY_ID, seconds: 8 };
  const stale = { ...UP_NEXT, play_id: PLAY_ID - 1 };
  assert.equal(renderUpNext(countdown, stale, null)[0], "up-next");
});

test("stay here dismisses the current playback", () => {
  const countdown = { play_id: PLAY_ID, seconds: 6 };
  assert.deepEqual(dismissUpNext(1, countdown), { play_id: PLAY_ID });
});
