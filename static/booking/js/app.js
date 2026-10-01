(() => {
  const API = '/api';
  const state = {
    access: localStorage.getItem('fixwell_access'),
    refresh: localStorage.getItem('fixwell_refresh'),
    user: null,
    services: [],
    technicians: [],
    selectedService: null,
    selectedSlot: null,
    slots: [],
    bookings: [],
    view: 'booking',
    appointmentFilter: 'upcoming',
    authMode: 'login',
  };

  const elements = Object.fromEntries([
    'service-list', 'service-count', 'technician-select', 'appointment-date', 'slot-list',
    'slot-date-label', 'booking-hint', 'book-button', 'customer-note', 'auth-dialog',
    'auth-form', 'auth-title', 'auth-subtitle', 'auth-error', 'auth-submit', 'name-fields',
    'first-name', 'last-name', 'auth-email', 'auth-password', 'sidebar-name', 'sidebar-email',
    'sidebar-avatar', 'account-action', 'mobile-account', 'booking-view', 'appointments-view',
    'appointment-list', 'appointment-count', 'current-section', 'toast',
  ].map((id) => [id, document.getElementById(id)]));

  const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);

  async function request(path, options = {}, retry = true) {
    const headers = new Headers(options.headers || {});
    if (state.access) headers.set('Authorization', `Bearer ${state.access}`);
    if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
    let response = await fetch(`${API}${path}`, { ...options, headers });
    if (response.status === 401 && state.refresh && retry && !path.startsWith('/auth/')) {
      const refreshed = await fetch(`${API}/auth/refresh/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: state.refresh }),
      });
      if (refreshed.ok) {
        const tokens = await refreshed.json();
        saveTokens(tokens.access, tokens.refresh || state.refresh);
        return request(path, options, false);
      }
      clearSession();
      updateAccount();
      throw new Error('Your session has expired. Please sign in again.');
    }
    const data = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) throw new Error(errorMessage(data, response.status));
    return data;
  }

  function errorMessage(data, status) {
    if (!data) return `Request failed (${status}).`;
    if (data.error?.message) return data.error.message;
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.non_field_errors)) return data.non_field_errors.join(' ');
    const messages = Object.entries(data).flatMap(([field, value]) => {
      const text = Array.isArray(value) ? value.join(' ') : typeof value === 'string' ? value : '';
      return text ? [`${field === 'email' ? 'Email' : field.replaceAll('_', ' ')}: ${text}`] : [];
    });
    return messages.join(' ') || `Request failed (${status}).`;
  }

  function saveTokens(access, refresh) {
    state.access = access;
    state.refresh = refresh;
    localStorage.setItem('fixwell_access', access);
    if (refresh) localStorage.setItem('fixwell_refresh', refresh);
  }

  function clearSession() {
    state.access = null;
    state.refresh = null;
    state.user = null;
    localStorage.removeItem('fixwell_access');
    localStorage.removeItem('fixwell_refresh');
  }

  function showToast(message, isError = false) {
    elements.toast.textContent = message;
    elements.toast.classList.toggle('is-error', isError);
    elements.toast.classList.add('is-visible');
    clearTimeout(showToast.timeout);
    showToast.timeout = setTimeout(() => elements.toast.classList.remove('is-visible'), 3600);
  }

  function updateAccount() {
    const signedIn = Boolean(state.user);
    const displayName = state.user ? `${state.user.first_name} ${state.user.last_name}`.trim() || state.user.email : 'Guest';
    elements['sidebar-name'].textContent = displayName;
    elements['sidebar-email'].textContent = state.user?.email || 'Sign in to continue';
    elements['sidebar-avatar'].textContent = displayName.charAt(0).toUpperCase();
    elements['account-action'].textContent = '↗';
    elements['account-action'].setAttribute('aria-label', signedIn ? 'Sign out' : 'Sign in');
    elements['mobile-account'].textContent = signedIn ? 'Sign out' : 'Sign in';
  }

  async function loadAccount() {
    if (!state.access) {
      updateAccount();
      return;
    }
    try {
      state.user = await request('/auth/me/');
      updateAccount();
      await loadBookings();
    } catch {
      clearSession();
      updateAccount();
    }
  }

  function formatMoney(value) {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(Number(value));
  }

  function renderServices() {
    const icons = ['⌁', '⌘', '⌖', '⌑', '⌂', '◈'];
    elements['service-count'].textContent = `${state.services.length} services`;
    if (!state.services.length) {
      elements['service-list'].innerHTML = '<div class="empty-state">No services are available right now.</div>';
      return;
    }
    elements['service-list'].innerHTML = state.services.map((service, index) => `
      <button class="service-card${state.selectedService?.id === service.id ? ' is-selected' : ''}" type="button" data-service-id="${service.id}" aria-pressed="${state.selectedService?.id === service.id}">
        <span class="service-card-top"><span class="service-symbol" aria-hidden="true">${icons[index % icons.length]}</span><span class="service-radio" aria-hidden="true"></span></span>
        <strong>${escapeHTML(service.name)}</strong>
        <small>${escapeHTML(service.description || 'Careful diagnosis and repair from an experienced technician.')}</small>
        <span class="service-card-footer"><span>${service.duration_minutes} min</span><b>${formatMoney(service.price)}</b></span>
      </button>`).join('');
    elements['service-list'].querySelectorAll('[data-service-id]').forEach((button) => {
      button.addEventListener('click', () => selectService(Number(button.dataset.serviceId)));
    });
  }

  async function loadServices() {
    try {
      const result = await request('/services/?is_active=true');
      state.services = Array.isArray(result) ? result : result.results || [];
      renderServices();
    } catch (error) {
      elements['service-list'].innerHTML = `<div class="empty-state">${escapeHTML(error.message)} <button type="button" class="inline-retry">Try again</button></div>`;
      elements['service-list'].querySelector('.inline-retry')?.addEventListener('click', loadServices);
    }
  }

  async function selectService(serviceId) {
    state.selectedService = state.services.find((service) => service.id === serviceId) || null;
    state.selectedSlot = null;
    renderServices();
    if (!state.user) {
      elements['booking-hint'].textContent = 'Sign in or create an account to choose a technician and time.';
      openAuth('login');
      return;
    }
    elements['booking-hint'].textContent = 'Choose a technician and date to see open appointments.';
    elements['technician-select'].disabled = true;
    elements['technician-select'].innerHTML = '<option value="">Loading technicians…</option>';
    elements['appointment-date'].disabled = true;
    elements['book-button'].disabled = true;
    elements['slot-list'].innerHTML = '<p class="empty-slots">Choose a technician and date to see open times.</p>';
    try {
      const result = await request(`/technicians/?service_id=${serviceId}&is_active=true`);
      state.technicians = (Array.isArray(result) ? result : result.results || []).filter((technician) => technician.is_active);
      elements['technician-select'].innerHTML = '<option value="">Select a technician</option>' + state.technicians.map((technician) => `<option value="${technician.id}">${escapeHTML(technician.name)}</option>`).join('');
      elements['technician-select'].disabled = !state.technicians.length;
      elements['appointment-date'].disabled = !state.technicians.length;
      elements['booking-hint'].textContent = state.technicians.length ? 'Pick a technician and date to find a time that works.' : 'No technicians are currently available for this service.';
    } catch (error) {
      elements['booking-hint'].textContent = error.message;
    }
  }

  function localISODate(date = new Date()) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function setMinimumDate() {
    const today = localISODate();
    elements['appointment-date'].min = today;
    elements['appointment-date'].value = today;
  }

  async function loadSlots() {
    const technicianId = elements['technician-select'].value;
    const date = elements['appointment-date'].value;
    state.selectedSlot = null;
    elements['book-button'].disabled = true;
    if (!state.selectedService || !technicianId || !date) {
      elements['slot-list'].innerHTML = '<p class="empty-slots">Choose a technician and date to see open times.</p>';
      return;
    }
    elements['slot-date-label'].textContent = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(`${date}T12:00:00`));
    elements['slot-list'].innerHTML = '<span class="spinner" aria-label="Loading available times"></span>';
    try {
      const data = await request(`/availability/?service_id=${state.selectedService.id}&technician_id=${technicianId}&date=${date}`);
      state.slots = data.slots || [];
      if (!state.slots.length) {
        elements['slot-list'].innerHTML = '<p class="empty-slots">No open times on this date. Try another day.</p>';
        return;
      }
      elements['slot-list'].innerHTML = state.slots.map((slot, index) => `<button class="slot-button" type="button" data-slot-index="${index}" aria-pressed="false">${escapeHTML(formatTime(slot.start))}</button>`).join('');
      elements['slot-list'].querySelectorAll('[data-slot-index]').forEach((button) => {
        button.addEventListener('click', () => {
          state.selectedSlot = state.slots[Number(button.dataset.slotIndex)];
          elements['slot-list'].querySelectorAll('.slot-button').forEach((item) => {
            const selected = item === button;
            item.classList.toggle('is-selected', selected);
            item.setAttribute('aria-pressed', String(selected));
          });
          elements['book-button'].disabled = false;
        });
      });
    } catch (error) {
      elements['slot-list'].innerHTML = `<p class="empty-slots">${escapeHTML(error.message)}</p>`;
    }
  }

  function formatTime(value) {
    const [hour, minute] = value.split(':').map(Number);
    const time = new Date();
    time.setHours(hour, minute, 0, 0);
    return new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(time);
  }

  async function createBooking() {
    if (!state.user) {
      openAuth('login');
      return;
    }
    if (!state.selectedService || !state.selectedSlot) return;
    const button = elements['book-button'];
    button.disabled = true;
    button.firstChild.textContent = 'Booking… ';
    const date = elements['appointment-date'].value;
    const startDatetime = new Date(`${date}T${state.selectedSlot.start}:00Z`).toISOString();
    try {
      await request('/bookings/', {
        method: 'POST',
        body: JSON.stringify({
          service_id: state.selectedService.id,
          technician_id: Number(elements['technician-select'].value),
          start_datetime: startDatetime,
          customer_note: elements['customer-note'].value.trim(),
        }),
      });
      elements['customer-note'].value = '';
      showToast('Your appointment is booked. We’ll take it from here.');
      await loadBookings();
      switchView('appointments');
      setAppointmentFilter('upcoming');
    } catch (error) {
      showToast(error.message, true);
      await loadSlots();
    } finally {
      button.innerHTML = 'Continue to booking <span aria-hidden="true">→</span>';
      button.disabled = !state.selectedSlot;
    }
  }

  async function loadBookings() {
    if (!state.user) return;
    try {
      const result = await request('/bookings/');
      state.bookings = Array.isArray(result) ? result : result.results || [];
      elements['appointment-count'].textContent = state.bookings.filter((booking) => ['PENDING', 'CONFIRMED'].includes(booking.status)).length;
      elements['appointment-count'].hidden = false;
      renderBookings();
    } catch (error) {
      showToast(error.message, true);
    }
  }

  function bookingDate(value) {
    return new Date(value);
  }

  function bookingIsUpcoming(booking) {
    return ['PENDING', 'CONFIRMED'].includes(booking.status) && bookingDate(booking.start_datetime) >= new Date();
  }

  function renderBookings() {
    if (!state.user) {
      elements['appointment-list'].innerHTML = '<div class="empty-appointments"><strong>Sign in to see your appointments</strong><p>Your bookings and repair history are saved to your account.</p></div>';
      return;
    }
    const filtered = state.bookings.filter((booking) => state.appointmentFilter === 'upcoming' ? bookingIsUpcoming(booking) : !bookingIsUpcoming(booking));
    if (!filtered.length) {
      const upcoming = state.appointmentFilter === 'upcoming';
      elements['appointment-list'].innerHTML = `<div class="empty-appointments"><strong>${upcoming ? 'Nothing on the calendar yet' : 'No past visits yet'}</strong><p>${upcoming ? 'When you book a repair, it will appear here.' : 'Completed and cancelled appointments will appear here.'}</p></div>`;
      return;
    }
    elements['appointment-list'].innerHTML = filtered.map((booking) => {
      const start = bookingDate(booking.start_datetime);
      const end = bookingDate(booking.end_datetime);
      const canCancel = bookingIsUpcoming(booking) && start.getTime() - Date.now() >= 2 * 60 * 60 * 1000;
      const day = new Intl.DateTimeFormat(undefined, { day: '2-digit' }).format(start);
      const month = new Intl.DateTimeFormat(undefined, { month: 'short' }).format(start);
      const dateText = new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).format(start);
      const timeText = `${formatDateTime(start)} – ${formatDateTime(end)}`;
      const statusClass = booking.status === 'CANCELLED' ? 'is-cancelled' : booking.status === 'COMPLETED' ? 'is-completed' : '';
      return `<article class="appointment-card">
        <div class="appointment-date"><strong>${day}</strong><span>${month}</span></div>
        <div class="appointment-main"><h3>${escapeHTML(booking.service.name)}</h3><p>${escapeHTML(dateText)} · ${escapeHTML(timeText)}</p><p>With ${escapeHTML(booking.technician.name)}</p></div>
        <div class="appointment-meta"><span class="status-pill ${statusClass}">${escapeHTML(statusLabel(booking.status))}</span><span class="appointment-price">${formatMoney(booking.price)}</span>${canCancel ? `<button class="cancel-link" type="button" data-cancel-id="${booking.id}">Cancel appointment</button>` : ''}</div>
      </article>`;
    }).join('');
    elements['appointment-list'].querySelectorAll('[data-cancel-id]').forEach((button) => {
      button.addEventListener('click', () => cancelBooking(Number(button.dataset.cancelId)));
    });
  }

  function formatDateTime(date) {
    return new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(date);
  }

  function statusLabel(status) {
    return ({ PENDING: 'Awaiting confirmation', CONFIRMED: 'Confirmed', CANCELLED: 'Cancelled', COMPLETED: 'Completed' })[status] || status;
  }

  async function cancelBooking(id) {
    if (!window.confirm('Cancel this appointment?')) return;
    try {
      await request(`/bookings/${id}/cancel/`, { method: 'POST', body: JSON.stringify({}) });
      showToast('Your appointment has been cancelled.');
      await loadBookings();
    } catch (error) {
      showToast(error.message, true);
    }
  }

  function switchView(view) {
    state.view = view;
    elements['booking-view'].hidden = view !== 'booking';
    elements['appointments-view'].hidden = view !== 'appointments';
    elements['current-section'].textContent = view === 'booking' ? 'Book a repair' : 'My appointments';
    document.querySelectorAll('.nav-item').forEach((button) => button.classList.toggle('is-active', button.dataset.view === view));
    if (view === 'appointments') renderBookings();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function setAppointmentFilter(filter) {
    state.appointmentFilter = filter;
    document.querySelectorAll('.appointment-tab').forEach((button) => {
      const selected = button.dataset.filter === filter;
      button.classList.toggle('is-selected', selected);
      button.setAttribute('aria-selected', String(selected));
    });
    renderBookings();
  }

  function openAuth(mode = 'login') {
    if (state.user) return;
    setAuthMode(mode);
    elements['auth-error'].hidden = true;
    elements['auth-dialog'].showModal();
  }

  function setAuthMode(mode) {
    state.authMode = mode;
    const registering = mode === 'register';
    elements['auth-title'].textContent = registering ? 'Create your account' : 'Welcome back';
    elements['auth-subtitle'].textContent = registering ? 'A few details and you’re ready to book.' : 'Sign in to book a visit and manage your appointments.';
    elements['name-fields'].hidden = !registering;
    elements['first-name'].required = registering;
    elements['last-name'].required = registering;
    elements['auth-password'].autocomplete = registering ? 'new-password' : 'current-password';
    elements['auth-submit'].innerHTML = `${registering ? 'Create account' : 'Sign in'} <span aria-hidden="true">→</span>`;
    document.querySelectorAll('.auth-tab').forEach((button) => button.classList.toggle('is-selected', button.dataset.authMode === mode));
  }

  async function submitAuth(event) {
    event.preventDefault();
    const registering = state.authMode === 'register';
    const email = elements['auth-email'].value.trim();
    const password = elements['auth-password'].value;
    elements['auth-error'].hidden = true;
    elements['auth-submit'].disabled = true;
    elements['auth-submit'].firstChild.textContent = registering ? 'Creating account… ' : 'Signing in… ';
    try {
      if (registering) {
        await request('/auth/register/', {
          method: 'POST',
          body: JSON.stringify({ email, password, first_name: elements['first-name'].value.trim(), last_name: elements['last-name'].value.trim() }),
        });
      }
      const tokens = await request('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) });
      saveTokens(tokens.access, tokens.refresh);
      state.user = await request('/auth/me/');
      updateAccount();
      await loadBookings();
      elements['auth-dialog'].close();
      showToast(registering ? 'Your account is ready. Let’s book your repair.' : 'Welcome back.');
      if (state.selectedService) await selectService(state.selectedService.id);
    } catch (error) {
      elements['auth-error'].textContent = error.message;
      elements['auth-error'].hidden = false;
    } finally {
      elements['auth-submit'].disabled = false;
      setAuthMode(state.authMode);
    }
  }

  function handleAccountAction() {
    if (state.user) {
      clearSession();
      state.bookings = [];
      updateAccount();
      if (state.view === 'appointments') renderBookings();
      elements['appointment-count'].hidden = true;
      showToast('You’re signed out.');
      return;
    }
    openAuth('login');
  }

  document.querySelectorAll('.nav-item').forEach((button) => button.addEventListener('click', () => {
    const view = button.dataset.view;
    if (view === 'appointments' && !state.user) {
      openAuth('login');
      return;
    }
    switchView(view);
  }));
  document.querySelectorAll('.appointment-tab').forEach((button) => button.addEventListener('click', () => setAppointmentFilter(button.dataset.filter)));
  document.querySelectorAll('.auth-tab').forEach((button) => button.addEventListener('click', () => setAuthMode(button.dataset.authMode)));
  elements['technician-select'].addEventListener('change', loadSlots);
  elements['appointment-date'].addEventListener('change', loadSlots);
  elements['book-button'].addEventListener('click', createBooking);
  elements['auth-form'].addEventListener('submit', submitAuth);
  elements['account-action'].addEventListener('click', handleAccountAction);
  elements['mobile-account'].addEventListener('click', handleAccountAction);
  document.getElementById('new-booking-button').addEventListener('click', () => switchView('booking'));
  setMinimumDate();
  loadServices();
  loadAccount();
})();