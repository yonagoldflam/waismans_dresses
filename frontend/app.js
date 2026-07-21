// API_BASE_URL is defined in config.js. This file keeps the client and admin UI logic separate by section.
const form = document.querySelector('#booking-form');
const dateInput = document.querySelector('#appointment-date');
const timeSlots = document.querySelector('#time-slots');
const availabilityMessage = document.querySelector('#availability-message');
const continueButton = document.querySelector('#continue-button');
const selectedAppointment = document.querySelector('#selected-appointment');
const formError = document.querySelector('#form-error');

let selectedTime = null;
let adminToken = null; // Deliberately not persisted in localStorage.
const weekDays = ['יום שני', 'יום שלישי', 'יום רביעי', 'יום חמישי', 'יום שישי', 'שבת', 'יום ראשון'];

function todayInLocalTimezone() { const today = new Date(); today.setMinutes(today.getMinutes() - today.getTimezoneOffset()); return today.toISOString().slice(0, 10); }
function formatTime(time) { return String(time).slice(0, 5); }
function showStep(stepId) { document.querySelectorAll('#booking-form .step').forEach((step) => step.classList.add('hidden')); document.querySelector(stepId).classList.remove('hidden'); }
function selectedDateLabel() { return new Intl.DateTimeFormat('he-IL', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date(`${dateInput.value}T12:00:00`)); }
function showPanel(name) { document.querySelector('#booking-panel').classList.toggle('hidden', name !== 'booking'); document.querySelector('#admin-panel').classList.toggle('hidden', name !== 'admin'); document.querySelectorAll('[data-panel]').forEach((link) => link.classList.toggle('active', link.dataset.panel === name)); }
dateInput.min = todayInLocalTimezone();

async function loadAvailableSlots() {
  selectedTime = null; continueButton.disabled = true; timeSlots.innerHTML = ''; availabilityMessage.textContent = 'מחפשים שעות פנויות…';
  try {
    const response = await fetch(`${API_BASE_URL}/appointments/available-slots?target_date=${dateInput.value}`);
    const slots = await response.json();
    if (!response.ok) throw new Error(slots.detail || 'לא הצלחנו לטעון שעות פנויות.');
    if (!slots.length) { availabilityMessage.textContent = 'אין שעות פנויות בתאריך זה. נסי יום אחר.'; return; }
    availabilityMessage.textContent = 'בחרי שעה.';
    slots.forEach((slot) => { const button = document.createElement('button'); button.type = 'button'; button.className = 'time-slot'; button.textContent = formatTime(slot.start_time); button.addEventListener('click', () => { document.querySelectorAll('.time-slot').forEach((item) => item.classList.remove('selected')); button.classList.add('selected'); selectedTime = formatTime(slot.start_time); continueButton.disabled = false; }); timeSlots.appendChild(button); });
  } catch (error) { availabilityMessage.textContent = error.message || 'לא ניתן להתחבר לשרת.'; }
}

function readableApiError(detail) {
  if (Array.isArray(detail)) {
    return detail.map((error) => `${error.loc.at(-1)}: ${error.msg}`).join(' | ');
  }
  return detail || 'לא ניתן לקבוע את המדידה כרגע.';
}

async function submitBooking(event) {
  event.preventDefault();
  formError.textContent = '';

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }
  if (!selectedTime) {
    formError.textContent = 'יש לבחור שעה לפני אישור המדידה.';
    return;
  }

  // The API payload is written explicitly so every required field is visible here.
  const values = {
    customer_name: document.querySelector('#customer-name').value.trim(),
    customer_email: document.querySelector('#customer-email').value.trim(),
    customer_phone: document.querySelector('#customer-phone').value.trim(),
    slot_date: dateInput.value,
    start_time: selectedTime,
  };

  const submitButton = document.querySelector('#submit-button');
  submitButton.disabled = true;
  submitButton.textContent = 'שולחים…';

  try {
    const response = await fetch(`${API_BASE_URL}/appointments/book`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    });
    const result = await response.json();

    if (!response.ok) throw new Error(readableApiError(result.detail));

    document.querySelector('#success-message').textContent = `המדידה נקבעה ל־${selectedAppointment.textContent}. אישור נשלח ל־${values.customer_email}.`;
    showStep('#step-success');
  } catch (error) {
    formError.textContent = error.message || 'אירעה שגיאה. נסי שוב.';
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = 'אישור המדידה';
  }
}

// All admin requests pass the token only in the Authorization header.
async function adminRequest(path, options = {}) {
  const headers = { 'X-Admin-Token': encodeURIComponent(adminToken), ...options.headers };
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || 'הפעולה נכשלה.');
  return body;
}

