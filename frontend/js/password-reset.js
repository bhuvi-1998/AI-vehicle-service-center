const PASSWORD_RESET_API = window.API_BASE_URL;

(() => {
    const accountType = document.body.dataset.accountType;

    const requestPanel = document.getElementById("requestResetPanel");
    const requestForm = document.getElementById("requestResetForm");
    const requestMessage = document.getElementById("requestResetMessage");
    const requestButton = document.getElementById("requestResetButton");

    const resetPanel = document.getElementById("completeResetPanel");
    const resetForm = document.getElementById("completeResetForm");
    const resetMessage = document.getElementById("resetMessage");
    const resetButton = document.getElementById("resetPasswordButton");
    const resetLoginLink = document.getElementById("resetLoginLink");

    // Email links carry the token in the URL fragment.
    let resetToken = new URLSearchParams(
        window.location.hash.slice(1)
    ).get("token");

    // Remove the token from the visible address bar.
    if (resetToken) {
        requestPanel.hidden = true;
        resetPanel.hidden = false;

        history.replaceState(
            null,
            document.title,
            window.location.pathname + window.location.search
        );
    } else {
        requestPanel.hidden = false;
        resetPanel.hidden = true;
    }

    function showMessage(element, text, isError = false) {
        element.textContent = text;
        element.dataset.state = isError ? "error" : "success";
    }

    // Request a password reset email.
    requestForm.addEventListener("submit", async event => {
        event.preventDefault();

        requestButton.disabled = true;
        requestButton.textContent = "Sending...";
        requestMessage.textContent = "";
        requestMessage.dataset.state = "";

        const email = document
            .getElementById("resetEmail")
            .value.trim()
            .toLowerCase();

        try {
            const response = await fetch(
                `${PASSWORD_RESET_API}/password-reset/request`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email,
                        account_type: accountType
                    })
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.detail || "Unable to process the request."
                );
            }

            showMessage(
                requestMessage,
                result.message ||
                "If an eligible account exists, a reset link will be sent."
            );

            requestForm.reset();

        } catch (error) {
            showMessage(
                requestMessage,
                error instanceof TypeError
                    ? "Unable to connect to the server. Check that FastAPI is running."
                    : error.message,
                true
            );
        } finally {
            requestButton.disabled = false;
            requestButton.textContent = "Send Reset Link";
        }
    });

    // Set a new password using the single-use token.
    resetForm.addEventListener("submit", async event => {
        event.preventDefault();

        const newPassword =
            document.getElementById("newPassword").value;

        const confirmPassword =
            document.getElementById("confirmPassword").value;

        if (!resetToken) {
            showMessage(
                resetMessage,
                "The reset link is missing. Request a new link.",
                true
            );
            return;
        }

        if (newPassword !== confirmPassword) {
            showMessage(
                resetMessage,
                "The passwords do not match.",
                true
            );
            return;
        }

        resetButton.disabled = true;
        resetButton.textContent = "Updating...";
        resetMessage.textContent = "";
        resetMessage.dataset.state = "";

        try {
            const response = await fetch(
                `${PASSWORD_RESET_API}/password-reset/complete`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        token: resetToken,
                        new_password: newPassword
                    })
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.detail || "Unable to reset the password."
                );
            }

            resetToken = null;
            resetForm.hidden = true;

            showMessage(
                resetMessage,
                result.message ||
                "Password changed successfully. You can now log in."
            );

            resetLoginLink.hidden = false;

        } catch (error) {
            showMessage(
                resetMessage,
                error instanceof TypeError
                    ? "Unable to connect to the server. Check that FastAPI is running."
                    : error.message,
                true
            );
        } finally {
            resetButton.disabled = false;
            resetButton.textContent = "Set New Password";
        }
    });
})();