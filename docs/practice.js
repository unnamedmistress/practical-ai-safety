document.querySelectorAll('[data-result]').forEach(button => { button.addEventListener('click', () => { button.closest('.exercise').querySelector('.feedback').textContent = button.dataset.result; }); });

document.querySelectorAll('.carousel').forEach(carousel => {
  const track = carousel.querySelector('.slide-track');
  const slides = [...track.querySelectorAll('.slide')];
  const previous = carousel.querySelector('.previous');
  const next = carousel.querySelector('.next');
  const status = carousel.querySelector('.slide-status');
  let current = 0;
  const sync = () => {
    const max = track.scrollWidth - track.clientWidth;
    current = track.scrollLeft >= max - 3 ? slides.length - 1 : slides.reduce((best, slide, i) => Math.abs(slide.offsetLeft - slides[0].offsetLeft - track.scrollLeft) < Math.abs(slides[best].offsetLeft - slides[0].offsetLeft - track.scrollLeft) ? i : best, 0);
    previous.disabled = track.scrollLeft <= 3;
    next.disabled = track.scrollLeft >= max - 3;
    status.textContent = `${current + 1} of ${slides.length}`;
  };
  const move = direction => {
    const target = slides[Math.max(0, Math.min(slides.length - 1, current + direction))];
    track.scrollTo({left: target.offsetLeft - slides[0].offsetLeft, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
  };
  previous.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  track.addEventListener('keydown', event => {if (event.target !== track) return; if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {event.preventDefault();move(event.key === 'ArrowRight' ? 1 : -1);}});
  let timer;
  track.addEventListener('scroll', () => {clearTimeout(timer);timer=setTimeout(sync,120);});
  window.addEventListener('resize', sync);
  carousel.querySelector('.carousel-controls').hidden = false;
  sync();
});