async function loadAdminData() {
  const status = document.querySelector('#admin-status');
  status.textContent = 'טוען נתונים…';

  try {
    const [appointments, slots] = await Promise.all([
      adminRequest('/admin/appointments?limit=100'),
      adminRequest('/admin/slots'),
    ]);
    renderAppointments(appointments);
    renderSlots(slots);
    status.textContent = `עודכן: ${new Date().toLocaleTimeString('he-IL')}`;
  } catch (error) {
    status.textContent = error.message;
    throw error;
  }
}
function renderAppointments(appointments) { const list = document.querySelector('#appointments-list'); if (!appointments.length) { list.innerHTML = '<p class="hint">אין תורים להצגה.</p>'; return; } list.innerHTML = appointments.map((item) => `<article><strong>${item.customer_name}</strong><span>${item.slot_date} · ${formatTime(item.start_time)}</span><span>${item.customer_phone} · ${item.customer_email}</span></article>`).join(''); }
function renderSlots(slots) { const list = document.querySelector('#slots-list'); if (!slots.length) { list.innerHTML = '<p class="hint">אין חלונות זמן מוגדרים.</p>'; return; } list.innerHTML = slots.map((slot) => `<article><strong>${weekDays[slot.day_of_week]}</strong><span>${formatTime(slot.start_time)}–${formatTime(slot.end_time)} · עד ${slot.max_capacity} לקוחות</span><button class="delete-slot" data-slot-id="${slot.id}">מחיקה</button></article>`).join(''); }

// Customer page events.
dateInput.addEventListener('change', loadAvailableSlots);
continueButton.addEventListener('click', () => { selectedAppointment.textContent = `${selectedDateLabel()} · ${selectedTime}`; showStep('#step-details'); });
document.querySelector('#back-button').addEventListener('click', () => showStep('#step-date-time'));
form.addEventListener('submit', submitBooking);
document.querySelector('#new-booking-button').addEventListener('click', () => { form.reset(); timeSlots.innerHTML = ''; availabilityMessage.textContent = 'בחרי תאריך כדי לראות שעות פנויות.'; selectedTime = null; continueButton.disabled = true; showStep('#step-date-time'); });

// Admin page events.
document.querySelectorAll('[data-panel]').forEach((link) => link.addEventListener('click', (event) => { event.preventDefault(); showPanel(link.dataset.panel); }));
document.querySelector('#admin-login-form').addEventListener('submit', async (event) => {
  event.preventDefault();

  const errorMessage = document.querySelector('#admin-login-error');
  const loginButton = event.currentTarget.querySelector('button[type="submit"]');
  errorMessage.textContent = '';
  adminToken = document.querySelector('#admin-token').value.trim();

  if (!adminToken) {
    errorMessage.textContent = 'יש להזין Admin token.';
    return;
  }

  loginButton.disabled = true;
  loginButton.textContent = 'מתחבר…';
  try {
    await loadAdminData();
    document.querySelector('#admin-login').classList.add('hidden');
    document.querySelector('#admin-dashboard').classList.remove('hidden');
  } catch (error) {
    errorMessage.textContent = error.message || 'לא ניתן להתחבר עם הטוקן הזה.';
    adminToken = null;
  } finally {
    loginButton.disabled = false;
    loginButton.textContent = 'כניסה לפאנל';
  }
});
document.querySelector('#admin-refresh').addEventListener('click', loadAdminData);
document.querySelector('#admin-logout').addEventListener('click', () => { adminToken = null; document.querySelector('#admin-token').value = ''; document.querySelector('#admin-dashboard').classList.add('hidden'); document.querySelector('#admin-login').classList.remove('hidden'); });
document.querySelector('#slot-form').addEventListener('submit', async (event) => { event.preventDefault(); const error = document.querySelector('#slot-error'); error.textContent = ''; const data = { day_of_week: Number(document.querySelector('#slot-day').value), start_time: document.querySelector('#slot-start').value, end_time: document.querySelector('#slot-end').value, max_capacity: Number(document.querySelector('#slot-capacity').value) }; try { await adminRequest('/admin/slots', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); event.target.reset(); document.querySelector('#slot-capacity').value = 1; await loadAdminData(); } catch (reason) { error.textContent = reason.message; } });
document.querySelector('#slots-list').addEventListener('click', async (event) => { const button = event.target.closest('.delete-slot'); if (!button || !confirm('למחוק את חלון הזמן הזה?')) return; try { await adminRequest(`/admin/slots/${button.dataset.slotId}`, { method: 'DELETE' }); await loadAdminData(); } catch (error) { document.querySelector('#admin-status').textContent = error.message; } });



