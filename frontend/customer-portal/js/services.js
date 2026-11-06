
const API_URL = window.API_BASE_URL;

const servicesList = document.getElementById("servicesList");
const servicesStatus = document.getElementById("servicesStatus");
const serviceSearch = document.getElementById("serviceSearch");

let serviceRecords = [];


function formatPrice(price) {

    const amount = Number(price);

    if (!Number.isFinite(amount)) {
        return "Price unavailable";
    }

    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}


function renderServices(records) {

    servicesList.replaceChildren();

    if (records.length === 0) {

        const emptyMessage = document.createElement("div");

        emptyMessage.className = "service-empty-state";

        const heading = document.createElement("h3");

        heading.textContent = serviceRecords.length === 0
            ? "No services listed yet"
            : "No matching services";

        const description = document.createElement("p");

        description.textContent = serviceRecords.length === 0
            ? "Available services will appear here when the service center adds them."
            : "Try another service name or search term.";

        emptyMessage.appendChild(heading);
        emptyMessage.appendChild(description);

        servicesList.appendChild(emptyMessage);

        return;
    }


    records.forEach(function(service, index) {

        const card = document.createElement("article");

        card.className = "service-item";


        const cardTop = document.createElement("div");

        cardTop.className = "service-item-top";


        const number = document.createElement("span");

        number.className = "service-number";

        number.textContent =
            String(index + 1).padStart(2, "0");


        const label = document.createElement("span");

        label.className = "service-available";

        label.textContent = "Available";


        cardTop.appendChild(number);
        cardTop.appendChild(label);


        const name = document.createElement("h3");

        name.textContent = service.service_name;


        const description = document.createElement("p");

        description.className = "service-description";

        description.textContent =
            service.description ||
            "Contact the service center for further details.";


        const divider = document.createElement("div");

        divider.className = "service-item-divider";


        const priceRow = document.createElement("div");

        priceRow.className = "service-price-row";


        const priceLabel = document.createElement("span");

        priceLabel.textContent = "Service price";


        const price = document.createElement("strong");

        price.textContent = formatPrice(service.price);


        priceRow.appendChild(priceLabel);
        priceRow.appendChild(price);


        card.appendChild(cardTop);
        card.appendChild(name);
        card.appendChild(description);
        card.appendChild(divider);
        card.appendChild(priceRow);


        servicesList.appendChild(card);

    });
}


function filterServices() {

    const searchText =
        serviceSearch.value.trim().toLowerCase();

    const filteredServices = serviceRecords.filter(
        function(service) {

            const name =
                String(service.service_name || "").toLowerCase();

            const description =
                String(service.description || "").toLowerCase();

            return name.includes(searchText) ||
                description.includes(searchText);
        }
    );

    renderServices(filteredServices);
}


async function loadServices() {

    servicesStatus.textContent =
        "Loading available services...";

    try {

        const response = await fetch(
            `${API_URL}/public/services`
        );

        if (!response.ok) {

            throw new Error(
                `Unable to load services (HTTP ${response.status}).`
            );
        }

        const result = await response.json();

        if (!Array.isArray(result)) {

            throw new Error(
                "The service API returned an unexpected response."
            );
        }

        serviceRecords = result;

        servicesStatus.textContent =
            `${serviceRecords.length} service(s) available`;

        filterServices();

    } catch (error) {

        console.error("Service catalog error:", error);

        servicesStatus.textContent =
            "We couldn't load the service catalog.";

        servicesList.replaceChildren();

        const errorBox = document.createElement("div");

        errorBox.className = "service-empty-state";

        const errorText = document.createElement("p");

        errorText.textContent =
            "Check that the FastAPI server is running and try again.";

        const retryButton = document.createElement("button");

        retryButton.type = "button";

        retryButton.className = "button button-gold";

        retryButton.textContent = "Retry";

        retryButton.addEventListener(
            "click",
            loadServices
        );

        errorBox.appendChild(errorText);
        errorBox.appendChild(retryButton);

        servicesList.appendChild(errorBox);

    }
}


serviceSearch.addEventListener(
    "input",
    filterServices
);


loadServices();
