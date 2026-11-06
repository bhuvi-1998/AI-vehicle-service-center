
const API_URL = window.API_BASE_URL;


/* =========================================
   APPOINTMENT TIME FORMATTING
========================================= */

function getAppointmentTimeParts(value) {
    const text = String(value ?? "").trim();

    // Handle time values stored as seconds since midnight.
    if (/^\d+$/.test(text)) {
        const totalSeconds = Number(text);

        if (!Number.isFinite(totalSeconds) || totalSeconds < 0) {
            return null;
        }

        return {
            hours: Math.floor(totalSeconds / 3600) % 24,
            minutes: Math.floor((totalSeconds % 3600) / 60)
        };
    }

    // Handle time strings such as 09:00:00 or 09:00.
    const match = text.match(/^(\d{1,2}):(\d{2})/);

    if (match) {
        const hours = Number(match[1]);
        const minutes = Number(match[2]);

        if (hours > 23 || minutes > 59) {
            return null;
        }

        return { hours, minutes };
    }

    return null;
}


function formatAppointmentTime(value) {
    const time = getAppointmentTimeParts(value);

    if (!time) {
        return value || "—";
    }

    const hour = time.hours % 12 || 12;
    const period = time.hours >= 12 ? "PM" : "AM";

    return `${hour}:${String(time.minutes).padStart(2, "0")} ${period}`;
}


function formatTimeInput(value) {
    const time = getAppointmentTimeParts(value);

    if (!time) {
        return "";
    }

    return `${String(time.hours).padStart(2, "0")}:${String(time.minutes).padStart(2, "0")}`;
}


/* =========================================
   HTML ELEMENTS
========================================= */

const appointmentForm =
    document.getElementById("appointmentForm");

const appointmentId =
    document.getElementById("appointment_id");

const customerSelect =
    document.getElementById("customer_id");

const vehicleSelect =
    document.getElementById("vehicle_id");

const serviceSelect =
    document.getElementById("service_id");

const technicianSelect =
    document.getElementById("technician_id");

const appointmentTable =
    document.getElementById("appointmentTable");

const requirementMessage =
    document.getElementById("requirementMessage");

const message =
    document.getElementById("message");

const cancelButton =
    document.getElementById("cancelButton");


/* =========================================
   DATA ARRAYS
========================================= */

let customers = [];
let vehicles = [];
let services = [];
let technicians = [];


/* =========================================
   LOAD CUSTOMERS
========================================= */

async function loadCustomers() {
    const response = await apiFetch(`${API_URL}/customers`);
    const result = await response.json();

    if (!response.ok) {
        throw new Error(
            result.detail || "Unable to load customers."
        );
    }

    customers = result;

    customerSelect.innerHTML =
        '<option value="">Select Customer</option>';

    customers.forEach(function(customer) {
        const option = document.createElement("option");

        option.value = customer.customer_id;
        option.textContent = customer.customer_name;

        customerSelect.appendChild(option);
    });
}


/* =========================================
   LOAD VEHICLES
========================================= */

async function loadVehicles() {
    const response = await apiFetch(`${API_URL}/vehicles`);
    const result = await response.json();

    if (!response.ok) {
        throw new Error(
            result.detail || "Unable to load vehicles."
        );
    }

    vehicles = result;
}


/* =========================================
   LOAD SERVICES
========================================= */

async function loadServices() {
    const response = await apiFetch(`${API_URL}/services`);
    const result = await response.json();

    if (!response.ok) {
        throw new Error(
            result.detail || "Unable to load services."
        );
    }

    services = result;

    serviceSelect.innerHTML =
        '<option value="">Select Service</option>';

    services.forEach(function(service) {
        const option = document.createElement("option");

        option.value = service.service_id;
        option.textContent =
            `${service.service_name} - ${service.price}`;

        serviceSelect.appendChild(option);
    });
}


/* =========================================
   LOAD TECHNICIANS
========================================= */

async function loadTechnicians() {
    const response = await apiFetch(`${API_URL}/technicians`);
    const result = await response.json();

    if (!response.ok) {
        throw new Error(
            result.detail || "Unable to load technicians."
        );
    }

    technicians = result;

    technicianSelect.innerHTML =
        '<option value="">Not Assigned</option>';

    technicians.forEach(function(technician) {
        const option = document.createElement("option");

        option.value = technician.technician_id;
        option.textContent = technician.technician_name;

        technicianSelect.appendChild(option);
    });
}


/* =========================================
   LOAD VEHICLES FOR SELECTED CUSTOMER
========================================= */

function loadCustomerVehicles(customerId) {
    vehicleSelect.innerHTML =
        '<option value="">Select Vehicle</option>';

    const selectedVehicles = vehicles.filter(function(vehicle) {
        return String(vehicle.customer_id) === String(customerId);
    });

    selectedVehicles.forEach(function(vehicle) {
        const option = document.createElement("option");

        option.value = vehicle.vehicle_id;
        option.textContent =
            `${vehicle.vehicle_number} - ${vehicle.brand} ${vehicle.model}`;

        vehicleSelect.appendChild(option);
    });
}


customerSelect.addEventListener("change", function() {
    loadCustomerVehicles(customerSelect.value);
});


/* =========================================
   LOAD APPOINTMENTS
========================================= */

