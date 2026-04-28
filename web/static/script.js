document.addEventListener("DOMContentLoaded", () => {

    const params = new URLSearchParams(window.location.search);
    const title = params.get("uploaded");

    if (title) {
        const container = document.getElementById("flash-container");
        if (container) {
            const li = document.createElement("li");
            li.className = "flash success";

            li.innerHTML = `Document uploaded: ${title}`;

            container.appendChild(li);
        }
    }

    const buttons = document.querySelectorAll(".details-btn");

    buttons.forEach(btn => {
        btn.addEventListener("click", () => {

            const title = btn.dataset.title;

            const details = document.getElementById("doc-details");
            const titleField = document.getElementById("doc-title");

            details.style.display = "block";

            renderTitle(title, "doc-title")
        });

    });

    const sharedButtons = document.querySelectorAll(".shared-details-btn");

    sharedButtons.forEach(btn => {

        btn.addEventListener("click", () => {

            const title = btn.dataset.title;

            const details = document.getElementById("shared-doc-details");
            const titleField = document.getElementById("shared-doc-title");

            details.style.display = "block";

            renderTitle(title, "shared-doc-title")
        });
    });

    function renderTitle(title, elementId) {
        const el = document.getElementById(elementId);
        updateField(el, title);
    }

    function updateField(element, value) {
        element.innerHTML = "Title: " + value;
    }

});