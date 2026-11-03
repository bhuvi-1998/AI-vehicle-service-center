const API_URL = "http://127.0.0.1:8000";

const technicianForm =
    document.getElementById("technicianForm");

const technicianTable =
    document.getElementById("technicianTable");

const technicianId =
    document.getElementById("technician_id");

const message =
    document.getElementById("message");

const cancelButton =
    document.getElementById("cancelButton");


async function loadTechnicians() {

    try {

        const response = await apiFetch(
            `${API_URL}/technicians`
        );

        const technicians =
            await response.json();

        if (!response.ok) {

            throw new Error(
                technicians.detail ||
                "Unable to load technicians"
            );
        }

        technicianTable.innerHTML = "";


        technicians.forEach(function(technician) {

            const row =
                document.createElement("tr");


            const idCell =
                document.createElement("td");

            idCell.textContent =
                technician.technician_id;


            const nameCell =
                document.createElement("td");

            nameCell.textContent =
                technician.technician_name;


            const phoneCell =
                document.createElement("td");

            phoneCell.textContent =
                technician.phone;


            const specializationCell =
                document.createElement("td");

            specializationCell.textContent =
                technician.specialization || "";


            // Vehicle Category
            const vehicleTypeCell =
                document.createElement("td");

            vehicleTypeCell.textContent =
                technician.vehicle_type || "All";


            const experienceCell =
                document.createElement("td");

            experienceCell.textContent =
                technician.experience ?? "";


            const actionCell =
                document.createElement("td");


            const editButton =
                document.createElement("button");

            editButton.textContent = "Edit";

            editButton.addEventListener(
                "click",
                function() {

                    editTechnician(technician);

                }
            );


            const deleteButton =
                document.createElement("button");

            deleteButton.textContent = "Delete";

            deleteButton.addEventListener(
                "click",
                function() {

                    deleteTechnician(
                        technician.technician_id
                    );

                }
            );


            actionCell.appendChild(editButton);

            actionCell.appendChild(
                document.createTextNode(" ")
            );

            actionCell.appendChild(deleteButton);


            row.appendChild(idCell);
            row.appendChild(nameCell);
            row.appendChild(phoneCell);
            row.appendChild(specializationCell);
            row.appendChild(vehicleTypeCell);
            row.appendChild(experienceCell);
            row.appendChild(actionCell);


            technicianTable.appendChild(row);

        });

    }
    catch (error) {

        message.textContent =
            error.message;

    }
}


technicianForm.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();


        const technicianData = {

            technician_name:
                document.getElementById(
                    "technician_name"
                ).value,

            phone:
                document.getElementById(
                    "phone"
                ).value,

            specialization:
                document.getElementById(
                    "specialization"
                ).value || null,

            // Vehicle Category
            vehicle_type:
                document.getElementById(
                    "vehicle_type"
                ).value,

            experience:
                document.getElementById(
                    "experience"
                ).value
                ? Number(
                    document.getElementById(
                        "experience"
                    ).value
                )
                : null
        };


        try {

            let response;


            if (technicianId.value) {

                response = await apiFetch(
                    `${API_URL}/technicians/${technicianId.value}`,
                    {
                        method: "PUT",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                technicianData
                            )
                    }
                );

            }
            else {

                response = await apiFetch(
                    `${API_URL}/technicians`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                technicianData
                            )
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

            technicianForm.reset();

            technicianId.value = "";

            cancelButton.hidden = true;

            await loadTechnicians();

        }
        catch (error) {

            message.textContent =
                error.message;

        }

    }
);


function editTechnician(technician) {

    technicianId.value =
        technician.technician_id;

    document.getElementById(
        "technician_name"
    ).value =
        technician.technician_name;

    document.getElementById(
        "phone"
    ).value =
        technician.phone;

    document.getElementById(
        "specialization"
    ).value =
        technician.specialization || "";

    // Vehicle Category
    document.getElementById(
        "vehicle_type"
    ).value =
        technician.vehicle_type || "All";

    document.getElementById(
        "experience"
    ).value =
        technician.experience ?? "";

    cancelButton.hidden = false;

}


cancelButton.addEventListener(
    "click",
    function() {

        technicianForm.reset();

        technicianId.value = "";

        cancelButton.hidden = true;

        message.textContent = "";

    }
);


async function deleteTechnician(technicianId) {

    try {

        const response =
            await apiFetch(
                `${API_URL}/technicians/${technicianId}`,
                {
                    method: "DELETE"
                }
            );


        const result =
            await response.json();


        if (!response.ok) {

            throw new Error(
                result.detail ||
                "Unable to delete technician"
            );
        }


        message.textContent =
            result.message;

        await loadTechnicians();

    }
    catch (error) {

        message.textContent =
            error.message;

    }
}


loadTechnicians();