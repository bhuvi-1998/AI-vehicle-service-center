window.API_BASE_URL = "http://127.0.0.1:8000";

// Protect admin pages from access without an admin login.
(function protectAdminPages() {

    const path = window.location.pathname.toLowerCase();
    const currentPage = path.split("/").pop();

    // Only apply this guard to pages inside /pages/.
    if (!path.includes("/pages/")) {
        return;
    }

    // Keep login and first-admin setup pages publicly accessible.
    if (
        currentPage === "login.html" ||
        currentPage === "admin-setup.html"
    ) {
        return;
    }

    const token = localStorage.getItem("access_token");
    const role = localStorage.getItem("admin_role");

    if (!token || role !== "admin") {
        window.location.replace("login.html");
    }

})();


async function apiFetch(url, options = {}) {

    const headers = new Headers(options.headers || {});
    const token = localStorage.getItem("access_token");

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (response.status === 401) {

        localStorage.removeItem("access_token");

        if (
            !window.location.pathname.endsWith("/login.html") &&
            !window.location.pathname.endsWith("/admin-setup.html")
        ) {
            window.location.href = "login.html";
        }
    }

    return response;
}


async function downloadProtectedPdf(url, filename) {

    const response = await apiFetch(url);

    if (!response.ok) {

        let detail = "Unable to download PDF.";

        try {
            const result = await response.json();
            detail = result.detail || detail;
        } catch {
            // Keep the default error message.
        }

        throw new Error(detail);
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(objectUrl);
}