async function loadAppointments() {
    const response = await apiFetch(`${API_URL}/appointments`);
    const appointments = await response.json();

    if (!response.ok) {
        throw new Error(
            appointments.detail || "Unable to load appointments."
        );
    }

    appointmentTable.innerHTML = "";

    appointments.forEach(function(appointment) {
        const row = document.createElement("tr");

        const idCell = document.createElement("td");
        idCell.textContent = appointment.appointment_id;

        const customerCell = document.createElement("td");
        customerCell.textContent = appointment.customer_name;

        const vehicleCell = document.createElement("td");
        vehicleCell.textContent = appointment.vehicle_number;

        const serviceCell = document.createElement("td");
        serviceCell.textContent = appointment.service_name;

        const technicianCell = document.createElement("td");
        technicianCell.textContent =
            appointment.technician_name || "Not Assigned";

        const dateCell = document.createElement("td");
        dateCell.textContent = appointment.appointment_date;

        const timeCell = document.createElement("td");
        timeCell.textContent =
            formatAppointmentTime(appointment.appointment_time);

        const statusCell = document.createElement("td");
        statusCell.textContent = appointment.status;

        const actionCell = document.createElement("td");

        const editButton = document.createElement("button");
        editButton.textContent = "Edit";

        editButton.addEventListener("click", function() {
            editAppointment(appointment);
        });

        const deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";

        deleteButton.addEventListener("click", function() {
            deleteAppointment(appointment.appointment_id);
        });

        actionCell.appendChild(editButton);
        actionCell.appendChild(document.createTextNode(" "));
        actionCell.appendChild(deleteButton);

        row.appendChild(idCell);
        row.appendChild(customerCell);
        row.appendChild(vehicleCell);
        row.appendChild(serviceCell);
        row.appendChild(technicianCell);
        row.appendChild(dateCell);
        row.appendChild(timeCell);
        row.appendChild(statusCell);
        row.appendChild(actionCell);

        appointmentTable.appendChild(row);
    });
}


/* =========================================
   CREATE OR UPDATE APPOINTMENT
========================================= */

appointmentForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const data = {
        customer_id: Number(customerSelect.value),

        vehicle_id: Number(vehicleSelect.value),

        service_id: Number(serviceSelect.value),

        technician_id: technicianSelect.value
            ? Number(technicianSelect.value)
            : null,

        appointment_date:
            document.getElementById("appointment_date").value,

        appointment_time:
            document.getElementById("appointment_time").value,

        status:
            document.getElementById("status").value
    };

    try {
        let response;

        if (appointmentId.value) {
            response = await apiFetch(
                `${API_URL}/appointments/${appointmentId.value}`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(data)
                }
            );
        } else {
            response = await apiFetch(
                `${API_URL}/appointments`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(data)
                }
            );
        }

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail || "Unable to save appointment."
            );
        }

        message.textContent = result.message;

        appointmentForm.reset();
        appointmentId.value = "";

        vehicleSelect.innerHTML =
            '<option value="">Select Vehicle</option>';

        cancelButton.hidden = true;

        await loadAppointments();

    } catch (error) {
        message.textContent =
            error.message || "Unable to save appointment.";
    }
});


/* =========================================
   EDIT APPOINTMENT
========================================= */

function editAppointment(appointment) {
    appointmentId.value = appointment.appointment_id;

    customerSelect.value = appointment.customer_id;

    loadCustomerVehicles(appointment.customer_id);

    vehicleSelect.value = appointment.vehicle_id;
    serviceSelect.value = appointment.service_id;
    technicianSelect.value = appointment.technician_id || "";

    document.getElementById("appointment_date").value =
        appointment.appointment_date;

    document.getElementById("appointment_time").value =
        formatTimeInput(appointment.appointment_time);

    document.getElementById("status").value =
        appointment.status;

    cancelButton.hidden = false;

    appointmentForm.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


/* =========================================
   CANCEL EDITING
========================================= */

cancelButton.addEventListener("click", function() {
    appointmentForm.reset();

    appointmentId.value = "";

    vehicleSelect.innerHTML =
        '<option value="">Select Vehicle</option>';

    cancelButton.hidden = true;
    message.textContent = "";
});


/* =========================================
   DELETE APPOINTMENT
========================================= */

async function deleteAppointment(id) {
    const confirmed = window.confirm(
        `Are you sure you want to delete appointment ${id}?`
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await apiFetch(
            `${API_URL}/appointments/${id}`,
            {
                method: "DELETE"
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail || "Unable to delete appointment."
            );
        }

        message.textContent = result.message;

        await loadAppointments();

    } catch (error) {
        message.textContent =
            error.message || "Unable to delete appointment.";
    }
}


/* =========================================
   INITIALIZE APPOINTMENT PAGE
========================================= */

async function initializePage() {
    try {
        await loadCustomers();
        await loadVehicles();
        await loadServices();
        await loadTechnicians();

        if (
            customers.length === 0 ||
            vehicles.length === 0 ||
            services.length === 0
        ) {
            requirementMessage.textContent =
                "A customer, vehicle, and service must exist before creating an appointment.";

            appointmentForm.hidden = true;
        } else {
            requirementMessage.textContent = "";
            appointmentForm.hidden = false;
        }

        await loadAppointments();

    } catch (error) {
        requirementMessage.textContent =
            error.message || "Unable to initialize appointments.";

        appointmentForm.hidden = true;
    }
}


initializePage();
