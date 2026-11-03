const CUSTOMER_API_URL = "http://127.0.0.1:8000";

function getCustomerToken() {
    return localStorage.getItem("customer_access_token");
}

function clearCustomerSession() {
    localStorage.removeItem("customer_access_token");
}

function showProfileEditMessage(text, isError = false) {
    const message = document.getElementById("profileEditMessage");

    message.textContent = text;
    message.style.color = isError ? "#FF9A9A" : "#86E3A1";
}

function displayCustomerProfile(customer) {
    document.getElementById("customerName").textContent =
        customer.customer_name || "Customer";

    document.getElementById("profileId").textContent =
        customer.customer_id ?? "—";

    document.getElementById("profileName").textContent =
        customer.customer_name || "Not provided";

    document.getElementById("profileEmail").textContent =
        customer.email || "Not provided";

    document.getElementById("profilePhone").textContent =
        customer.phone || "Not provided";

    document.getElementById("profileAddress").textContent =
        customer.address || "Not provided";

    // Populate the edit form with saved profile data.
    document.getElementById("editCustomerName").value =
        customer.customer_name || "";

    document.getElementById("editCustomerEmail").value =
        customer.email || "";

    document.getElementById("editCustomerPhone").value =
        customer.phone || "";

    document.getElementById("editCustomerAddress").value =
        customer.address || "";
}


async function customerRequest(path, options = {}) {
    const token = getCustomerToken();

    if (!token) {
        window.location.replace("login.html");
        throw new Error("Please log in to continue.");
    }

    const headers = {
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`
    };

    const response = await fetch(
        `${CUSTOMER_API_URL}${path}`,
        {
            ...options,
            headers
        }
    );

    const result = await response.json().catch(() => ({}));

    if (response.status === 401 || response.status === 403) {
        clearCustomerSession();
        window.location.replace("login.html");

        throw new Error(
            result.detail || "Your session is no longer valid. Please log in again."
        );
    }

    if (!response.ok) {
        throw new Error(
            result.detail || "The request failed."
        );
    }

    return result;
}


async function loadCustomerDashboard() {
    const message = document.getElementById("dashboardMessage");

    if (!getCustomerToken()) {
        window.location.replace("login.html");
        return;
    }

    try {
        const customer = await customerRequest("/customer-auth/me");

        displayCustomerProfile(customer);

        message.textContent = "Your profile loaded successfully.";

    } catch (error) {
        message.textContent =
            error.message || "Could not connect to the backend.";
    }
}


// Open and close the edit profile form.
const toggleProfileButton =
    document.getElementById("toggleCustomerProfile");

const profilePanel =
    document.getElementById("customerProfilePanel");

toggleProfileButton.addEventListener("click", () => {
    profilePanel.hidden = !profilePanel.hidden;

    const isOpen = !profilePanel.hidden;

    toggleProfileButton.textContent = isOpen
        ? "Close Profile Editor"
        : "Edit Profile";

    toggleProfileButton.setAttribute(
        "aria-expanded",
        String(isOpen)
    );

    if (isOpen) {
        profilePanel.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }
});


// Save the edited customer profile.
document.getElementById("customerProfileForm").addEventListener(
    "submit",
    async event => {
        event.preventDefault();

        const saveButton =
            document.getElementById("saveCustomerProfile");

        saveButton.disabled = true;
        saveButton.textContent = "Saving...";

        showProfileEditMessage("");

        const password =
            document.getElementById("editCustomerPassword").value;

        const profileData = {
            customer_name: document
                .getElementById("editCustomerName")
                .value.trim(),

            email: document
                .getElementById("editCustomerEmail")
                .value.trim(),

            phone: document
                .getElementById("editCustomerPhone")
                .value.trim(),

            address: document
                .getElementById("editCustomerAddress")
                .value.trim() || null,

            password: password || null
        };

        try {
            const result = await customerRequest(
                "/customer-auth/me",
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(profileData)
                }
            );

            document.getElementById(
                "editCustomerPassword"
            ).value = "";

            // Changing the email requires verification again.
            if (result.email_verification_required) {
                window.alert(
                    result.message ||
                    "Your email was changed. Please verify your new email address."
                );

                clearCustomerSession();
                window.location.replace("login.html");
                return;
            }

            displayCustomerProfile(result);

            showProfileEditMessage(
                result.message || "Customer profile updated successfully."
            );

        } catch (error) {
            showProfileEditMessage(error.message, true);

        } finally {
            saveButton.disabled = false;
            saveButton.textContent = "Save Profile";
        }
    }
);


// Log out the customer.
document.getElementById("logoutButton").addEventListener("click", () => {
    clearCustomerSession();
    window.location.replace("login.html");
});

loadCustomerDashboard();