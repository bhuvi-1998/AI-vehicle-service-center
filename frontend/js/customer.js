const API_URL = window.API_BASE_URL;

const customerForm = document.getElementById("customerForm");
const customerTable = document.getElementById("customerTable");
const message = document.getElementById("message");
const customerId = document.getElementById("customer_id");
const cancelButton = document.getElementById("cancelButton");


async function loadCustomers() {
    try {
        const response = await apiFetch(`${API_URL}/customers`);
        const customers = await response.json();

        if (!response.ok) {
            throw new Error(
                customers.detail || "Unable to load customers"
            );
        }

        customerTable.replaceChildren();

        customers.forEach(function(customer) {
            const row = document.createElement("tr");

            const fields = [
                customer.customer_id,
                customer.customer_name,
                customer.phone,
                customer.email || "",
                customer.address || ""
            ];

            fields.forEach(function(value) {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            const actionCell = document.createElement("td");

            const editButton = document.createElement("button");
            editButton.type = "button";
            editButton.textContent = "Edit";
            editButton.addEventListener("click", function() {
                editCustomer(customer);
            });

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.textContent = "Delete";
            deleteButton.addEventListener("click", function() {
                deleteCustomer(customer.customer_id);
            });

            actionCell.appendChild(editButton);
            actionCell.appendChild(document.createTextNode(" "));
            actionCell.appendChild(deleteButton);

            row.appendChild(actionCell);
            customerTable.appendChild(row);
        });

    } catch (error) {
        message.textContent = error.message;
    }
}


customerForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const data = {
        customer_name:
            document.getElementById("customer_name").value.trim(),

        phone:
            document.getElementById("phone").value.trim(),

        email:
            document.getElementById("email").value.trim() || null,

        address:
            document.getElementById("address").value.trim() || null
    };

    try {
        let response;

        if (customerId.value) {
            response = await apiFetch(
                `${API_URL}/customers/${customerId.value}`,
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
                `${API_URL}/customers`,
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
            throw new Error(result.detail || "Operation failed");
        }

        customerForm.reset();
        customerId.value = "";
        cancelButton.hidden = true;

        await loadCustomers();

        message.textContent = result.message;

    } catch (error) {
        message.textContent = error.message;
    }
});


function editCustomer(customer) {
    customerId.value = customer.customer_id;

    document.getElementById("customer_name").value =
        customer.customer_name;

    document.getElementById("phone").value =
        customer.phone;

    document.getElementById("email").value =
        customer.email || "";

    document.getElementById("address").value =
        customer.address || "";

    cancelButton.hidden = false;
}


cancelButton.addEventListener("click", function() {
    customerForm.reset();
    customerId.value = "";
    cancelButton.hidden = true;
    message.textContent = "";
});


async function deleteCustomer(id) {
    try {
        const response = await apiFetch(
            `${API_URL}/customers/${id}`,
            {
                method: "DELETE"
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail || "Unable to delete customer"
            );
        }

        message.textContent = result.message;

        await loadCustomers();

    } catch (error) {
        message.textContent = error.message;
    }
}


loadCustomers();