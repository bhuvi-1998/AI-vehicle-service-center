/*
 * Shared backend API configuration.
 * Local development uses localhost.
 * Set the real Render URL before production deployment.
 */
(() => {
    const hostname = window.location.hostname;

    const isLocalDevelopment =
        hostname === "localhost" ||
        hostname === "127.0.0.1";

    const LOCAL_API_URL = "http://127.0.0.1:8000";

    const PRODUCTION_API_URL =
        "https://YOUR-RENDER-BACKEND.onrender.com";

    window.API_BASE_URL = isLocalDevelopment
        ? LOCAL_API_URL
        : PRODUCTION_API_URL;

    if (PRODUCTION_API_URL.includes("YOUR-RENDER-BACKEND")) {
        console.warn(
            "Set the real Render backend URL in frontend/js/config.js."
        );
    }
})();
