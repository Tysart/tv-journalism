/* ==========================================================================
   «ТЕЛЕЖУРНАЛИСТИКА С НУЛЯ» — INTERACTIVITY SCRIPT
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile Drawer Toggle
  const burgerBtn = document.getElementById('burgerBtn');
  const drawerClose = document.getElementById('drawerClose');
  const mobileDrawer = document.getElementById('mobileDrawer');
  const drawerLinks = document.querySelectorAll('.drawer-link');

  if (burgerBtn && mobileDrawer) {
    burgerBtn.addEventListener('click', () => {
      mobileDrawer.classList.add('active');
      document.body.style.overflow = 'hidden';
    });
  }

  if (drawerClose && mobileDrawer) {
    drawerClose.addEventListener('click', () => {
      mobileDrawer.classList.remove('active');
      document.body.style.overflow = '';
    });
  }

  drawerLinks.forEach(link => {
    link.addEventListener('click', () => {
      mobileDrawer.classList.remove('active');
      document.body.style.overflow = '';
    });
  });

  // Radio button highlight
  const payMethods = document.querySelectorAll('.pay-method');
  payMethods.forEach(method => {
    method.addEventListener('click', () => {
      payMethods.forEach(m => m.classList.remove('active'));
      method.classList.add('active');
      const radio = method.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
    });
  });

  // Sticky Navbar Blur on Scroll
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 30) {
      navbar.style.background = 'rgba(5, 8, 17, 0.95)';
      navbar.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.5)';
    } else {
      navbar.style.background = 'rgba(7, 11, 20, 0.85)';
      navbar.style.boxShadow = 'none';
    }
  });
});

// Accordion for Modules
function toggleModule(header) {
  const block = header.closest('.module-block');
  const isOpen = block.classList.contains('open');

  // Optional: close other modules if desired
  // document.querySelectorAll('.module-block').forEach(b => b.classList.remove('open'));

  if (isOpen) {
    block.classList.remove('open');
  } else {
    block.classList.add('open');
  }
}

// Accordion for FAQ
function toggleFaq(question) {
  const item = question.closest('.faq-item');
  const isOpen = item.classList.contains('open');

  // Close other FAQs for smooth reading
  document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));

  if (!isOpen) {
    item.classList.add('open');
  }
}

// Payment Modal Logic
function openPaymentModal(tariffName, price) {
  const modal = document.getElementById('paymentModal');
  const nameEl = document.getElementById('modalTariffName');
  const priceEl = document.getElementById('modalTariffPrice');

  if (nameEl) nameEl.textContent = tariffName;
  if (priceEl) priceEl.textContent = Number(price).toLocaleString('ru-RU') + ' ₽';

  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closePaymentModal() {
  const modal = document.getElementById('paymentModal');
  modal.classList.remove('active');
  document.body.style.overflow = '';
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
  const modal = document.getElementById('paymentModal');
  if (e.target === modal) {
    closePaymentModal();
  }
});

// Handle form submission
function handlePaymentSubmit(e) {
  e.preventDefault();

  const name = document.getElementById('studentName').value;
  const email = document.getElementById('studentEmail').value;
  const tg = document.getElementById('studentTelegram').value;
  const method = document.querySelector('input[name="paymethod"]:checked').value;
  const tariffName = document.getElementById('modalTariffName').textContent;
  const tariffPrice = document.getElementById('modalTariffPrice').textContent;

  const submitBtn = document.querySelector('.btn-submit-pay');
  const originalText = submitBtn.innerHTML;

  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>Формирование счёта...</span>`;

  setTimeout(() => {
    alert(`Спасибо, ${name}!\n\nВы выбрали тариф: «${tariffName}» (${tariffPrice}).\n\nСпособ оплаты: ${method === 'yookassa' ? 'ЮKassa (Карта / СБП)' : 'Telegram-бот'}.\n\n(Здесь происходит защищённый переход на платежный шлюз ЮKassa или в Telegram-бот @tyshchenko_tv_bot).`);
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
    closePaymentModal();
  }, 900);
}
