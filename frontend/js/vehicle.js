
const API_URL = "http://127.0.0.1:8000";

const vehicleForm = document.getElementById("vehicleForm");
const customerSelect = document.getElementById("customer_id");
const customerMessage = document.getElementById("customerMessage");
const message = document.getElementById("message");
const vehicleTable = document.getElementById("vehicleTable");


async function loadCustomers() {

    try {

        const response = await apiFetch(
            `${API_URL}/customers`
        );

        const customers = await response.json();

        if (!response.ok) {
            throw new Error(
                customers.detail || "Unable to load customers"
            );
        }

        customerSelect.innerHTML =
            '<option value="">Select Customer</option>';

        if (customers.length === 0) {

            customerMessage.textContent =
                "Please add a customer before adding a vehicle.";

            vehicleForm.hidden = true;

            return;
        }

        customerMessage.textContent = "";

        vehicleForm.hidden = false;


        customers.forEach(function(customer) {

            const option = document.createElement("option");

            option.value = customer.customer_id;

            option.textContent = customer.customer_name;

            customerSelect.appendChild(option);
        });

    }
    catch (error) {

        customerMessage.textContent =
            error.message;

        vehicleForm.hidden = true;
    }
}


async function loadVehicles() {

    try {

        const response = await apiFetch(
            `${API_URL}/vehicles`
        );

        const vehicles = await response.json();

        if (!response.ok) {
            throw new Error(
                vehicles.detail || "Unable to load vehicles"
            );
        }

        vehicleTable.innerHTML = "";


        vehicles.forEach(function(vehicle) {

            const row = document.createElement("tr");


            const vehicleIdCell =
                document.createElement("td");

            vehicleIdCell.textContent =
                vehicle.vehicle_id;


            const customerIdCell =
                document.createElement("td");

            customerIdCell.textContent =
                vehicle.customer_id;





            const numberCell =
                document.createElement("td");

            numberCell.textContent =
                vehicle.vehicle_number;

            const typeCell =
                document.createElement("td");

            typeCell.textContent =
                vehicle.vehicle_type || "Car";


            const brandCell =
                document.createElement("td");

            brandCell.textContent =
                vehicle.brand;


            const modelCell =
                document.createElement("td");

            modelCell.textContent =
                vehicle.model;


            const yearCell =
                document.createElement("td");

            yearCell.textContent =
                vehicle.manufacture_year || "";


            const actionCell =
                document.createElement("td");


            const deleteButton =
                document.createElement("button");

            deleteButton.textContent = "Delete";


            deleteButton.addEventListener(
                "click",
                function() {
                    deleteVehicle(vehicle.vehicle_id);
                }
            );


            actionCell.appendChild(deleteButton);


            row.appendChild(vehicleIdCell);
            row.appendChild(customerIdCell);

            row.appendChild(numberCell);
            row.appendChild(typeCell);
            row.appendChild(brandCell);
            row.appendChild(modelCell);
            row.appendChild(yearCell);
            row.appendChild(actionCell);


            vehicleTable.appendChild(row);

        });

    }
    catch (error) {

        message.textContent =
            error.message;
    }
}


vehicleForm.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();


        const vehicleData = {

            customer_id:
                Number(
                    document.getElementById(
                        "customer_id"
                    ).value
                ),

            // Vehicle Category
            vehicle_type:
                document.getElementById(
                    "vehicle_type"
                ).value,

            vehicle_number:
                document.getElementById(
                    "vehicle_number"
                ).value,

            brand:
                document.getElementById(
                    "brand"
                ).value,

            model:
                document.getElementById(
                    "model"
                ).value,

            manufacture_year:
                document.getElementById(
                    "manufacture_year"
                ).value
                ? Number(
                    document.getElementById(
                        "manufacture_year"
                    ).value
                )
                : null
        };


        try {

            const response = await apiFetch(
                `${API_URL}/vehicles`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify(vehicleData)
                }
            );


            const result = await response.json();


            if (!response.ok) {

                throw new Error(
                    result.detail ||
                    "Unable to add vehicle"
                );
            }


            message.textContent =
                result.message;

            vehicleForm.reset();

            await loadVehicles();

        }
        catch (error) {

            message.textContent =
                error.message;
        }

    }
);


async function deleteVehicle(vehicleId) {

    try {

        const response = await apiFetch(
            `${API_URL}/vehicles/${vehicleId}`,
            {
                method: "DELETE"
            }
        );


        const result = await response.json();


        if (!response.ok) {

            throw new Error(
                result.detail ||
                "Unable to delete vehicle"
            );
        }


        message.textContent =
            result.message;

        await loadVehicles();

    }
    catch (error) {

        message.textContent =
            error.message;
    }
}


loadCustomers();
loadVehicles();
