
const APPOINTMENT_API = window.API_BASE_URL;

async function loadMyAppointments() {
    const token = localStorage.getItem("customer_access_token");
    const message = document.getElementById("appointmentsMessage");
    const list = document.getElementById("appointmentsList");

    if (!token) {
        window.location.replace("login.html");
        return;
    }

    try {
        const response = await fetch(`${APPOINTMENT_API}/customer-portal/appointments`, {
            headers: { Authorization: `Bearer ${token}` }
        });

        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem("customer_access_token");
            window.location.replace("login.html");
            return;
        }

        const appointments = await response.json();

        if (!response.ok) {
            throw new Error(appointments.detail || "Unable to load appointments.");
        }

        list.replaceChildren();

        if (!appointments.length) {
            message.textContent = "You don't have any service appointments yet.";
            return;
        }

        message.textContent = `You have ${appointments.length} appointment(s).`;

        appointments.forEach(appointment => {
            const card = document.createElement("article");
            card.className = "appointment-card";

            const title = document.createElement("h2");
            title.textContent = appointment.service_name;

            const vehicle = document.createElement("p");
            vehicle.textContent =
                `Vehicle: ${appointment.vehicle_number} — ${appointment.brand} ${appointment.model}`;

            const date = document.createElement("p");
            date.textContent =
                `Date: ${appointment.appointment_date} at ${appointment.appointment_time}`;

            const price = document.createElement("p");
            price.textContent =
                `Service price: ₹${Number(appointment.price).toLocaleString("en-IN")}`;

            const status = document.createElement("p");
            status.className = "appointment-status";
            status.textContent = `Current status: ${appointment.status}`;

            const id = document.createElement("p");
            id.textContent = `Appointment ID: ${appointment.appointment_id}`;

            card.append(title, id, vehicle, date, price, status);
            list.appendChild(card);
        });
    } catch (error) {
        message.textContent = error.message || "Could not connect to the server.";
    }
}

loadMyAppointments();
