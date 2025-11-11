/**
 * Fuel cards flip controls.
 * Keeps pager dots in sync and maintains accessible state.
 */
(function () {
  function setActiveDots(cardEl, side) {
    cardEl.querySelectorAll('.pager-dots .dot').forEach((dot) => {
      const isActive = dot.getAttribute('data-side') === side;
      dot.classList.toggle('is-active', isActive);
      dot.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
  }

  function toggleFlip(wrapperEl, toBack) {
    wrapperEl.classList.toggle('is-flipped', toBack);
  }

  function initFuelCards(root = document) {
    root.querySelectorAll('.fuel-card').forEach((card) => {
      const wrapper = card.closest('.flip-card');
      if (!wrapper) return;

      // Default view = front
      setActiveDots(card, 'front');
      toggleFlip(wrapper, false);

      card.addEventListener('click', (event) => {
        const dot = event.target.closest('.pager-dots .dot');
        if (!dot) return;

        event.preventDefault();
        const side = dot.getAttribute('data-side');
        const showBack = side === 'back';
        toggleFlip(wrapper, showBack);
        setActiveDots(card, showBack ? 'back' : 'front');
      });
    });
  }

  // expose for manual re-initialization
  window.initFuelCards = initFuelCards;

  document.addEventListener('DOMContentLoaded', () => initFuelCards());
  document.addEventListener('shown.bs.modal', (event) => {
    if (event.target && event.target.querySelector('.fuel-card')) {
      initFuelCards(event.target);
    }
  });
})();

