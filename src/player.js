/** Framework-independent, once-only player. Returns a cleanup function. */
export function mountACEAnimation(container, { baseURL = './exports/', label = 'Automated Concessions and Entertainment' } = {}) {
  const url = name => new URL(name, new URL(baseURL, document.baseURI)).href;
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const still = document.createElement('img');
  still.src = url('ace-hero-final-frame.png');
  still.alt = label; still.width = 768; still.height = 1024;
  Object.assign(container.style, { position: 'relative', aspectRatio: '3 / 4' });
  Object.assign(still.style, { display: 'block', width: '100%', height: '100%', objectFit: 'contain' });
  container.append(still);
  let video;
  const stop = () => { still.style.visibility = 'visible'; if (video) { video.pause(); video.replaceChildren(); video.removeAttribute('src'); video.load(); video.remove(); video = undefined; } };
  const start = () => {
    if (motion.matches || video) return;
    video = document.createElement('video');
    video.muted = true; video.playsInline = true; video.loop = false;
    video.setAttribute('aria-hidden', 'true'); video.tabIndex = -1;
    Object.assign(video.style, { position: 'absolute', inset: '0', width: '100%', height: '100%', objectFit: 'contain' });
    // WebM alpha on Chromium/Firefox. H.264 fallback has an opaque dark background.
    const webm = document.createElement('source'); webm.src = url('ace-hero-animation.webm'); webm.type = 'video/webm; codecs="vp9"';
    const mp4 = document.createElement('source'); mp4.src = url('ace-hero-animation.mp4'); mp4.type = 'video/mp4';
    // A source-selection failure may never reject play() or fire video.error.
    mp4.addEventListener('error', stop, { once: true });
    video.append(webm, mp4);
    video.addEventListener('playing', () => { still.style.visibility = 'hidden'; }, { once: true });
    video.addEventListener('ended', stop, { once: true });
    video.addEventListener('error', stop, { once: true });
    container.append(video);
    video.play().catch(stop);
  };
  const onMotionChange = () => { if (motion.matches) stop(); };
  motion.addEventListener('change', onMotionChange);
  start();
  return () => { motion.removeEventListener('change', onMotionChange); stop(); still.remove(); };
}
