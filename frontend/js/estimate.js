const API_URL = "http://127.0.0.1:8000";

const estimateForm = document.getElementById("estimateForm");
const appointmentSelect = document.getElementById("appointment_id");
const partsContainer = document.getElementById("partsContainer");
const estimateTable = document.getElementById("estimateTable");
const requirementMessage = document.getElementById("requirementMessage");
const message = document.getElementById("message");


function addCell(row, value) {

    const cell = document.createElement("td");

    cell.textContent = value ?? "";

    row.appendChild(cell);
}


async function loadAppointments() {

    const response = await apiFetch(
        `${API_URL}/appointments`
    );

    const appointments = await response.json();

    if (!response.ok) {
        throw new Error(
            appointments.detail || "Unable to load appointments."
        );
    }

    appointmentSelect.innerHTML =
        '<option value="">Select Appointment</option>';

    appointments.forEach(function(appointment) {

        const option = document.createElement("option");

        option.value = appointment.appointment_id;

        option.textContent =
            `Appointment #${appointment.appointment_id} - ` +
            `${appointment.customer_name} - ` +
            `${appointment.vehicle_number} - ` +
            `${appointment.service_name} - ` +
            `${appointment.appointment_date}`;

        appointmentSelect.appendChild(option);
    });

    estimateForm.hidden = appointments.length === 0;

    if (appointments.length === 0) {

        requirementMessage.textContent =
            "Create an appointment before generating a service estimate.";

    } else {

        requirementMessage.textContent = "";

    }
}


async function loadParts() {

    const response = await apiFetch(
        `${API_URL}/parts`
    );

    const parts = await response.json();

    if (!response.ok) {
        throw new Error(
            parts.detail || "Unable to load parts."
        );
    }

    partsContainer.replaceChildren();

    if (parts.length === 0) {

        const note = document.createElement("p");

        note.textContent =
            "No parts have been registered. You can create an estimate without parts.";

        partsContainer.appendChild(note);

        return;
    }

    parts.forEach(function(part) {

        const row = document.createElement("div");

        row.dataset.partRow = "true";

        const checkbox = document.createElement("input");

        checkbox.type = "checkbox";
        checkbox.value = part.part_id;

        const label = document.createElement("label");

        label.appendChild(checkbox);

        label.appendChild(
            document.createTextNode(
                ` ${part.part_name} (${part.part_number}) - ` +
                `INR ${Number(part.price).toFixed(2)} - ` +
                `Current stock: ${part.quantity}`
            )
        );

        const quantityLabel = document.createElement("label");

        quantityLabel.textContent = " Quantity: ";

        const quantityInput = document.createElement("input");

        quantityInput.type = "number";
        quantityInput.min = "1";
        quantityInput.step = "1";
        quantityInput.disabled = true;

        quantityInput.setAttribute(
            "aria-label",
            `Quantity for ${part.part_name}`
        );

        checkbox.addEventListener("change", function() {

            quantityInput.disabled = !checkbox.checked;
            quantityInput.required = checkbox.checked;

            if (!checkbox.checked) {
                quantityInput.value = "";
            }
        });

        row.appendChild(label);
        row.appendChild(quantityLabel);
        row.appendChild(quantityInput);

        partsContainer.appendChild(row);

        partsContainer.appendChild(
            document.createElement("br")
        );
    });
}


async function loadEstimates() {

    const response = await apiFetch(
        `${API_URL}/estimates`
    );

    const estimates = await response.json();

    if (!response.ok) {
        throw new Error(
            estimates.detail || "Unable to load estimates."
        );
    }

    estimateTable.replaceChildren();

    estimates.forEach(function(estimate) {

        const row = document.createElement("tr");

        addCell(row, estimate.estimate_id);
        addCell(row, estimate.appointment_id);
        addCell(row, estimate.customer_name);
        addCell(row, estimate.vehicle_number);

        addCell(
            row,
            `INR ${Number(estimate.total_amount).toFixed(2)}`
        );

        addCell(row, estimate.estimate_date);


        // Download the PDF using the authentication token.
        const pdfCell = document.createElement("td");

        const pdfButton = document.createElement("button");

        pdfButton.type = "button";
        pdfButton.textContent = "Download PDF";

        pdfButton.addEventListener("click", async function() {

            pdfButton.disabled = true;

            try {

                await downloadProtectedPdf(
                    `${API_URL}/estimates/${estimate.estimate_id}/pdf`,
                    `service-estimate-${estimate.estimate_id}.pdf`
                );

                message.textContent =
                    `Estimate ${estimate.estimate_id} PDF downloaded successfully.`;

            } catch (error) {

                message.textContent = error.message;

            } finally {

                pdfButton.disabled = false;

            }

        });

        pdfCell.appendChild(pdfButton);

        row.appendChild(pdfCell);

        estimateTable.appendChild(row);
    });
}


estimateForm.addEventListener("submit", async function(event) {

    event.preventDefault();

    const selectedParts = [];

    const partRows = partsContainer.querySelectorAll(
        '[data-part-row="true"]'
    );

    for (const row of partRows) {

        const checkbox = row.querySelector(
            'input[type="checkbox"]'
        );

        const quantityInput = row.querySelector(
            'input[type="number"]'
        );

        if (checkbox.checked) {

            const quantity = Number(quantityInput.value);

            if (
                !quantityInput.value ||
                !Number.isInteger(quantity) ||
                quantity < 1
            ) {

                message.textContent =
                    "Enter a valid quantity for every selected part.";

                return;
            }

            selectedParts.push({
                part_id: Number(checkbox.value),
                quantity: quantity
            });
        }
    }

    if (!appointmentSelect.value) {

        message.textContent =
            "Please select an appointment.";

        return;
    }

    const estimateData = {

        appointment_id: Number(appointmentSelect.value),

        parts: selectedParts,

        notes:
            document.getElementById("notes").value || null
    };

    try {

        const response = await apiFetch(
            `${API_URL}/estimates`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(estimateData)
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail || "Unable to create estimate."
            );
        }

        message.textContent =
            `Estimate #${result.estimate_id} created successfully. ` +
            "You can download the PDF from the saved estimates table.";

        estimateForm.reset();

        partsContainer.querySelectorAll(
            'input[type="checkbox"]'
        ).forEach(function(checkbox) {

            checkbox.checked = false;

        });

        partsContainer.querySelectorAll(
            'input[type="number"]'
        ).forEach(function(input) {

            input.value = "";
            input.disabled = true;
            input.required = false;

        });

        await loadEstimates();

    } catch (error) {

        message.textContent = error.message;

    }
});


async function initializePage() {

    try {

        await loadAppointments();

        await loadParts();

        await loadEstimates();

    } catch (error) {

        requirementMessage.textContent = error.message;

        estimateForm.hidden = true;

    }
}


initializePage();