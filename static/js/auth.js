const formEl = document.getElementById("auth-form");
const errorEl = document.getElementById("auth-error");

formEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorEl.hidden = true;

    const formData = new FormData(formEl);
    const payload = Object.fromEntries(formData.entries());
    if (payload.display_name === "") delete payload.display_name;

    const button = formEl.querySelector("button");
    button.disabled = true;
    try {
        await apiFetch(AUTH_ENDPOINT, { method: "POST", body: JSON.stringify(payload) });
        window.location.href = AUTH_REDIRECT;
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.hidden = false;
        button.disabled = false;
    }
});
