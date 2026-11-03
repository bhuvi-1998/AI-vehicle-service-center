
const API_URL = "http://127.0.0.1:8000";

const serviceForm = document.getElementById("serviceForm");
const serviceId = document.getElementById("service_id");
const serviceTable = document.getElementById("serviceTable");
const message = document.getElementById("message");
const cancelButton = document.getElementById("cancelButton");

async function loadServices() {
    try {
        const response = await apiFetch(`${API_URL}/services`);
        const services = await response.json();

        if (!response.ok) {
            throw new Error(
                services.detail || "Unable to load services."
            );
        }

        serviceTable.replaceChildren();

        services.forEach(service => {
            const row = document.createElement("tr");

            const values = [
                service.service_id,
                service.service_name,
                service.vehicle_type || "Car",
                service.description || "",
                Number(service.price).toLocaleString("en-IN", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                })
            ];

            values.forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            const actions = document.createElement("td");

            const editButton = document.createElement("button");
            editButton.type = "button";
            editButton.textContent = "Edit";
            editButton.addEventListener("click", () => {
                editService(service);
            });

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.textContent = "Delete";
            deleteButton.addEventListener("click", () => {
                deleteService(service.service_id);
            });

            actions.append(editButton, document.createTextNode(" "), deleteButton);
            row.appendChild(actions);
            serviceTable.appendChild(row);
        });

    } catch (error) {
        message.textContent = error.message;
    }
}

serviceForm.addEventListener("submit", async event => {
    event.preventDefault();

    const saveButton = serviceForm.querySelector(
        'button[type="submit"]'
    );
    saveButton.disabled = true;

    const serviceData = {
        service_name: document.getElementById("service_name").value.trim(),
        vehicle_type: document.getElementById("vehicle_type").value,
        description:
            document.getElementById("description").value.trim() || null,
        price: Number(document.getElementById("price").value)
    };

    try {
        const isEditing = Boolean(serviceId.value);

        const url = isEditing
            ? `${API_URL}/services/${serviceId.value}`
            : `${API_URL}/services`;

        const response = await apiFetch(url, {
            method: isEditing ? "PUT" : "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(serviceData)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail || "Unable to save service."
            );
        }

        message.textContent = result.message || "Service saved successfully.";
        serviceForm.reset();
        serviceId.value = "";
        cancelButton.hidden = true;

        await loadServices();

    } catch (error) {
        message.textContent = error.message;
    } finally {
        saveButton.disabled = false;
    }
});

function editService(service) {
    serviceId.value = service.service_id;

    document.getElementById("service_name").value =
        service.service_name;

    document.getElementById("vehicle_type").value =
        service.vehicle_type || "Car";

    document.getElementById("description").value =
        service.description || "";

    document.getElementById("price").value =
        service.price;

    cancelButton.hidden = false;
    message.textContent = `Editing service ${service.service_id}.`;
}

cancelButton.addEventListener("click", () => {
    serviceForm.reset();
    serviceId.value = "";
    cancelButton.hidden = true;
    message.textContent = "";
});

async function deleteService(id) {
    if (!confirm("Delete this service?")) {
        return;
    }

    try {
        const response = await apiFetch(
            `${API_URL}/services/${id}`,
            { method: "DELETE" }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail || "Unable to delete service."
            );
        }

        message.textContent = result.message || "Service deleted.";
        await loadServices();

    } catch (error) {
        message.textContent = error.message;
    }
}

loadServices();
