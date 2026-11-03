const API_URL = "http://127.0.0.1:8000";

const partForm =
    document.getElementById("partForm");

const partId =
    document.getElementById("part_id");

const partTable =
    document.getElementById("partTable");

const message =
    document.getElementById("message");

const cancelButton =
    document.getElementById("cancelButton");


async function loadParts() {

    try {

        const response =
            await apiFetch(`${API_URL}/parts`);

        const parts =
            await response.json();

        if (!response.ok) {

            throw new Error(
                parts.detail ||
                "Unable to load parts"
            );
        }

        partTable.innerHTML = "";


        parts.forEach(function(part) {

            const row =
                document.createElement("tr");


            const idCell =
                document.createElement("td");

            idCell.textContent =
                part.part_id;


            const nameCell =
                document.createElement("td");

            nameCell.textContent =
                part.part_name;


            // Vehicle Category
            const vehicleTypeCell =
                document.createElement("td");

            vehicleTypeCell.textContent =
                part.vehicle_type || "All";


            const numberCell =
                document.createElement("td");

            numberCell.textContent =
                part.part_number;


            const quantityCell =
                document.createElement("td");

            quantityCell.textContent =
                part.quantity;


            const priceCell =
                document.createElement("td");

            priceCell.textContent =
                part.price;


            const actionCell =
                document.createElement("td");


            const editButton =
                document.createElement("button");

            editButton.textContent =
                "Edit";

            editButton.addEventListener(
                "click",
                function() {

                    editPart(part);

                }
            );


            const deleteButton =
                document.createElement("button");

            deleteButton.textContent =
                "Delete";

            deleteButton.addEventListener(
                "click",
                function() {

                    deletePart(part.part_id);

                }
            );


            actionCell.appendChild(editButton);

            actionCell.appendChild(
                document.createTextNode(" ")
            );

            actionCell.appendChild(deleteButton);


            row.appendChild(idCell);
            row.appendChild(nameCell);
            row.appendChild(vehicleTypeCell);
            row.appendChild(numberCell);
            row.appendChild(quantityCell);
            row.appendChild(priceCell);
            row.appendChild(actionCell);


            partTable.appendChild(row);

        });

    }
    catch (error) {

        message.textContent =
            error.message;

    }

}


partForm.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();


        const partData = {

            part_name:
                document.getElementById(
                    "part_name"
                ).value,

            // Vehicle Category
            vehicle_type:
                document.getElementById(
                    "vehicle_type"
                ).value,

            part_number:
                document.getElementById(
                    "part_number"
                ).value,

            quantity:
                Number(
                    document.getElementById(
                        "quantity"
                    ).value
                ),

            price:
                Number(
                    document.getElementById(
                        "price"
                    ).value
                )

        };


        try {

            let response;


            if (partId.value) {

                response =
                    await apiFetch(
                        `${API_URL}/parts/${partId.value}`,
                        {
                            method: "PUT",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(partData)
                        }
                    );

            }
            else {

                response =
                    await apiFetch(
                        `${API_URL}/parts`,
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(partData)
                        }
                    );

            }


            const result =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    result.detail ||
                    "Operation failed"
                );

            }


            message.textContent =
                result.message;

            partForm.reset();

            partId.value = "";

            cancelButton.hidden = true;

            await loadParts();

        }
        catch (error) {

            message.textContent =
                error.message;

        }

    }
);


function editPart(part) {

    partId.value =
        part.part_id;

    document.getElementById(
        "part_name"
    ).value =
        part.part_name;

    // Vehicle Category
    document.getElementById(
        "vehicle_type"
    ).value =
        part.vehicle_type || "All";

    document.getElementById(
        "part_number"
    ).value =
        part.part_number;

    document.getElementById(
        "quantity"
    ).value =
        part.quantity;

    document.getElementById(
        "price"
    ).value =
        part.price;

    cancelButton.hidden = false;

}


cancelButton.addEventListener(
    "click",
    function() {

        partForm.reset();

        partId.value = "";

        cancelButton.hidden = true;

        message.textContent = "";

    }
);


async function deletePart(id) {

    try {

        const response =
            await apiFetch(
                `${API_URL}/parts/${id}`,
                {
                    method: "DELETE"
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.detail ||
                "Unable to delete part"
            );

        }


        message.textContent =
            result.message;

        await loadParts();

    }
    catch (error) {

        message.textContent =
            error.message;

    }

}


loadParts();