const API_URL = "http://127.0.0.1:8000";

const invoiceForm = document.getElementById("invoiceForm");
const appointmentSelect = document.getElementById("appointment_id");
const partsContainer = document.getElementById("partsContainer");
const invoiceTable = document.getElementById("invoiceTable");
const requirementMessage = document.getElementById("requirementMessage");
const message = document.getElementById("message");

let appointments = [];
let parts = [];
let invoices = [];


async function getJson(url, options = {}) {

    const response = await apiFetch(url, options);
    const result = await response.json();

    if (!response.ok) {
        throw new Error(
            result.detail || "The request failed."
        );
    }

    return result;
}


async function loadAppointments() {

    appointments = await getJson(`${API_URL}/appointments`);
}


async function loadParts() {

    parts = await getJson(`${API_URL}/parts`);

    partsContainer.replaceChildren();

    if (parts.length === 0) {

        const note = document.createElement("p");

        note.textContent =
            "No parts are registered. You can create a bill without parts.";

        partsContainer.appendChild(note);

        return;
    }

    parts.forEach(function(part) {

        const row = document.createElement("div");
        row.dataset.partRow = "true";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = part.part_id;
        checkbox.disabled = Number(part.quantity) < 1;

        const label = document.createElement("label");

        label.appendChild(checkbox);

        label.appendChild(
            document.createTextNode(
                ` ${part.part_name} (${part.part_number}) - ` +
                `INR ${Number(part.price).toFixed(2)} - ` +
                `Available: ${part.quantity}`
            )
        );

        const quantityLabel = document.createElement("label");
        quantityLabel.textContent = " Quantity: ";

        const quantityInput = document.createElement("input");
        quantityInput.type = "number";
        quantityInput.min = "1";
        quantityInput.max = String(part.quantity);
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
        partsContainer.appendChild(document.createElement("br"));
    });
}


function renderAppointmentOptions() {

    appointmentSelect.replaceChildren();

    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = "Select Appointment";

    appointmentSelect.appendChild(emptyOption);

    const invoicedIds = new Set(
        invoices.map(function(invoice) {
            return Number(invoice.appointment_id);
        })
    );

    const completedAppointments = appointments.filter(
        function(appointment) {
            return String(appointment.status).toLowerCase() === "completed";
        }
    );

    const availableAppointments = completedAppointments.filter(
        function(appointment) {
            return !invoicedIds.has(Number(appointment.appointment_id));
        }
    );

    availableAppointments.forEach(function(appointment) {

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

    invoiceForm.hidden = availableAppointments.length === 0;

    if (availableAppointments.length === 0) {

        if (completedAppointments.length === 0) {

            requirementMessage.textContent =
                "Mark an appointment as Completed before generating a final bill.";

        } else {

            requirementMessage.textContent =
                "All completed appointments already have final invoices.";

        }

    } else {

        requirementMessage.textContent = "";

    }
}


function addCell(row, value) {

    const cell = document.createElement("td");

    cell.textContent = value ?? "";

    row.appendChild(cell);

    return cell;
}


async function loadInvoices() {

    invoices = await getJson(`${API_URL}/invoices`);

    invoiceTable.replaceChildren();

    invoices.forEach(function(invoice) {

        const row = document.createElement("tr");

        addCell(row, invoice.invoice_id);
        addCell(row, invoice.appointment_id);
        addCell(row, invoice.customer_name);
        addCell(row, invoice.vehicle_number);

        addCell(
            row,
            `INR ${Number(invoice.total_amount).toFixed(2)}`
        );

        addCell(row, invoice.payment_status);
        addCell(row, invoice.payment_method || "");
        addCell(row, invoice.invoice_date);

        const actionsCell = document.createElement("td");

        // Download the PDF with the admin authentication token.
        const pdfButton = document.createElement("button");

        pdfButton.type = "button";
        pdfButton.textContent = "Download Bill PDF";

        pdfButton.addEventListener("click", async function() {

            try {

                await downloadProtectedPdf(
                    `${API_URL}/invoices/${invoice.invoice_id}/pdf`,
                    `invoice-${invoice.invoice_id}.pdf`
                );

                message.textContent =
                    `Invoice ${invoice.invoice_id} PDF downloaded.`;

            } catch (error) {

                message.textContent = error.message;

            }

        });

        actionsCell.appendChild(pdfButton);

        if (invoice.payment_status !== "Paid") {

            actionsCell.appendChild(
                document.createElement("br")
            );

            const paymentSelect = document.createElement("select");

            const paymentOptions = [
                ["", "Select Payment Method"],
                ["Cash", "Cash"],
                ["UPI", "UPI"],
                ["Card", "Card"],
                ["Bank Transfer", "Bank Transfer"]
            ];

            paymentOptions.forEach(function(item) {

                const option = document.createElement("option");

                option.value = item[0];
                option.textContent = item[1];

                paymentSelect.appendChild(option);
            });

            const paidButton = document.createElement("button");

            paidButton.type = "button";
            paidButton.textContent = "Mark Paid";

            paidButton.addEventListener("click", async function() {

                if (!paymentSelect.value) {

                    message.textContent =
                        "Select a payment method first.";

                    return;
                }

                try {

                    await getJson(
                        `${API_URL}/invoices/${invoice.invoice_id}/payment`,
                        {
                            method: "PUT",

                            headers: {
                                "Content-Type": "application/json"
                            },

                            body: JSON.stringify({
                                payment_method: paymentSelect.value
                            })
                        }
                    );

                    message.textContent =
                        "Invoice payment updated.";

                    await loadInvoices();

                } catch (error) {

                    message.textContent = error.message;

                }

            });

            actionsCell.appendChild(paymentSelect);
            actionsCell.appendChild(paidButton);
        }

        row.appendChild(actionsCell);

        invoiceTable.appendChild(row);
    });

    renderAppointmentOptions();
}


invoiceForm.addEventListener("submit", async function(event) {

    event.preventDefault();

    const selectedParts = [];

    const rows = partsContainer.querySelectorAll(
        '[data-part-row="true"]'
    );

    for (const row of rows) {

        const checkbox = row.querySelector(
            'input[type="checkbox"]'
        );

        const quantityInput = row.querySelector(
            'input[type="number"]'
        );

        if (checkbox.checked) {

            const quantity = Number(quantityInput.value);
            const available = Number(quantityInput.max);

            if (
                !Number.isInteger(quantity) ||
                quantity < 1 ||
                quantity > available
            ) {

                message.textContent =
                    "Enter a valid part quantity within the available stock.";

                return;
            }

            selectedParts.push({
                part_id: Number(checkbox.value),
                quantity: quantity
            });
        }
    }

    const discountText =
        document.getElementById("discount_amount").value;

    const discount = discountText === ""
        ? 0
        : Number(discountText);

    if (!Number.isFinite(discount) || discount < 0) {

        message.textContent =
            "Enter a valid discount amount.";

        return;
    }

    const invoiceData = {

        appointment_id: Number(appointmentSelect.value),

        parts: selectedParts,

        discount_amount: discount,

        notes:
            document.getElementById("notes").value || null
    };

    try {

        const result = await getJson(`${API_URL}/invoices`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(invoiceData)
        });

        message.textContent =
            `Invoice #${result.invoice_id} created successfully.`;

        invoiceForm.reset();

        await loadParts();
        await loadInvoices();

    } catch (error) {

        message.textContent = error.message;

    }

});


async function initializePage() {

    try {

        await loadAppointments();
        await loadParts();
        await loadInvoices();

    } catch (error) {

        requirementMessage.textContent = error.message;
        invoiceForm.hidden = true;

    }

}


initializePage();