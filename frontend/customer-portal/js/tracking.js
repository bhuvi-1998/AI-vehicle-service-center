
const TRACKING_API = "http://127.0.0.1:8000";

let myRepairAppointments = [];

const repairSteps = [
    {
        title: "Pending",
        description: "Your service booking has been received."
    },
    {
        title: "Confirmed",
        description: "Your appointment has been confirmed."
    },
    {
        title: "Vehicle Received",
        description: "The service center has received your vehicle."
    },
    {
        title: "In Progress",
        description: "Repair or maintenance work is in progress."
    },
    {
        title: "Ready for Pickup",
        description: "The vehicle is ready for collection."
    },
    {
        title: "Completed",
        description: "The service process is marked as completed."
    }
];

async function loadRepairAppointments() {
    const message = document.getElementById("trackingMessage");
    const token = localStorage.getItem("customer_access_token");

    if (!token) {
        window.location.replace("login.html");
        return;
    }

    try {
        const response = await fetch(
            `${TRACKING_API}/customer-portal/appointments`,
            {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        );

        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem("customer_access_token");
            window.location.replace("login.html");
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Unable to load repair information."
            );
        }

        myRepairAppointments = data;
        displayRepairAppointments(myRepairAppointments);

    } catch (error) {
        message.textContent =
            error.message || "Could not connect to the backend.";
    }
}

function createTextElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    element.textContent = text;
    return element;
}

function createRepairTimeline(statusValue) {
    const section = document.createElement("section");
    section.className = "tracking-progress";

    section.appendChild(
        createTextElement("h3", "", "Repair Progress")
    );

    if (statusValue === "Cancelled") {
        section.appendChild(
            createTextElement(
                "p",
                "tracking-cancelled",
                "This appointment has been cancelled."
            )
        );

        return section;
    }

    const currentIndex = repairSteps.findIndex(
        step => step.title === statusValue
    );

    if (currentIndex === -1) {
        section.appendChild(
            createTextElement(
                "p",
                "",
                "The current status is not part of the standard repair timeline."
            )
        );

        return section;
    }

    const timeline = document.createElement("ol");
    timeline.className = "progress-timeline";

    repairSteps.forEach((step, index) => {
        const item = document.createElement("li");
        item.className = "progress-step";

        if (index < currentIndex ||
            (currentIndex === repairSteps.length - 1)) {
            item.classList.add("is-complete");
        } else if (index === currentIndex) {
            item.classList.add("is-current");
        }

        const dot = createTextElement(
            "span",
            "progress-dot",
            index < currentIndex ||
            currentIndex === repairSteps.length - 1
                ? "✓"
                : String(index + 1)
        );

        const content = document.createElement("div");

        content.appendChild(
            createTextElement(
                "div",
                "progress-title",
                step.title
            )
        );

        content.appendChild(
            createTextElement(
                "span",
                "progress-description",
                step.description
            )
        );

        if (index === currentIndex) {
            content.appendChild(
                createTextElement(
                    "span",
                    "progress-description",
                    "Current status"
                )
            );
        }

        item.append(dot, content);
        timeline.appendChild(item);
    });

    section.appendChild(timeline);
    return section;
}

function displayRepairAppointments(appointments) {
    const results = document.getElementById("trackingResults");
    const message = document.getElementById("trackingMessage");

    results.replaceChildren();

    if (appointments.length === 0) {
        message.textContent =
            "No matching appointments were found in your account.";
        return;
    }

    message.textContent =
        `Showing ${appointments.length} appointment(s) from your account.`;

    appointments.forEach(appointment => {
        const card = document.createElement("article");
        card.className = "tracking-card";

        card.appendChild(
            createTextElement("h2", "", appointment.service_name)
        );

        const details = [
            `Appointment ID: ${appointment.appointment_id}`,
            `Vehicle: ${appointment.vehicle_number} — ${appointment.brand} ${appointment.model}`,
            `Appointment date: ${appointment.appointment_date}`,
            `Appointment time: ${appointment.appointment_time}`,
            `Service price: ₹${Number(appointment.price).toLocaleString("en-IN")}`
        ];

        details.forEach(detail => {
            card.appendChild(
                createTextElement("p", "", detail)
            );
        });

        const statusValue = appointment.status || "Not updated";

        card.appendChild(
            createTextElement(
                "p",
                "",
                "Latest recorded status:"
            )
        );

        card.appendChild(
            createTextElement(
                "span",
                "tracking-status",
                statusValue
            )
        );

        card.appendChild(createRepairTimeline(statusValue));

        results.appendChild(card);
    });
}

document
    .getElementById("trackingSearch")
    .addEventListener("submit", event => {
        event.preventDefault();

        const query = document
            .getElementById("appointmentSearch")
            .value.trim().toLowerCase();

        const filtered = myRepairAppointments.filter(appointment =>
            String(appointment.appointment_id).includes(query) ||
            String(appointment.vehicle_number)
                .toLowerCase()
                .includes(query)
        );

        displayRepairAppointments(filtered);
    });

document
    .getElementById("showAllButton")
    .addEventListener("click", () => {
        document.getElementById("appointmentSearch").value = "";
        displayRepairAppointments(myRepairAppointments);
    });

loadRepairAppointments();
