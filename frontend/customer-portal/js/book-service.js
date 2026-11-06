const CUSTOMER_API = window.API_BASE_URL;

let customerVehicles = [];
let availableServices = [];

async function customerRequest(path, options = {}) {
    const token = localStorage.getItem("customer_access_token");

    if (!token) {
        window.location.replace("login.html");
        throw new Error("Please log in to continue.");
    }

    const headers = {
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`
    };

    if (options.body) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${CUSTOMER_API}${path}`, {
        ...options,
        headers
    });

    const data = await response.json().catch(() => ({}));

    if (response.status === 401 || response.status === 403) {
        localStorage.removeItem("customer_access_token");
        window.location.replace("login.html");
        throw new Error("Your session expired. Please log in again.");
    }

    if (!response.ok) {
        throw new Error(data.detail || "The request failed.");
    }

    return data;
}

function showPortalMessage(id, text, error = false) {
    const element = document.getElementById(id);
    element.textContent = text;
    element.style.color = error ? "#FF9A9A" : "#86E3A1";
}

function addOption(select, value, label) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
}


// Show services matching the selected vehicle category
function updateServicesForVehicle() {

    const vehicleSelect =
        document.getElementById("bookingVehicle");

    const serviceSelect =
        document.getElementById("bookingService");

    serviceSelect.replaceChildren();

    addOption(serviceSelect, "", "Select a service");

    const selectedVehicle = customerVehicles.find(
        vehicle =>
            String(vehicle.vehicle_id) === vehicleSelect.value
    );

    if (!selectedVehicle) {
        serviceSelect.disabled = true;
        addOptionPlaceholderMessage();
        return;
    }

    serviceSelect.disabled = false;

    const vehicleType =
        selectedVehicle.vehicle_type || "Car";

    const matchingServices = availableServices.filter(
        service =>
            service.vehicle_type === vehicleType ||
            service.vehicle_type === "All"
    );

    matchingServices.forEach(service => {
        addOption(
            serviceSelect,
            service.service_id,
            `${service.service_name} - INR ${Number(service.price).toLocaleString("en-IN")}`
        );
    });

    if (!matchingServices.length) {
        showPortalMessage(
            "bookingMessage",
            `No services are available for ${vehicleType} vehicles.`,
            true
        );
    } else {
        showPortalMessage("bookingMessage", "");
    }
}


function addOptionPlaceholderMessage() {
    const serviceSelect =
        document.getElementById("bookingService");

    addOption(serviceSelect, "", "Select a vehicle first");
}


async function loadVehiclesAndServices() {

    try {

        const [vehicles, services] = await Promise.all([
            customerRequest("/customer-portal/vehicles"),
            customerRequest("/customer-portal/services")
        ]);

        const vehicleSelect =
            document.getElementById("bookingVehicle");

        const vehicleContainer =
            document.getElementById("myVehicles");

        customerVehicles = vehicles;
        availableServices = services;

        vehicleSelect.replaceChildren();
        vehicleContainer.replaceChildren();

        addOption(vehicleSelect, "", "Select a vehicle");

        customerVehicles.forEach(vehicle => {

            const vehicleType =
                vehicle.vehicle_type || "Car";

            addOption(
                vehicleSelect,
                vehicle.vehicle_id,
                `${vehicle.vehicle_number} - ${vehicle.brand} ${vehicle.model} (${vehicleType})`
            );

            const item = document.createElement("p");

            item.textContent =
                `${vehicle.vehicle_number} - ${vehicle.brand} ${vehicle.model}` +
                ` | Category: ${vehicleType}` +
                (vehicle.manufacture_year
                    ? ` | Year: ${vehicle.manufacture_year}`
                    : "");

            vehicleContainer.appendChild(item);
        });

        if (!customerVehicles.length) {
            vehicleContainer.textContent =
                "You have not added a vehicle yet.";
        }

        updateServicesForVehicle();

        if (!availableServices.length) {
            showPortalMessage(
                "bookingMessage",
                "No services are available yet.",
                true
            );
        }

    } catch (error) {

        showPortalMessage(
            "bookingMessage",
            error.message,
            true
        );

    }
}


// Update service options whenever the customer changes vehicles
document.getElementById("bookingVehicle").addEventListener(
    "change",
    updateServicesForVehicle
);


const dateInput =
    document.getElementById("appointmentDate");

const now = new Date();

dateInput.min = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0")
].join("-");


document.getElementById("vehicleForm").addEventListener(
    "submit",
    async event => {

        event.preventDefault();

        const button = event.submitter;
        button.disabled = true;

        const yearValue =
            document.getElementById("vehicleYear").value;

        const vehicle = {

            vehicle_number:
                document.getElementById(
                    "vehicleNumber"
                ).value.trim(),

            vehicle_type:
                document.getElementById(
                    "vehicleType"
                ).value,

            brand:
                document.getElementById(
                    "vehicleBrand"
                ).value.trim(),

            model:
                document.getElementById(
                    "vehicleModel"
                ).value.trim(),

            manufacture_year:
                yearValue ? Number(yearValue) : null
        };

        try {

            const result = await customerRequest(
                "/customer-portal/vehicles",
                {
                    method: "POST",
                    body: JSON.stringify(vehicle)
                }
            );

            showPortalMessage(
                "vehicleMessage",
                result.message
            );

            event.target.reset();

            await loadVehiclesAndServices();

        } catch (error) {

            showPortalMessage(
                "vehicleMessage",
                error.message,
                true
            );

        } finally {

            button.disabled = false;

        }

    }
);


document.getElementById("bookingForm").addEventListener(
    "submit",
    async event => {

        event.preventDefault();

        const button = event.submitter;
        button.disabled = true;

        const booking = {

            vehicle_id: Number(
                document.getElementById(
                    "bookingVehicle"
                ).value
            ),

            service_id: Number(
                document.getElementById(
                    "bookingService"
                ).value
            ),

            appointment_date:
                document.getElementById(
                    "appointmentDate"
                ).value,

            appointment_time:
                document.getElementById(
                    "appointmentTime"
                ).value

        };

        try {

            const result = await customerRequest(
                "/customer-portal/appointments",
                {
                    method: "POST",
                    body: JSON.stringify(booking)
                }
            );

            showPortalMessage(
                "bookingMessage",
                `${result.message} Appointment ID: ${result.appointment_id}. Status: ${result.status}.`
            );

            event.target.reset();
            updateServicesForVehicle();

        } catch (error) {

            showPortalMessage(
                "bookingMessage",
                error.message,
                true
            );

        } finally {

            button.disabled = false;

        }

    }
);


loadVehiclesAndServices();