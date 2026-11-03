
const API_BASE_URL = "http://127.0.0.1:8000";


// CUSTOMER REGISTRATION
const registerForm = document.getElementById("registerForm");

if (registerForm) {
    registerForm.addEventListener("submit", async event => {
        event.preventDefault();

        const message = document.getElementById("registerMessage");
        const button = registerForm.querySelector('button[type="submit"]');

        button.disabled = true;
        message.textContent = "Creating your account and sending the verification email...";
        message.dataset.state = "";

        const customer = {
            customer_name: document.getElementById("customerName").value.trim(),
            phone: document.getElementById("customerPhone").value.trim(),
            email: document.getElementById("customerEmail").value.trim().toLowerCase(),
            password: document.getElementById("customerPassword").value,
            address: document.getElementById("customerAddress").value.trim() || null
        };

        try {
            const response = await fetch(`${API_BASE_URL}/customer-auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(customer)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Registration failed.");
            }

            message.textContent =
                "Registration successful! Check your email and click Verify My Email before logging in.";
            message.dataset.state = "success";
            registerForm.reset();

        } catch (error) {
            message.textContent = error.message || "Could not connect to the server.";
            message.dataset.state = "error";
        } finally {
            button.disabled = false;
        }
    });
}


// CUSTOMER LOGIN
const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async event => {
        event.preventDefault();

        const message = document.getElementById("loginMessage");
        const button = loginForm.querySelector('button[type="submit"]');

        button.disabled = true;
        message.textContent = "Logging in...";
        message.dataset.state = "";

        const credentials = {
            email: document.getElementById("loginEmail").value.trim().toLowerCase(),
            password: document.getElementById("loginPassword").value
        };

        try {
            const response = await fetch(`${API_BASE_URL}/customer-auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(credentials)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Login failed.");
            }

            localStorage.setItem("customer_access_token", result.access_token);
            window.location.href = "dashboard.html";

        } catch (error) {
            message.textContent = error.message || "Could not connect to the server.";
            message.dataset.state = "error";
        } finally {
            button.disabled = false;
        }
    });
}


// RESEND VERIFICATION EMAIL
const resendForm = document.getElementById("resendVerificationForm");

if (resendForm) {
    resendForm.addEventListener("submit", async event => {
        event.preventDefault();

        const message = document.getElementById("resendMessage");
        const button = resendForm.querySelector('button[type="submit"]');
        const email = document.getElementById("resendEmail").value.trim().toLowerCase();

        button.disabled = true;
        message.textContent = "Requesting a new verification email...";
        message.dataset.state = "";

        try {
            const response = await fetch(
                `${API_BASE_URL}/customer-auth/resend-verification`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email })
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "Unable to resend the email.");
            }

            message.textContent = result.message;
            message.dataset.state = "success";

        } catch (error) {
            message.textContent = error.message || "Could not connect to the server.";
            message.dataset.state = "error";
        } finally {
            button.disabled = false;
        }
    });
}
