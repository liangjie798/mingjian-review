const header = document.querySelector('.site-header');
const revealItems = document.querySelectorAll('[data-reveal]');

function updateHeader() {
  header.classList.toggle('scrolled', window.scrollY > 20);
}

updateHeader();
window.addEventListener('scroll', updateHeader, { passive: true });
document.documentElement.classList.add('gsap-ready');

if (!window.gsap || !window.ScrollTrigger) {
  revealItems.forEach((item) => {
    item.style.visibility = 'visible';
    item.style.opacity = '1';
  });
} else {
  gsap.registerPlugin(ScrollTrigger);

  const media = gsap.matchMedia();
  media.add({
    reduceMotion: '(prefers-reduced-motion: reduce)',
    desktop: '(min-width: 901px)'
  }, (context) => {
    const { reduceMotion, desktop } = context.conditions;
    if (reduceMotion) {
      gsap.set(revealItems, { autoAlpha: 1, clearProps: 'transform' });
      return;
    }

    gsap.defaults({ duration: 0.9, ease: 'power3.out' });
    gsap.set(revealItems, { autoAlpha: 0, y: 34 });

    const intro = gsap.timeline({ defaults: { ease: 'power3.out' } });
    intro
      .from('.site-header', { y: -18, autoAlpha: 0, duration: 0.65 })
      .from('.hero-eyebrow', { x: -22, autoAlpha: 0, duration: 0.55 }, '-=.2')
      .from('.hero h1', { y: 45, autoAlpha: 0, duration: 1 }, '-=.25')
      .from('.hero-lead', { y: 24, autoAlpha: 0, duration: 0.7 }, '-=.58')
      .from('.hero-actions, .trust-row', { y: 18, autoAlpha: 0, stagger: 0.12, duration: 0.6 }, '-=.42')
      .from('.hero-visual', { x: 45, autoAlpha: 0, scale: .97, duration: 1.1 }, '-=.92');

    revealItems.forEach((item) => {
      gsap.to(item, {
        autoAlpha: 1,
        y: 0,
        scrollTrigger: {
          trigger: item,
          start: 'top 84%',
          once: true
        }
      });
    });

    gsap.to('.scroll-progress', {
      scaleX: 1,
      ease: 'none',
      scrollTrigger: { start: 0, end: 'max', scrub: .2 }
    });

    gsap.utils.toArray('.story-visual img, .workflow-visual img, .ecosystem-visual img').forEach((image) => {
      gsap.fromTo(image,
        { scale: 1.08, yPercent: -2 },
        {
          scale: 1,
          yPercent: 2,
          ease: 'none',
          scrollTrigger: {
            trigger: image,
            start: 'top bottom',
            end: 'bottom top',
            scrub: .8
          }
        }
      );
    });

    gsap.from('.provider-cloud span', {
      y: 16,
      autoAlpha: 0,
      stagger: .045,
      duration: .45,
      scrollTrigger: {
        trigger: '.provider-cloud',
        start: 'top 88%',
        once: true
      }
    });

    if (desktop) {
      const heroVisual = document.querySelector('.hero-visual');
      const handleMove = (event) => {
        const bounds = heroVisual.getBoundingClientRect();
        const x = (event.clientX - bounds.left) / bounds.width - .5;
        const y = (event.clientY - bounds.top) / bounds.height - .5;
        gsap.to(heroVisual, {
          rotationY: x * 3,
          rotationX: y * -3,
          transformPerspective: 900,
          duration: .55,
          overwrite: 'auto'
        });
      };
      const resetTilt = () => gsap.to(heroVisual, { rotationX: 0, rotationY: 0, duration: .7, overwrite: 'auto' });
      heroVisual.addEventListener('pointermove', handleMove);
      heroVisual.addEventListener('pointerleave', resetTilt);
      return () => {
        heroVisual.removeEventListener('pointermove', handleMove);
        heroVisual.removeEventListener('pointerleave', resetTilt);
      };
    }
  });
}
