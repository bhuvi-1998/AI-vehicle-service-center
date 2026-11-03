(function () {
    // Prevent duplicate chatbot instances.
    if (document.getElementById("vsc-chatbot-button")) {
        return;
    }

    const API_BASE_URL = "http://127.0.0.1:8000";

    // Detect whether the customer or admin dashboard is open.
    const isCustomerPage =
        window.location.pathname.toLowerCase().includes("/customer-portal/");

    // Appointment booking conversation state.
    const bookingState = {
        step: null,
        vehicles: [],
        services: [],
        matchingServices: [],
        selectedVehicle: null,
        selectedService: null,
        appointmentDate: null,
        appointmentTime: null
    };

    const managementState = {
        action: null,
        step: null,
        appointments: [],
        selectedAppointment: null,
        newDate: null,
        newTime: null
    };
    let requestInProgress = false;
    // Admin appointment status conversation.
    const adminStatusState = {
        step: null,
        appointment: null,
        requestedStatus: null
    };

    // Admin technician assignment conversation.
    const adminTechnicianState = {
        step: null,
        appointment: null,
        technician: null
    };

    // Admin stock, estimate, invoice and payment confirmation.
    const adminActionState = {
        step: null,
        type: null,
        endpoint: null,
        method: null,
        body: null,
        preview: null
    };


    const button = document.createElement("button");
    button.id = "vsc-chatbot-button";
    button.type = "button";
    button.textContent = "💬";
    button.setAttribute("aria-label", "Open vehicle service assistant");
    button.setAttribute("aria-expanded", "false");

    const panel = document.createElement("section");
    panel.id = "vsc-chatbot-panel";
    panel.setAttribute("aria-label", "Vehicle Service Assistant");

    panel.innerHTML = `
        <header class="vsc-chatbot-header">
            <div>
                <div class="vsc-chatbot-heading">
                    Vehicle Service Assistant
                </div>
                <div class="vsc-chatbot-subtitle">
                    How can I help you today?
                </div>
            </div>
            <button id="vsc-chatbot-close"
                    type="button"
                    aria-label="Close chat">&times;</button>
        </header>

        <div id="vsc-chatbot-messages" aria-live="polite">
            <div class="vsc-chatbot-message vsc-chatbot-bot">
                Hello! I can answer vehicle questions, check your appointments,
                and help you book a service.
                Try asking: "Book a service".
            </div>
        </div>

        <form id="vsc-chatbot-form">
            <input
                id="vsc-chatbot-input"
                type="text"
                placeholder="Type your message..."
                aria-label="Your message"
                autocomplete="off"
                required
            >
            <button id="vsc-chatbot-send" type="submit">Send</button>
        </form>
    `;

    // Load chatbot stylesheet.
    const scriptUrl = document.currentScript.src;
    const stylesheet = document.createElement("link");

    stylesheet.rel = "stylesheet";
    stylesheet.href = new URL("chatbot.css", scriptUrl).href;

    document.head.appendChild(stylesheet);
    document.body.appendChild(panel);
    document.body.appendChild(button);

    const closeButton = document.getElementById("vsc-chatbot-close");
    const form = document.getElementById("vsc-chatbot-form");
    const input = document.getElementById("vsc-chatbot-input");
    const messages = document.getElementById("vsc-chatbot-messages");
    const sendButton = document.getElementById("vsc-chatbot-send");

    function toggleChat(open) {
        panel.classList.toggle("vsc-chatbot-open", open);
        button.setAttribute("aria-expanded", String(open));

        if (open) {
            input.focus();
        }
    }

    button.addEventListener("click", function () {
        toggleChat(!panel.classList.contains("vsc-chatbot-open"));
    });

    closeButton.addEventListener("click", function () {
        toggleChat(false);
        button.focus();
    });

    // Display messages safely as text.
    function addMessage(text, sender) {
        const message = document.createElement("div");

        message.className =
            "vsc-chatbot-message vsc-chatbot-" + sender;

        message.textContent = text;
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
    }

    // Reset the appointment booking conversation.
    function resetBookingState() {
        bookingState.step = null;
        bookingState.vehicles = [];
        bookingState.services = [];
        bookingState.matchingServices = [];
        bookingState.selectedVehicle = null;
        bookingState.selectedService = null;
        bookingState.appointmentDate = null;
        bookingState.appointmentTime = null;
    }

    // Make authenticated requests to existing customer APIs.
    async function customerApi(path, options = {}) {
        const token = localStorage.getItem("customer_access_token");

        if (!token) {
            throw new Error(
                "Please log in to your customer account first."
            );
        }

        const headers = {
            ...(options.headers || {}),
            Authorization: `Bearer ${token}`
        };

        if (options.body !== undefined) {
            headers["Content-Type"] = "application/json";
        }

        const response = await fetch(
            `${API_BASE_URL}${path}`,
            {
                ...options,
                headers
            }
        );

        const data = await response.json().catch(() => ({}));

        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem("customer_access_token");

            throw new Error(
                "Your customer session has expired. Please log in again."
            );
        }

        if (!response.ok) {
            const error = new Error(
                data.detail || "The request failed."
            );

            error.status = response.status;
            throw error;
        }

        return data;
    }

    // ------------------------------------------
    // APPOINTMENT BOOKING
    // ------------------------------------------

    function normalizeValue(value) {
        return String(value || "")
            .toLowerCase()
            .replace(/[^a-z0-9]/g, "");
    }

    function resolveChoice(message, items, type) {
        const value = message.trim();

        // Allow selecting by displayed option number.
        if (/^\d+$/.test(value)) {
            const index = Number(value) - 1;

            if (index >= 0 && index < items.length) {
                return {
                    item: items[index],
                    ambiguous: false
                };
            }
        }

        const normalized = normalizeValue(value);

        if (!normalized) {
            return { item: null, ambiguous: false };
        }

        function getLabels(item) {
            if (type === "vehicle") {
                return [
                    item.vehicle_number,
                    `${item.brand} ${item.model}`
                ];
            }

            return [item.service_name];
        }

        const exactMatches = items.filter(item =>
            getLabels(item).some(
                label => normalizeValue(label) === normalized
            )
        );

        if (exactMatches.length === 1) {
            return {
                item: exactMatches[0],
                ambiguous: false
            };
        }

        if (exactMatches.length > 1) {
            return { item: null, ambiguous: true };
        }

        const partialMatches = items.filter(item =>
            getLabels(item).some(
                label =>
                    normalized.length >= 3 &&
                    normalizeValue(label).includes(normalized)
            )
        );

        if (partialMatches.length === 1) {
            return {
                item: partialMatches[0],
                ambiguous: false
            };
        }

        return {
            item: null,
            ambiguous: partialMatches.length > 1
        };
    }

    async function startAppointmentBooking() {
        if (!isCustomerPage) {
            addMessage(
                "Please log in to your customer dashboard to book an appointment.",
                "bot"
            );
            return;
        }

        addMessage(
            "I'll help you book a service. Let me check your registered vehicles and available services.",
            "bot"
        );

        const [vehicles, services] = await Promise.all([
            customerApi("/customer-portal/vehicles"),
            customerApi("/customer-portal/services")
        ]);

        if (!Array.isArray(vehicles) || !Array.isArray(services)) {
            throw new Error(
                "I received an unexpected response from the server."
            );
        }

        if (vehicles.length === 0) {
            addMessage(
                "You haven't registered a vehicle yet. Please add your vehicle in the customer dashboard before booking a service.",
                "bot"
            );
            return;
        }

        if (services.length === 0) {
            addMessage(
                "There are currently no services available for booking. Please contact the service center.",
                "bot"
            );
            return;
        }

        resetBookingState();

        bookingState.vehicles = vehicles;
        bookingState.services = services;
        bookingState.step = "vehicle";

        const vehicleList = vehicles.map((vehicle, index) => {
            const type = vehicle.vehicle_type || "Car";

            return (
                `${index + 1}. ${vehicle.vehicle_number} - ` +
                `${vehicle.brand} ${vehicle.model} (${type})`
            );
        });

        addMessage(
            "Which vehicle would you like to service?\n\n" +
            vehicleList.join("\n") +
            "\n\nReply with the option number or vehicle registration number. " +
            "You can reply CANCEL to stop.",
            "bot"
        );
    }

    function validateBookingDate(value) {
        const match =
            /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());

        if (!match) {
            return {
                valid: false,
                message: "Please enter the date in YYYY-MM-DD format, for example 2026-12-15."
            };
        }

        const year = Number(match[1]);
        const month = Number(match[2]);
        const day = Number(match[3]);

        const selectedDate = new Date(year, month - 1, day);

        if (
            selectedDate.getFullYear() !== year ||
            selectedDate.getMonth() !== month - 1 ||
            selectedDate.getDate() !== day
        ) {
            return {
                valid: false,
                message: "That is not a valid calendar date. Please try again."
            };
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        if (selectedDate < today) {
            return {
                valid: false,
                message: "The appointment date cannot be in the past. Please choose a future date."
            };
        }

        return {
            valid: true,
            value: value.trim()
        };
    }

    function validateBookingTime(value) {
        const match =
            /^([01]\d|2[0-3]):([0-5]\d)$/.exec(value.trim());

        if (!match) {
            return {
                valid: false,
                message: "Please enter the time in 24-hour HH:MM format, for example 10:30 or 14:00."
            };
        }

        const hours = Number(match[1]);
        const minutes = Number(match[2]);

        const now = new Date();
        const todayString = [
            now.getFullYear(),
            String(now.getMonth() + 1).padStart(2, "0"),
            String(now.getDate()).padStart(2, "0")
        ].join("-");

        if (bookingState.appointmentDate === todayString) {
            const selectedMinutes = hours * 60 + minutes;
            const currentMinutes =
                now.getHours() * 60 + now.getMinutes();

            if (selectedMinutes <= currentMinutes) {
                return {
                    valid: false,
                    message: "That time has already passed. Please choose a future time."
                };
            }
        }

        return {
            valid: true,
            value: `${match[1]}:${match[2]}`
        };
    }

    async function submitConfirmedBooking() {
        bookingState.step = "submitting";

        addMessage(
            "Your confirmation was received. Submitting your appointment...",
            "bot"
        );

        const booking = {
            vehicle_id: bookingState.selectedVehicle.vehicle_id,
            service_id: bookingState.selectedService.service_id,
            appointment_date: bookingState.appointmentDate,
            appointment_time: bookingState.appointmentTime
        };

        try {
            const result = await customerApi(
                "/customer-portal/appointments",
                {
                    method: "POST",
                    body: JSON.stringify(booking)
                }
            );

            addMessage(
                "Your service appointment was booked successfully!\n\n" +
                `Appointment ID: ${result.appointment_id}\n` +
                `Status: ${result.status}\n\n` +
                "You can view your booking in My Appointments.",
                "bot"
            );

            resetBookingState();

        } catch (error) {
            if (error.status && error.status < 500) {
                bookingState.step = "confirm";

                addMessage(
                    `The booking was not created: ${error.message}\n\n` +
                    "Please reply CANCEL to end this booking and start again with corrected details.",
                    "bot"
                );
            } else {
                bookingState.step = "uncertain";

                addMessage(
                    "I couldn't verify the result of the booking request. " +
                    "Please check My Appointments before trying again, " +
                    "so that we don't accidentally create a duplicate booking.\n\n" +
                    "Reply CANCEL to end this conversation.",
                    "bot"
                );
            }
        }
    }

    async function handleBookingConversation(message) {
        const answer = message.trim().toLowerCase().replace(/[.!?,]+$/g, "");

        if (
            /^(cancel|cancel booking|stop|no|no thanks|start over|exit)$/.test(answer)
        ) {
            resetBookingState();

            addMessage(
                "The booking conversation has been cancelled. No new appointment was created.",
                "bot"
            );

            return;
        }

        if (bookingState.step === "uncertain") {
            addMessage(
                "Please check My Appointments first. Once you've checked, you can start a new booking by saying BOOK A SERVICE.",
                "bot"
            );
            return;
        }

        if (bookingState.step === "submitting") {
            addMessage(
                "Your booking request is already being processed. Please wait for the result.",
                "bot"
            );
            return;
        }

        if (bookingState.step === "vehicle") {
            const choice = resolveChoice(
                message,
                bookingState.vehicles,
                "vehicle"
            );

            if (!choice.item) {
                addMessage(
                    choice.ambiguous
                        ? "I found more than one matching vehicle. Please reply with the option number."
                        : "Please select a vehicle using its option number or registration number.",
                    "bot"
                );
                return;
            }

            bookingState.selectedVehicle = choice.item;

            const vehicleType =
                choice.item.vehicle_type || "Car";

            bookingState.matchingServices =
                bookingState.services.filter(service =>
                    normalizeValue(service.vehicle_type) ===
                        normalizeValue(vehicleType) ||
                    normalizeValue(service.vehicle_type) === "all"
                );

            if (bookingState.matchingServices.length === 0) {
                bookingState.selectedVehicle = null;

                addMessage(
                    `No services are currently available for ${vehicleType} vehicles. Please select another vehicle.`,
                    "bot"
                );
                return;
            }

            bookingState.step = "service";

            const serviceList =
                bookingState.matchingServices.map((service, index) => {
                    const price = Number(service.price);

                    const priceText = Number.isFinite(price)
                        ? `₹${price.toLocaleString("en-IN")}`
                        : String(service.price);

                    return `${index + 1}. ${service.service_name} - ${priceText}`;
                });

            addMessage(
                `You selected ${choice.item.brand} ${choice.item.model}.\n\n` +
                "Please select a service:\n\n" +
                serviceList.join("\n") +
                "\n\nReply with the option number or service name.",
                "bot"
            );

            return;
        }

        if (bookingState.step === "service") {
            const choice = resolveChoice(
                message,
                bookingState.matchingServices,
                "service"
            );

            if (!choice.item) {
                addMessage(
                    choice.ambiguous
                        ? "More than one service matches. Please select using its option number."
                        : "Please select a service using the displayed option number or service name.",
                    "bot"
                );
                return;
            }

            bookingState.selectedService = choice.item;
            bookingState.step = "date";

            addMessage(
                `You selected ${choice.item.service_name}.\n\n` +
                "What date would you prefer for the appointment?\n" +
                "Please use YYYY-MM-DD format, for example 2026-12-15.",
                "bot"
            );

            return;
        }

        if (bookingState.step === "date") {
            const result = validateBookingDate(message);

            if (!result.valid) {
                addMessage(result.message, "bot");
                return;
            }

            bookingState.appointmentDate = result.value;
            bookingState.step = "time";

            addMessage(
                "What time would you prefer?\n" +
                "Please use 24-hour HH:MM format, for example 10:30 or 14:00.",
                "bot"
            );

            return;
        }

        if (bookingState.step === "time") {
            const result = validateBookingTime(message);

            if (!result.valid) {
                addMessage(result.message, "bot");
                return;
            }

            bookingState.appointmentTime = result.value;
            bookingState.step = "confirm";

            const vehicle = bookingState.selectedVehicle;
            const service = bookingState.selectedService;
            const price = Number(service.price);

            const priceText = Number.isFinite(price)
                ? `₹${price.toLocaleString("en-IN")}`
                : String(service.price);

            addMessage(
                "Please review your appointment details:\n\n" +
                `Vehicle: ${vehicle.brand} ${vehicle.model}\n` +
                `Registration: ${vehicle.vehicle_number}\n` +
                `Service: ${service.service_name}\n` +
                `Price: ${priceText}\n` +
                `Date: ${bookingState.appointmentDate}\n` +
                `Time: ${bookingState.appointmentTime}\n\n` +
                "Would you like me to confirm this booking?\n" +
                "Reply YES to confirm or CANCEL to stop.",
                "bot"
            );

            return;
        }

        if (bookingState.step === "confirm") {
            if (
                /^(yes|y|confirm|confirm booking|yes please|yes confirm|go ahead|proceed)$/.test(answer)
            ) {
                await submitConfirmedBooking();
                return;
            }

            addMessage(
                "Please review the booking summary. Reply YES to create the appointment or CANCEL to stop.",
                "bot"
            );
        }
    }

    // ------------------------------------------
    // ------------------------------------------
    // ADMIN AI ASSISTANT
    // ------------------------------------------

    async function sendAdminMessage(text) {
        const token = localStorage.getItem("access_token");
        const role = localStorage.getItem("admin_role");

        if (!token || role !== "admin") {
            throw new Error(
                "Please log in with an administrator account."
            );
        }

        const response = await fetch(
            `${API_BASE_URL}/admin-chatbot/message`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ message: text })
            }
        );

        const data = await response.json().catch(() => ({}));

        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("admin_role");

            throw new Error(
                "Your admin session is invalid or expired. Please log in again."
            );
        }

        if (!response.ok) {
            throw new Error(
                data.detail || "The admin AI request failed."
            );
        }

        addMessage(
            data.reply || "Sorry, I couldn't generate a response.",
            "bot"
        );
    }

    // EXISTING APPOINTMENT LOOKUP
    // ------------------------------------------

    async function getMyAppointments(options = {}) {
        addMessage("Checking your appointments...", "bot");

        try {
            const result = await customerApi(
                "/customer-portal/appointments"
            );

            if (!Array.isArray(result)) {
                throw new Error(
                    "The server returned an unexpected response."
                );
            }

            if (result.length === 0) {
                addMessage(
                    "You don't have any service appointments yet.",
                    "bot"
                );
                return;
            }

            if (options.statusOnly) {
                const summary = result.map(appointment =>
                    `Appointment #${appointment.appointment_id} ` +
                    `(${appointment.service_name}): ` +
                    `${appointment.status || "Status not updated"}`
                );

                addMessage(summary.join("\n"), "bot");

            } else {
                const summary = result.map((appointment, index) => {
                    const date = String(appointment.appointment_date);
                    const time = String(appointment.appointment_time);

                    return [
                        `${index + 1}. ${appointment.service_name}`,
                        `Appointment ID: ${appointment.appointment_id}`,
                        `Vehicle: ${appointment.vehicle_number} - ${appointment.brand || ""} ${appointment.model || ""}`.trim(),
                        `Date: ${date} at ${time}`,
                        `Status: ${appointment.status || "Not updated"}`,
                        `Service price: INR ${Number(appointment.price).toLocaleString("en-IN")}`
                    ].join("\n");
                });

                addMessage(
                    `I found ${result.length} appointment(s):\n\n` +
                    summary.join("\n\n"),
                    "bot"
                );
            }

        } catch (error) {
            addMessage(error.message, "bot");
        }
    }

    // ------------------------------------------
    // APPOINTMENT CANCELLATION AND RESCHEDULING
    // ------------------------------------------

    function resetManagementState() {
        managementState.action = null;
        managementState.step = null;
        managementState.appointments = [];
        managementState.selectedAppointment = null;
        managementState.newDate = null;
        managementState.newTime = null;
    }

    function isCancellationRequest(query) {
        return (
            /\b(cancel|cancellation)\b/.test(query) &&
            /\b(appointment|appointments|booking|bookings)\b/.test(query)
        );
    }

    function isRescheduleRequest(query) {
        return (
            /\b(reschedule|rescheduling)\b/.test(query) ||
            (
                /\b(change|move)\b/.test(query) &&
                /\b(appointment|appointments|booking|bookings)\b/.test(query)
            )
        );
    }

    async function startAppointmentManagement(action) {
        if (!isCustomerPage) {
            addMessage(
                "Please use your customer dashboard to manage personal appointments.",
                "bot"
            );
            return;
        }

        addMessage("Checking your appointments...", "bot");

        const appointments = await customerApi(
            "/customer-portal/appointments"
        );

        if (!Array.isArray(appointments)) {
            throw new Error("Unexpected appointment data received.");
        }

        // Customers may manage only Pending or Confirmed appointments.
        const eligible = appointments.filter(appointment =>
            ["pending", "confirmed"].includes(
                String(appointment.status || "").toLowerCase()
            )
        );

        if (eligible.length === 0) {
            addMessage(
                "You don't have any appointments eligible for " +
                (action === "cancel" ? "cancellation." : "rescheduling.") +
                " Only Pending or Confirmed appointments can be changed.",
                "bot"
            );
            return;
        }

        resetManagementState();

        managementState.action = action;
        managementState.step = "select";
        managementState.appointments = eligible;

        const choices = eligible.map((appointment, index) =>
            `${index + 1}. Appointment #${appointment.appointment_id} - ` +
            `${appointment.service_name} - ` +
            `${appointment.vehicle_number} - ` +
            `${appointment.appointment_date} at ${appointment.appointment_time} ` +
            `(${appointment.status})`
        );

        addMessage(
            action === "cancel"
                ? "Which appointment would you like to cancel?"
                : "Which appointment would you like to reschedule?"
            ,
            "bot"
        );

        addMessage(
            choices.join("\n") +
            "\n\nReply with the option number or appointment ID. " +
            "Reply CANCEL to stop.",
            "bot"
        );
    }

    function resolveManagedAppointment(message) {
        const value = message.trim();

        // Explicit appointment ID, such as appointment #4.
        const idMatch = value.match(
            /(?:appointment\s*#?|#)\s*(\d+)/i
        );

        if (idMatch) {
            return managementState.appointments.find(
                appointment =>
                    Number(appointment.appointment_id) ===
                    Number(idMatch[1])
            ) || null;
        }

        // A plain number selects the displayed option.
        if (/^\d+$/.test(value)) {
            const index = Number(value) - 1;

            if (
                index >= 0 &&
                index < managementState.appointments.length
            ) {
                return managementState.appointments[index];
            }
        }

        const normalized = normalizeValue(value);

        const matches = managementState.appointments.filter(
            appointment => {
                const labels = [
                    appointment.service_name,
                    appointment.vehicle_number,
                    `${appointment.brand || ""} ${appointment.model || ""}`
                ];

                return labels.some(label =>
                    normalizeValue(label) === normalized
                );
            }
        );

        return matches.length === 1 ? matches[0] : null;
    }

    function validateManagementTime(value) {
        const match =
            /^([01]\d|2[0-3]):([0-5]\d)$/.exec(value.trim());

        if (!match) {
            return {
                valid: false,
                message: "Enter time in HH:MM format, such as 10:30 or 14:00."
            };
        }

        const now = new Date();

        const todayString = [
            now.getFullYear(),
            String(now.getMonth() + 1).padStart(2, "0"),
            String(now.getDate()).padStart(2, "0")
        ].join("-");

        if (managementState.newDate === todayString) {
            const selectedMinutes =
                Number(match[1]) * 60 + Number(match[2]);

            const currentMinutes =
                now.getHours() * 60 + now.getMinutes();

            if (selectedMinutes <= currentMinutes) {
                return {
                    valid: false,
                    message: "Please choose a future time."
                };
            }
        }

        return {
            valid: true,
            value: `${match[1]}:${match[2]}`
        };
    }

    async function handleAppointmentManagement(message) {
        const answer = message.trim().toLowerCase().replace(/[.!?,]+$/g, "");

        if (/^(cancel|stop|exit|nevermind)$/.test(answer)) {
            resetManagementState();

            addMessage(
                "The appointment management operation was cancelled. " +
                "No appointment was changed.",
                "bot"
            );
            return;
        }

        if (managementState.step === "uncertain") {
            addMessage(
                "Please check My Appointments to verify the result " +
                "before starting another request.",
                "bot"
            );
            return;
        }

        if (managementState.step === "submitting") {
            addMessage(
                "Your request is being processed.",
                "bot"
            );
            return;
        }

        if (managementState.step === "select") {
            const appointment = resolveManagedAppointment(message);

            if (!appointment) {
                addMessage(
                    "I couldn't identify that appointment. " +
                    "Please enter one of the displayed option numbers " +
                    "or an appointment ID.",
                    "bot"
                );
                return;
            }

            managementState.selectedAppointment = appointment;

            if (managementState.action === "cancel") {
                managementState.step = "confirm";

                addMessage(
                    "Please review the cancellation request:\n\n" +
                    `Appointment ID: #${appointment.appointment_id}\n` +
                    `Service: ${appointment.service_name}\n` +
                    `Vehicle: ${appointment.brand} ${appointment.model}\n` +
                    `Registration: ${appointment.vehicle_number}\n` +
                    `Date: ${appointment.appointment_date}\n` +
                    `Time: ${appointment.appointment_time}\n` +
                    `Current status: ${appointment.status}\n\n` +
                    "Do you want to cancel this appointment?\n" +
                    "Reply YES to confirm or CANCEL to stop.",
                    "bot"
                );

            } else {
                managementState.step = "date";

                addMessage(
                    `You selected appointment #${appointment.appointment_id} ` +
                    `for ${appointment.service_name}.\n\n` +
                    "What new date would you prefer?\n" +
                    "Enter YYYY-MM-DD, for example 2026-12-15.",
                    "bot"
                );
            }

            return;
        }

        if (managementState.step === "date") {
            const result = validateBookingDate(message);

            if (!result.valid) {
                addMessage(result.message, "bot");
                return;
            }

            managementState.newDate = result.value;
            managementState.step = "time";

            addMessage(
                "What new time would you prefer?\n" +
                "Enter time in 24-hour HH:MM format, for example 10:30.",
                "bot"
            );

            return;
        }

        if (managementState.step === "time") {
            const result = validateManagementTime(message);

            if (!result.valid) {
                addMessage(result.message, "bot");
                return;
            }

            managementState.newTime = result.value;
            managementState.step = "confirm";

            const appointment =
                managementState.selectedAppointment;

            addMessage(
                "Please review your rescheduling request:\n\n" +
                `Appointment ID: #${appointment.appointment_id}\n` +
                `Service: ${appointment.service_name}\n` +
                `Vehicle: ${appointment.brand} ${appointment.model}\n` +
                `Current date: ${appointment.appointment_date}\n` +
                `Current time: ${appointment.appointment_time}\n` +
                `New date: ${managementState.newDate}\n` +
                `New time: ${managementState.newTime}\n\n` +
                "Do you want to reschedule this appointment?\n" +
                "Reply YES to confirm or CANCEL to stop.",
                "bot"
            );

            return;
        }

        if (managementState.step === "confirm") {
            if (/^(no|n|no thanks)$/.test(answer)) {
                resetManagementState();

                addMessage(
                    "No changes were made to your appointment.",
                    "bot"
                );
                return;
            }

            if (
                !/^(yes|y|confirm|proceed|go ahead)$/.test(answer)
            ) {
                addMessage(
                    "Please reply YES to confirm or CANCEL to stop.",
                    "bot"
                );
                return;
            }

            const appointment =
                managementState.selectedAppointment;

            const action = managementState.action;

            managementState.step = "submitting";

            addMessage(
                action === "cancel"
                    ? "Submitting your cancellation request..."
                    : "Submitting your rescheduling request...",
                "bot"
            );

            try {
                let result;

                if (action === "cancel") {
                    result = await customerApi(
                        `/customer-portal/appointments/${appointment.appointment_id}/cancel`,
                        {
                            method: "POST"
                        }
                    );

                    addMessage(
                        "Appointment cancelled successfully!\n\n" +
                        `Appointment ID: #${result.appointment_id}\n` +
                        `Status: ${result.status}`,
                        "bot"
                    );

                } else {
                    result = await customerApi(
                        `/customer-portal/appointments/${appointment.appointment_id}/reschedule`,
                        {
                            method: "PUT",
                            body: JSON.stringify({
                                appointment_date: managementState.newDate,
                                appointment_time: managementState.newTime
                            })
                        }
                    );

                    addMessage(
                        "Appointment rescheduled successfully!\n\n" +
                        `Appointment ID: #${result.appointment_id}\n` +
                        `New date: ${result.appointment_date}\n` +
                        `New time: ${result.appointment_time}\n` +
                        `Status: ${result.status}`,
                        "bot"
                    );
                }

                resetManagementState();

            } catch (error) {
                if (error.status && error.status < 500) {
                    resetManagementState();

                    addMessage(
                        `The operation was not completed: ${error.message}\n\n` +
                        "Please check My Appointments before trying again.",
                        "bot"
                    );

                } else {
                    managementState.step = "uncertain";

                    addMessage(
                        "I couldn't verify whether the operation succeeded. " +
                        "Please check My Appointments before trying again " +
                        "to avoid duplicate changes.",
                        "bot"
                    );
                }
            }
        }
    }

    function isBookingRequest(query) {
        return (
            /\b(book|booking|schedule|reserve)\b/.test(query) ||
            /\b(make|create)\b.*\b(appointment|booking)\b/.test(query)
        );
    }

    // ------------------------------------------
    // ------------------------------------------
    // ADMIN APPOINTMENT STATUS MANAGEMENT
    // ------------------------------------------

    function resetAdminStatusState() {
        adminStatusState.step = null;
        adminStatusState.appointment = null;
        adminStatusState.requestedStatus = null;
    }

    function parseAdminStatusRequest(query) {

        const idMatch = query.match(
            /\bappointment(?:\s+(?:id|number))?\s*#?\s*(\d+)\b/
        );

        const hasUpdateIntent =
            /\b(update|change|set|mark|move|confirm|cancel)\b/.test(query);

        if (!idMatch || !hasUpdateIntent) {
            return null;
        }

        const statusOptions = [
            {
                pattern: /\bready for pickup\b/,
                value: "Ready for Pickup"
            },
            {
                pattern: /\bvehicle received\b/,
                value: "Vehicle Received"
            },
            {
                pattern: /\bin progress\b/,
                value: "In Progress"
            },
            {
                pattern: /\bcomplete(?:d)?\b/,
                value: "Completed"
            },
            {
                pattern: /\bcancel(?:led|ed)?\b/,
                value: "Cancelled"
            },
            {
                pattern: /\bconfirm(?:ed)?\b/,
                value: "Confirmed"
            },
            {
                pattern: /\bpending\b/,
                value: "Pending"
            }
        ];

        const matched = statusOptions.find(
            item => item.pattern.test(query)
        );

        let requestedStatus = matched?.value || null;

        // Convenient commands without an explicit status.
        if (!requestedStatus && /\bconfirm\b/.test(query)) {
            requestedStatus = "Confirmed";
        }

        if (!requestedStatus && /\bcancel\b/.test(query)) {
            requestedStatus = "Cancelled";
        }

        if (!requestedStatus) {
            return null;
        }

        return {
            appointmentId: Number(idMatch[1]),
            status: requestedStatus
        };
    }

    async function startAdminStatusUpdate(request) {

        const token = localStorage.getItem("access_token");
        const role = localStorage.getItem("admin_role");

        if (!token || role !== "admin") {
            throw new Error(
                "Administrator login is required."
            );
        }

        addMessage(
            `Checking appointment #${request.appointmentId}...`,
            "bot"
        );

        const response = await fetch(
            `${API_BASE_URL}/appointments`,
            {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        );

        const records = await response.json().catch(() => []);

        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("admin_role");

            throw new Error(
                "Your administrator session is invalid or expired."
            );
        }

        if (!response.ok) {
            throw new Error(
                "Unable to retrieve appointment details."
            );
        }

        if (!Array.isArray(records)) {
            throw new Error(
                "Unexpected appointment data received."
            );
        }

        const appointment = records.find(
            item =>
                Number(item.appointment_id) === request.appointmentId
        );

        if (!appointment) {
            addMessage(
                `Appointment #${request.appointmentId} was not found.`,
                "bot"
            );
            return;
        }

        const terminalStatuses = ["Completed", "Cancelled"];

        if (terminalStatuses.includes(appointment.status)) {
            addMessage(
                `Appointment #${appointment.appointment_id} is already ${appointment.status}. ` +
                "No further status changes are allowed.",
                "bot"
            );
            return;
        }

        if (appointment.status === request.status) {
            addMessage(
                `Appointment #${appointment.appointment_id} ` +
                `already has status ${appointment.status}. No changes needed.`,
                "bot"
            );
            return;
        }

        adminStatusState.appointment = appointment;
        adminStatusState.requestedStatus = request.status;
        adminStatusState.step = "confirm";

        addMessage(
            "Please review the requested status change:\n\n" +
            `Appointment ID: #${appointment.appointment_id}\n` +
            `Customer: ${appointment.customer_name}\n` +
            `Vehicle: ${appointment.vehicle_number} - ` +
            `${appointment.brand} ${appointment.model}\n` +
            `Service: ${appointment.service_name}\n` +
            `Current status: ${appointment.status}\n` +
            `Requested status: ${request.status}\n\n` +
            "Do you confirm this status update?\n" +
            "Reply YES to proceed or CANCEL to stop.",
            "bot"
        );
    }

    async function handleAdminStatusConversation(message) {

        const answer = message
            .trim()
            .toLowerCase()
            .replace(/[.!?,]+$/g, "");

        if (/^(cancel|stop|no|exit)$/.test(answer)) {

            resetAdminStatusState();

            addMessage(
                "Status update cancelled. No appointment was changed.",
                "bot"
            );

            return;
        }

        if (adminStatusState.step === "uncertain") {
            addMessage(
                "Please retrieve the appointment status again before " +
                "trying another update.",
                "bot"
            );
            return;
        }

        if (adminStatusState.step === "submitting") {
            addMessage(
                "The status update is already being processed.",
                "bot"
            );
            return;
        }

        if (!/^(yes|y|confirm|proceed|go ahead)$/.test(answer)) {
            addMessage(
                "Please reply YES to confirm the status update or CANCEL to stop.",
                "bot"
            );
            return;
        }

        const appointment = adminStatusState.appointment;
        const requestedStatus = adminStatusState.requestedStatus;

        adminStatusState.step = "submitting";

        addMessage(
            "Updating appointment status...",
            "bot"
        );

        try {
            const token = localStorage.getItem("access_token");

            const response = await fetch(
                `${API_BASE_URL}/admin-chatbot/appointments/` +
                `${appointment.appointment_id}/status`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        status: requestedStatus
                    })
                }
            );

            const result = await response.json().catch(() => ({}));

            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem("access_token");
                localStorage.removeItem("admin_role");

                resetAdminStatusState();

                throw new Error(
                    "Administrator authentication failed. Please log in again."
                );
            }

            if (!response.ok) {
                const error = new Error(
                    result.detail || "Appointment status update failed."
                );

                error.status = response.status;
                throw error;
            }

            resetAdminStatusState();

            addMessage(
                result.message + "\n\n" +
                `Appointment ID: #${result.appointment_id}\n` +
                `Current status: ${result.status}`,
                "bot"
            );

        } catch (error) {

            if (error.status) {
                resetAdminStatusState();

                addMessage(
                    `Status update not completed: ${error.message}`,
                    "bot"
                );
            } else {
                adminStatusState.step = "uncertain";

                addMessage(
                    "I couldn't verify the update result. " +
                    "Please check the appointment status before trying again.",
                    "bot"
                );
            }
        }
    }


    // ------------------------------------------
    // ADMIN TECHNICIAN ASSIGNMENT
    // ------------------------------------------

    function resetAdminTechnicianState() {
        adminTechnicianState.step = null;
        adminTechnicianState.appointment = null;
        adminTechnicianState.technician = null;
    }

    function parseAdminTechnicianAssignment(query) {

        const technicianMatch = query.match(
            /\b(?:technician|tech)(?:\s+(?:id|number))?\s*#?\s*(\d+)\b/
        );

        const appointmentMatch = query.match(
            /\bappointment(?:\s+(?:id|number))?\s*#?\s*(\d+)\b/
        );

        const hasAssignmentIntent =
            /\b(assign|reassign|change|replace)\b/.test(query);

        if (
            !hasAssignmentIntent ||
            !technicianMatch ||
            !appointmentMatch
        ) {
            return null;
        }

        return {
            technicianId: Number(technicianMatch[1]),
            appointmentId: Number(appointmentMatch[1])
        };
    }

    async function startAdminTechnicianAssignment(request) {

        const token = localStorage.getItem("access_token");
        const role = localStorage.getItem("admin_role");

        if (!token || role !== "admin") {
            throw new Error("Administrator login is required.");
        }

        addMessage(
            `Checking appointment #${request.appointmentId} and ` +
            `technician #${request.technicianId}...`,
            "bot"
        );

        const headers = {
            Authorization: `Bearer ${token}`
        };

        const [appointmentResponse, technicianResponse] =
            await Promise.all([
                fetch(`${API_BASE_URL}/appointments`, { headers }),
                fetch(`${API_BASE_URL}/technicians`, { headers })
            ]);

        if (
            appointmentResponse.status === 401 ||
            appointmentResponse.status === 403 ||
            technicianResponse.status === 401 ||
            technicianResponse.status === 403
        ) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("admin_role");

            throw new Error(
                "Administrator session is invalid or expired."
            );
        }

        const appointmentData = await appointmentResponse
            .json().catch(() => null);

        const technicianData = await technicianResponse
            .json().catch(() => null);

        if (!appointmentResponse.ok) {
            throw new Error(
                appointmentData?.detail ||
                "Unable to retrieve appointment records."
            );
        }

        if (!technicianResponse.ok) {
            throw new Error(
                technicianData?.detail ||
                "Unable to retrieve technician records."
            );
        }

        if (
            !Array.isArray(appointmentData) ||
            !Array.isArray(technicianData)
        ) {
            throw new Error(
                "Unexpected appointment or technician data received."
            );
        }

        const appointment = appointmentData.find(
            item =>
                Number(item.appointment_id) === request.appointmentId
        );

        if (!appointment) {
            addMessage(
                `Appointment #${request.appointmentId} was not found.`,
                "bot"
            );
            return;
        }

        const technician = technicianData.find(
            item =>
                Number(item.technician_id) === request.technicianId
        );

        if (!technician) {
            addMessage(
                `Technician #${request.technicianId} was not found.`,
                "bot"
            );
            return;
        }

        if (
            ["Completed", "Cancelled"].includes(appointment.status)
        ) {
            addMessage(
                `Appointment #${appointment.appointment_id} is already ` +
                `${appointment.status}. A technician cannot be assigned.`,
                "bot"
            );
            return;
        }

        if (
            Number(appointment.technician_id) ===
            Number(technician.technician_id)
        ) {
            addMessage(
                `${technician.technician_name} is already assigned to ` +
                `appointment #${appointment.appointment_id}.`,
                "bot"
            );
            return;
        }

        adminTechnicianState.appointment = appointment;
        adminTechnicianState.technician = technician;
        adminTechnicianState.step = "confirm";

        addMessage(
            "Please review the technician assignment:\n\n" +
            `Appointment ID: #${appointment.appointment_id}\n` +
            `Customer: ${appointment.customer_name}\n` +
            `Vehicle: ${appointment.vehicle_number} - ` +
            `${appointment.brand} ${appointment.model}\n` +
            `Service: ${appointment.service_name}\n` +
            `Appointment status: ${appointment.status}\n` +
            `Current technician: ` +
            `${appointment.technician_name || "Unassigned"}\n` +
            `Requested technician: #${technician.technician_id} - ` +
            `${technician.technician_name}\n` +
            `Technician vehicle category: ` +
            `${technician.vehicle_type || "All"}\n` +
            `Specialization: ${technician.specialization || "Not specified"}\n\n` +
            "Do you confirm this assignment?\n" +
            "Reply YES to proceed or CANCEL to stop.",
            "bot"
        );
    }

    async function handleAdminTechnicianConversation(message) {

        const answer = message
            .trim()
            .toLowerCase()
            .replace(/[.!?,]+$/g, "");

        if (/^(cancel|stop|no|exit)$/.test(answer)) {

            resetAdminTechnicianState();

            addMessage(
                "Technician assignment cancelled. No appointment was changed.",
                "bot"
            );

            return;
        }

        if (adminTechnicianState.step === "uncertain") {
            addMessage(
                "I couldn't verify the assignment result. " +
                "Please retrieve the appointment details before trying again.",
                "bot"
            );
            return;
        }

        if (adminTechnicianState.step === "submitting") {
            addMessage(
                "The technician assignment is already being processed.",
                "bot"
            );
            return;
        }

        if (!/^(yes|y|confirm|proceed|go ahead)$/.test(answer)) {
            addMessage(
                "Please reply YES to confirm the assignment or CANCEL to stop.",
                "bot"
            );
            return;
        }

        const appointment = adminTechnicianState.appointment;
        const technician = adminTechnicianState.technician;

        adminTechnicianState.step = "submitting";

        addMessage(
            "Assigning technician...",
            "bot"
        );

        try {
            const token = localStorage.getItem("access_token");

            const response = await fetch(
                `${API_BASE_URL}/admin-chatbot/appointments/` +
                `${appointment.appointment_id}/technician`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        technician_id: technician.technician_id
                    })
                }
            );

            const result = await response.json().catch(() => ({}));

            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem("access_token");
                localStorage.removeItem("admin_role");

                resetAdminTechnicianState();

                throw new Error(
                    "Administrator authentication failed. Please log in again."
                );
            }

            if (!response.ok) {
                const error = new Error(
                    result.detail || "Technician assignment failed."
                );

                error.status = response.status;
                throw error;
            }

            resetAdminTechnicianState();

            addMessage(
                result.message + "\n\n" +
                `Appointment ID: #${result.appointment_id}\n` +
                `Technician: ${result.technician_name}\n` +
                `Appointment status remains: ${result.status}`,
                "bot"
            );

        } catch (error) {

            if (error.status) {
                resetAdminTechnicianState();

                addMessage(
                    `Technician assignment not completed: ${error.message}`,
                    "bot"
                );
            } else {
                adminTechnicianState.step = "uncertain";

                addMessage(
                    "I couldn't verify the assignment result. " +
                    "Please check the appointment before trying again.",
                    "bot"
                );
            }
        }
    }


    // ------------------------------------------
    // ADMIN AI: SHARED ACTION HELPERS
    // ------------------------------------------

    function resetAdminActionState() {
        adminActionState.step = null;
        adminActionState.type = null;
        adminActionState.endpoint = null;
        adminActionState.method = null;
        adminActionState.body = null;
        adminActionState.preview = null;
    }

    async function adminApiRequest(endpoint, options = {}) {

        const token = localStorage.getItem("access_token");

        if (!token || localStorage.getItem("admin_role") !== "admin") {
            throw new Error("Administrator login is required.");
        }

        const headers = {
            ...(options.headers || {}),
            Authorization: `Bearer ${token}`
        };

        if (options.body !== undefined) {
            headers["Content-Type"] = "application/json";
        }

        const response = await fetch(
            `${API_BASE_URL}${endpoint}`,
            {
                ...options,
                headers
            }
        );

        const data = await response.json().catch(() => ({}));

        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("admin_role");

            throw new Error(
                "Administrator session expired. Please log in again."
            );
        }

        if (!response.ok) {
            const error = new Error(
                data.detail || "The administrative operation failed."
            );
            error.status = response.status;
            throw error;
        }

        return data;
    }

    function adminMoney(value) {
        return `INR ${Number(value || 0).toFixed(2)}`;
    }

    function startAdminAction(action) {

        adminActionState.step = "confirm";
        adminActionState.type = action.type;
        adminActionState.endpoint = action.endpoint;
        adminActionState.method = action.method;
        adminActionState.body = action.body;
        adminActionState.preview = action.preview;

        addMessage(
            action.preview +
            "\n\nReply YES to confirm or CANCEL to stop.",
            "bot"
        );
    }

    async function handleAdminActionConversation(message) {

        const answer = message
            .trim()
            .toLowerCase()
            .replace(/[.!?,]+$/g, "");

        if (/^(cancel|stop|no|exit)$/.test(answer)) {
            resetAdminActionState();

            addMessage(
                "Operation cancelled. No records were changed.",
                "bot"
            );

            return;
        }

        if (adminActionState.step === "uncertain") {
            addMessage(
                "The operation result could not be verified. " +
                "Please retrieve the record before trying again.",
                "bot"
            );
            return;
        }

        if (adminActionState.step === "submitting") {
            addMessage(
                "This operation is already being processed.",
                "bot"
            );
            return;
        }

        if (!/^(yes|y|confirm|proceed|go ahead)$/.test(answer)) {
            addMessage(
                "Please reply YES to confirm or CANCEL to stop.",
                "bot"
            );
            return;
        }

        const type = adminActionState.type;
        const endpoint = adminActionState.endpoint;
        const method = adminActionState.method;
        const body = adminActionState.body;

        adminActionState.step = "submitting";

        addMessage("Processing your request...", "bot");

        try {
            const result = await adminApiRequest(endpoint, {
                method,
                body: JSON.stringify(body)
            });

            resetAdminActionState();

            let reply = result.message || "Operation completed successfully.";

            if (type === "stock") {
                reply +=
                    `\nPart: ${result.part_name}` +
                    `\nPrevious quantity: ${result.previous_quantity}` +
                    `\nNew quantity: ${result.quantity}`;
            }

            if (type === "estimate") {
                reply += `\nEstimate ID: #${result.estimate_id}`;
            }

            if (type === "invoice") {
                reply += `\nInvoice ID: #${result.invoice_id}`;
                reply += "\nParts stock was updated by the invoice service.";
            }

            if (type === "payment") {
                reply += `\nInvoice ID: #${result.invoice_id}`;
                reply += `\nPayment method: ${body.payment_method}`;
            }

            if (type === "reschedule") {
                reply += `\nAppointment ID: #${result.appointment_id}`;
                reply += `\nNew date: ${result.appointment_date}`;
                reply += `\nNew time: ${result.appointment_time}`;
            }

            addMessage(reply, "bot");

        } catch (error) {
            if (error.status) {
                resetAdminActionState();

                addMessage(
                    `Operation not completed: ${error.message}`,
                    "bot"
                );
            } else {
                adminActionState.step = "uncertain";

                addMessage(
                    "I couldn't verify the operation result. " +
                    "Please check the database record before retrying.",
                    "bot"
                );
            }
        }
    }

    // ------------------------------------------
    // TECHNICIAN RECOMMENDATIONS / AVAILABILITY
    // ------------------------------------------

    function parseAdminTechnicianRecommendation(query) {

        const appointmentMatch = query.match(
            /\bappointment(?:\s+(?:id|number))?\s*#?\s*(\d+)\b/
        );

        const intent =
            /\b(recommend|suggest|availability|available|busy|free|schedule)\b/
                .test(query);

        const technicianTopic =
            /\b(technician|technicians|mechanic|mechanics)\b/.test(query);

        if (!appointmentMatch || !intent || !technicianTopic) {
            return null;
        }

        return {
            appointmentId: Number(appointmentMatch[1])
        };
    }

    async function showAdminTechnicianRecommendations(request) {

        addMessage(
            `Checking technician availability for appointment #${request.appointmentId}...`,
            "bot"
        );

        const result = await adminApiRequest(
            `/admin-chatbot/appointments/${request.appointmentId}/technician-recommendations`
        );

        const recommendations = result.recommendations || [];

        if (!recommendations.length) {
            addMessage(
                `No compatible technicians were found for appointment #${request.appointmentId}.`,
                "bot"
            );
            return;
        }

        const lines = recommendations.map(item => (
            `Technician #${item.technician_id}: ${item.technician_name}\n` +
            `Vehicle category: ${item.vehicle_type}\n` +
            `Specialization: ${item.specialization || "Not specified"}\n` +
            `Experience: ${item.experience ?? "Not specified"} years\n` +
            `Availability: ${item.availability}\n` +
            `Service match: ${item.matches_service ? "Yes" : "No"}`
        ));

        addMessage(
            `Technician recommendations for appointment #${request.appointmentId}\n\n` +
            lines.join("\n\n") +
            "\n\n" +
            result.availability_scope,
            "bot"
        );
    }

    // ------------------------------------------
    // SPARE-PART STOCK ADJUSTMENT
    // ------------------------------------------

    function parseAdminStockRequest(query) {

        const match = query.match(
            /\b(add|increase|remove|decrease)\s+(\d+)\s*(?:units?|pieces?)?\s+(?:to|from)\s+(?:part|item)\s*#?(\d+)\b/
        );

        if (!match) {
            return null;
        }

        return {
            operation: ["add", "increase"].includes(match[1])
                ? "add" : "remove",
            quantity: Number(match[2]),
            partId: Number(match[3])
        };
    }

    async function startAdminStockAdjustment(request) {

        const parts = await adminApiRequest("/parts");

        if (!Array.isArray(parts)) {
            throw new Error("Unexpected inventory data received.");
        }

        const part = parts.find(
            item => Number(item.part_id) === request.partId
        );

        if (!part) {
            addMessage(`Part #${request.partId} was not found.`, "bot");
            return;
        }

        const current = Number(part.quantity);

        if (
            request.operation === "remove" &&
            request.quantity > current
        ) {
            addMessage(
                `Cannot remove ${request.quantity} units from ${part.part_name}. ` +
                `Available stock: ${current}.`,
                "bot"
            );
            return;
        }

        const updated = request.operation === "add"
            ? current + request.quantity
            : current - request.quantity;

        startAdminAction({
            type: "stock",
            endpoint: `/admin-chatbot/parts/${request.partId}/stock`,
            method: "POST",
            body: {
                operation: request.operation,
                quantity: request.quantity
            },
            preview:
                "Please confirm the stock adjustment:\n\n" +
                `Part ID: #${part.part_id}\n` +
                `Part: ${part.part_name}\n` +
                `Current quantity: ${current}\n` +
                `Operation: ${request.operation}\n` +
                `Adjustment: ${request.quantity}\n` +
                `New quantity: ${updated}`
        });
    }

    // ------------------------------------------
    // ESTIMATE AND INVOICE CREATION
    // ------------------------------------------

    function extractAdminPartSelections(query) {

        const matches = [
            ...query.matchAll(
                /\bpart\s*#?(\d+)\s+quantity\s+(\d+)\b/g
            )
        ];

        const selections = matches.map(match => ({
            part_id: Number(match[1]),
            quantity: Number(match[2])
        }));

        const ids = selections.map(item => item.part_id);

        if (new Set(ids).size !== ids.length) {
            throw new Error(
                "Each part can only be selected once. Combine duplicate quantities."
            );
        }

        return selections;
    }

    function parseAdminEstimateRequest(query) {

        const match = query.match(
            /\b(?:create|make|generate)\s+(?:a\s+)?estimate\s+for\s+appointment\s*#?(\d+)\b/
        );

        return match
            ? {
                appointmentId: Number(match[1]),
                parts: extractAdminPartSelections(query)
            }
            : null;
    }

    function parseAdminInvoiceRequest(query) {

        const match = query.match(
            /\b(?:create|make|generate)\s+(?:a\s+)?(?:final\s+)?invoice\s+for\s+appointment\s*#?(\d+)\b/
        );

        if (!match) {
            return null;
        }

        const discountMatch = query.match(
            /\bdiscount(?:\s+of)?\s+(\d+(?:\.\d{1,2})?)\b/
        );

        return {
            appointmentId: Number(match[1]),
            parts: extractAdminPartSelections(query),
            discount: discountMatch ? Number(discountMatch[1]) : 0
        };
    }

    async function prepareAdminFinancialAction(request, type) {

        const appointments = await adminApiRequest("/appointments");

        if (!Array.isArray(appointments)) {
            throw new Error("Unexpected appointment data received.");
        }

        const appointment = appointments.find(
            item => Number(item.appointment_id) === request.appointmentId
        );

        if (!appointment) {
            addMessage(
                `Appointment #${request.appointmentId} was not found.`,
                "bot"
            );
            return;
        }

        if (type === "invoice" && appointment.status !== "Completed") {
            addMessage(
                `Appointment #${appointment.appointment_id} is ${appointment.status}. ` +
                "A final invoice can only be generated after the appointment is Completed.",
                "bot"
            );
            return;
        }

        if (type === "invoice") {
            const invoices = await adminApiRequest("/invoices");

            if (invoices.some(
                item => Number(item.appointment_id) === request.appointmentId
            )) {
                addMessage(
                    `A final invoice already exists for appointment #${request.appointmentId}.`,
                    "bot"
                );
                return;
            }
        }

        let selectedParts = [];
        let partsAmount = 0;

        if (request.parts.length) {
            const parts = await adminApiRequest("/parts");

            for (const selection of request.parts) {
                const part = parts.find(
                    item => Number(item.part_id) === selection.part_id
                );

                if (!part) {
                    addMessage(
                        `Part #${selection.part_id} was not found.`,
                        "bot"
                    );
                    return;
                }

                const available = Number(part.quantity);
                const quantity = selection.quantity;

                if (type === "invoice" && quantity > available) {
                    addMessage(
                        `Insufficient stock for ${part.part_name}. ` +
                        `Available quantity: ${available}.`,
                        "bot"
                    );
                    return;
                }

                const lineTotal = Number(part.price) * quantity;
                partsAmount += lineTotal;

                selectedParts.push({
                    part_id: selection.part_id,
                    quantity,
                    part_name: part.part_name,
                    line_total: lineTotal,
                    available
                });
            }
        }

        const serviceAmount = Number(appointment.price || 0);
        const subtotal = serviceAmount + partsAmount;
        const discount = type === "invoice"
            ? request.discount || 0
            : 0;

        if (discount < 0 || discount > subtotal) {
            addMessage(
                "The discount cannot exceed the subtotal.",
                "bot"
            );
            return;
        }

        const total = subtotal - discount;

        const selectedPartLines = selectedParts.length
            ? selectedParts.map(part =>
                `  ${part.part_name} (#${part.part_id}) ? ${part.quantity}: ` +
                `${adminMoney(part.line_total)}` +
                (type === "invoice"
                    ? ` (stock: ${part.available})`
                    : "")
            ).join("\n")
            : "No additional parts selected.";

        const preview =
            `Please review the ${type}:\n\n` +
            `Appointment: #${appointment.appointment_id}\n` +
            `Customer: ${appointment.customer_name}\n` +
            `Vehicle: ${appointment.vehicle_number} - ${appointment.brand} ${appointment.model}\n` +
            `Service: ${appointment.service_name}\n` +
            `Appointment status: ${appointment.status}\n` +
            `Service amount: ${adminMoney(serviceAmount)}\n` +
            `Parts:\n${selectedPartLines}\n` +
            `Parts amount: ${adminMoney(partsAmount)}\n` +
            (type === "invoice"
                ? `Discount: ${adminMoney(discount)}\n`
                : "") +
            `Total: ${adminMoney(total)}\n\n` +
            (type === "invoice"
                ? "Confirming will create the final invoice and deduct selected parts from inventory."
                : "This creates an estimate. It does not deduct inventory stock.");

        startAdminAction({
            type,
            endpoint: type === "estimate" ? "/estimates" : "/invoices",
            method: "POST",
            body: {
                appointment_id: request.appointmentId,
                parts: request.parts.map(item => ({
                    part_id: item.part_id,
                    quantity: item.quantity
                })),
                ...(type === "invoice"
                    ? { discount_amount: discount }
                    : {})
            },
            preview
        });
    }

    // ------------------------------------------

    // ------------------------------------------
    // ADMIN APPOINTMENT RESCHEDULING
    // ------------------------------------------

    function parseAdminRescheduleRequest(query) {

        const match = query.match(
            /\b(?:reschedule|move)\s+appointment(?:\s+(?:id|number))?\s*#?(\d+)\s+to\s+(\d{4}-\d{2}-\d{2})\s+(?:at\s+)?(\d{1,2}:\d{2})\b/
        );

        if (!match) {
            return null;
        }

        return {
            appointmentId: Number(match[1]),
            appointmentDate: match[2],
            appointmentTime: match[3].padStart(5, "0")
        };
    }

    async function startAdminReschedule(request) {

        const appointments = await adminApiRequest("/appointments");

        if (!Array.isArray(appointments)) {
            throw new Error("Unexpected appointment data received.");
        }

        const appointment = appointments.find(
            item => Number(item.appointment_id) === request.appointmentId
        );

        if (!appointment) {
            addMessage(
                `Appointment #${request.appointmentId} was not found.`,
                "bot"
            );
            return;
        }

        if (["Completed", "Cancelled"].includes(appointment.status)) {
            addMessage(
                `Appointment #${appointment.appointment_id} is ${appointment.status}. ` +
                "It cannot be rescheduled.",
                "bot"
            );
            return;
        }

        startAdminAction({
            type: "reschedule",
            endpoint:
                `/admin-chatbot/appointments/${request.appointmentId}/schedule`,
            method: "PUT",
            body: {
                appointment_date: request.appointmentDate,
                appointment_time: request.appointmentTime
            },
            preview:
                "Please review the appointment reschedule:\n\n" +
                `Appointment ID: #${appointment.appointment_id}\n` +
                `Customer: ${appointment.customer_name}\n` +
                `Vehicle: ${appointment.vehicle_number} - ` +
                `${appointment.brand} ${appointment.model}\n` +
                `Service: ${appointment.service_name}\n` +
                `Current status: ${appointment.status}\n` +
                `Current date: ${appointment.appointment_date}\n` +
                `Current time: ${appointment.appointment_time}\n` +
                `Requested date: ${request.appointmentDate}\n` +
                `Requested time: ${request.appointmentTime}\n\n` +
                "Confirming changes only the appointment date and time."
        });
    }

    // INVOICE PAYMENT
    // ------------------------------------------

    function parseAdminPaymentRequest(query) {

        const match = query.match(
            /\b(?:mark|record|set)\s+invoice\s*#?(\d+)\s+(?:as\s+)?paid\s+(?:by|via)\s+(cash|upi|card|bank transfer)\b/
        );

        if (!match) {
            return null;
        }

        const methods = {
            cash: "Cash",
            upi: "UPI",
            card: "Card",
            "bank transfer": "Bank Transfer"
        };

        return {
            invoiceId: Number(match[1]),
            paymentMethod: methods[match[2]]
        };
    }

    async function startAdminPaymentUpdate(request) {

        const invoices = await adminApiRequest("/invoices");

        if (!Array.isArray(invoices)) {
            throw new Error("Unexpected invoice data received.");
        }

        const invoice = invoices.find(
            item => Number(item.invoice_id) === request.invoiceId
        );

        if (!invoice) {
            addMessage(
                `Invoice #${request.invoiceId} was not found.`,
                "bot"
            );
            return;
        }

        if (invoice.payment_status === "Paid") {
            addMessage(
                `Invoice #${request.invoiceId} is already Paid.`,
                "bot"
            );
            return;
        }

        startAdminAction({
            type: "payment",
            endpoint: `/invoices/${request.invoiceId}/payment`,
            method: "PUT",
            body: {
                payment_method: request.paymentMethod
            },
            preview:
                "Please confirm this payment update:\n\n" +
                `Invoice ID: #${invoice.invoice_id}\n` +
                `Appointment ID: #${invoice.appointment_id}\n` +
                `Customer: ${invoice.customer_name}\n` +
                `Vehicle: ${invoice.vehicle_number}\n` +
                `Invoice amount: ${adminMoney(invoice.total_amount)}\n` +
                `Current payment status: ${invoice.payment_status}\n` +
                `Payment method: ${request.paymentMethod}\n\n` +
                "Confirming will mark this invoice as Paid."
        });
    }

    // CHAT MESSAGE HANDLER
    // ------------------------------------------

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const text = input.value.trim();

        if (!text || requestInProgress) {
            return;
        }

        addMessage(text, "user");
        input.value = "";

        requestInProgress = true;
        sendButton.disabled = true;
        input.disabled = true;

        const query = text
            .toLowerCase()
            .replace(/[!?.,]/g, "")
            .trim();

        try {
            // Continue an active admin action confirmation.
            if (!isCustomerPage && adminActionState.step) {
                await handleAdminActionConversation(text);
                return;
            }

            // Continue an active admin technician assignment.
            if (!isCustomerPage && adminTechnicianState.step) {
                await handleAdminTechnicianConversation(text);
                return;
            }

            // Continue an active admin status confirmation.
            if (!isCustomerPage && adminStatusState.step) {
                await handleAdminStatusConversation(text);
                return;
            }
            // Handle cancellation and rescheduling before booking detection.
            if (isCustomerPage && isCancellationRequest(query)) {
                resetBookingState();
                await startAppointmentManagement("cancel");
                return;
            }

            if (isCustomerPage && isRescheduleRequest(query)) {
                resetBookingState();
                await startAppointmentManagement("reschedule");
                return;
            }

            // Continue an active cancellation or rescheduling conversation.
            if (isCustomerPage && managementState.step) {
                await handleAppointmentManagement(text);
                return;
            }

            if (isCustomerPage && bookingState.step) {
                await handleBookingConversation(text);
                return;
            }

            // Greetings.
            if (
                /^(hi|hello|hey|good morning|good afternoon|good evening)$/.test(query)
            ) {
                addMessage(
                    "Hello! Welcome to our Vehicle Service Center. I can answer vehicle questions, check your appointments, or help you book a service.",
                    "bot"
                );
                return;
            }

            // Thank-you messages.
            if (
                /^(thanks|thank you|thank you so much|thanks a lot)$/.test(query)
            ) {
                addMessage(
                    "You're welcome! Is there anything else I can help you with?",
                    "bot"
                );
                return;
            }

            // Booking requests must be handled before general appointment matching.
            if (isCustomerPage && isBookingRequest(query)) {
                await startAppointmentBooking();
                return;
            }

            // Admin-only AI actions.
            if (!isCustomerPage) {

                const rescheduleRequest =
                    parseAdminRescheduleRequest(query);

                if (rescheduleRequest) {
                    await startAdminReschedule(rescheduleRequest);
                    return;
                }

                const recommendationRequest =
                    parseAdminTechnicianRecommendation(query);

                if (recommendationRequest) {
                    await showAdminTechnicianRecommendations(
                        recommendationRequest
                    );
                    return;
                }

                const stockRequest = parseAdminStockRequest(query);

                if (stockRequest) {
                    await startAdminStockAdjustment(stockRequest);
                    return;
                }

                const paymentRequest = parseAdminPaymentRequest(query);

                if (paymentRequest) {
                    await startAdminPaymentUpdate(paymentRequest);
                    return;
                }

                const estimateRequest = parseAdminEstimateRequest(query);

                if (estimateRequest) {
                    await prepareAdminFinancialAction(
                        estimateRequest,
                        "estimate"
                    );
                    return;
                }

                const invoiceRequest = parseAdminInvoiceRequest(query);

                if (invoiceRequest) {
                    await prepareAdminFinancialAction(
                        invoiceRequest,
                        "invoice"
                    );
                    return;
                }

                const technicianRequest =
                    parseAdminTechnicianAssignment(query);

                if (technicianRequest) {
                    await startAdminTechnicianAssignment(technicianRequest);
                    return;
                }

                const statusRequest = parseAdminStatusRequest(query);

                if (statusRequest) {
                    await startAdminStatusUpdate(statusRequest);
                    return;
                }

                await sendAdminMessage(text);
                return;
            }

            // Recognize appointment status questions.
            const asksStatus =
                /\b(status|progress|confirmed|confirmation|in progress|completed)\b/.test(query);

            const asksForAppointments =
                /\b(show|list|view|display)\b/.test(query) &&
                /\b(my|appointment|appointments|booking|bookings)\b/.test(query);

            const asksAboutAppointments =
                /\b(appointment|appointments|booking|bookings)\b/.test(query) ||
                (
                    /\b(track|check)\b/.test(query) &&
                    /\b(my|appointment|appointments|booking|bookings|status)\b/.test(query)
                );

            if (
                asksStatus ||
                asksForAppointments ||
                asksAboutAppointments
            ) {
                await getMyAppointments({
                    statusOnly: asksStatus && !asksForAppointments
                });
                return;
            }

            // Send general vehicle questions to Ollama through FastAPI.
            const token = localStorage.getItem("customer_access_token");

            if (!token) {
                addMessage(
                    "Please log in to your customer account to use the AI assistant.",
                    "bot"
                );
                return;
            }

            const response = await fetch(
                `${API_BASE_URL}/chatbot/message`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        message: text
                    })
                }
            );

            const data = await response.json().catch(() => ({}));

            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem("customer_access_token");

                throw new Error(
                    "Your customer session has expired. Please log in again."
                );
            }

            if (!response.ok) {
                throw new Error(
                    data.detail || "AI request failed."
                );
            }

            addMessage(
                data.reply || "Sorry, I couldn't generate a response.",
                "bot"
            );

        } catch (error) {
            console.error("Vehicle Service Assistant error:", error);

            addMessage(
                error.message ||
                "Sorry, the assistant is temporarily unavailable. Please try again.",
                "bot"
            );

        } finally {
            requestInProgress = false;
            sendButton.disabled = false;
            input.disabled = false;
            input.focus();
        }
    });

})();
