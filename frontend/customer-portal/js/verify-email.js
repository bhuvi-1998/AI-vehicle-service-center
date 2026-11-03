
const VERIFY_API_URL = "http://127.0.0.1:8000";

async function verifyEmailFromLink() {
    const message = document.getElementById("verificationMessage");
    const action = document.getElementById("verificationAction");

    // The email link uses a URL fragment, which is not sent in the
    // browser's HTTP request to the frontend server.
    const token = new URLSearchParams(
        window.location.hash.slice(1)
    ).get("token");

    // Remove the token from the visible URL after reading it.
    history.replaceState(null, document.title, window.location.pathname);

    if (!token) {
        message.textContent = "The verification link is missing or invalid.";
        message.dataset.state = "error";
        action.innerHTML = '<a href="login.html">Return to login</a>';
        return;
    }

    try {
        const response = await fetch(`${VERIFY_API_URL}/customer-auth/verify-email`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Email verification failed.");
        }

        message.textContent = result.message;
        message.dataset.state = "success";
        action.innerHTML = '<a href="login.html">Continue to Customer Login</a>';

    } catch (error) {
        message.textContent = error.message || "Unable to contact the server.";
        message.dataset.state = "error";
        action.innerHTML = '<a href="login.html">Return to login</a>';
    }
}

verifyEmailFromLink();
