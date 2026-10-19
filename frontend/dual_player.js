/*
 * dual_player.js - play YouTube's split video/audio streams in a plain <video>.
 *
 * Qt WebEngine can decode VP9/AV1 + Opus (WebM) but not H.264/AAC.  YouTube only
 * serves those free codecs as separate video-only and audio-only files, so the
 * video goes in the <video> element and the sound in a hidden <audio> element
 * that this helper keeps in lock-step (play / pause / seek / speed / volume).
 *
 * Usage:
 *   const info = await (await fetch(`/api/stream?url=${enc}&format_id=${q}`)).json();
 *   siphonPlay(videoEl, info);          // info = response of /api/stream
 */
(function (global) {
  "use strict";

  const DRIFT_LIMIT = 0.25; // seconds of audio/video drift tolerated before re-syncing

  function proxify(url) {
    return "/api/proxy?url=" + encodeURIComponent(url);
  }

  // Keep `audio` synchronised with `video`. Returns a detach() function.
  function attachAudio(video, audio) {
    const safePlay = () => { const p = audio.play(); if (p && p.catch) p.catch(() => {}); };
    const sync = () => {
      if (Math.abs(audio.currentTime - video.currentTime) > DRIFT_LIMIT) {
        try { audio.currentTime = video.currentTime; } catch (e) { /* not seekable yet */ }
      }
    };
    const on = {
      play:         () => { sync(); safePlay(); },
      playing:      () => { sync(); if (audio.paused) safePlay(); },
      pause:        () => audio.pause(),
      waiting:      () => audio.pause(),          // video is buffering -> hold the sound
      seeking:      () => { try { audio.currentTime = video.currentTime; } catch (e) {} },
      seeked:       sync,
      timeupdate:   sync,
      ratechange:   () => { audio.playbackRate = video.playbackRate; },
      volumechange: () => { audio.volume = video.volume; audio.muted = video.muted; },
      ended:        () => audio.pause(),
    };
    Object.keys(on).forEach((ev) => video.addEventListener(ev, on[ev]));
    on.volumechange();
    on.ratechange();

    return function detach() {
      Object.keys(on).forEach((ev) => video.removeEventListener(ev, on[ev]));
      audio.pause();
      audio.removeAttribute("src");
      audio.load();
    };
  }

  /*
   * Load a /api/stream response into a <video>.  Keeps the playback position when
   * called again for a quality switch.  Returns { audio, detach }.
   */
  function siphonPlay(video, info, opts) {
    opts = opts || {};
    if (video.__siphonDetach) { video.__siphonDetach(); video.__siphonDetach = null; }

    const resumeAt = opts.resumeAt != null ? opts.resumeAt : 0;
    const wasPlaying = opts.autoplay !== false;

    video.src = proxify(info.stream_url);
    video.load();
    if (resumeAt > 0) {
      video.addEventListener("loadedmetadata", function once() {
        video.removeEventListener("loadedmetadata", once);
        video.currentTime = resumeAt;
      });
    }

    let audio = null;
    let detach = function () {};
    if (info.separate_audio && info.audio_url) {
      audio = new Audio();
      audio.preload = "auto";
      audio.src = proxify(info.audio_url);
      detach = attachAudio(video, audio);
      video.__siphonDetach = detach;
    }
    if (wasPlaying) {
      // play() issued before the stream is ready can be cancelled by the browser, so
      // ask once now and again as soon as enough data has arrived.
      const start = () => { const p = video.play(); if (p && p.catch) p.catch(() => {}); };
      video.addEventListener("canplay", function once() {
        video.removeEventListener("canplay", once);
        if (video.paused) start();
      });
      start();
    }
    return { audio: audio, detach: detach };
  }

  global.siphonPlay = siphonPlay;
})(window);