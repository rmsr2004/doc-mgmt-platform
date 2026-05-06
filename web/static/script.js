document.addEventListener("DOMContentLoaded", () => {

    // Dismiss flash notifications when the close button is clicked
    const flashContainer = document.getElementById("flash-container");
    if (flashContainer) {
        flashContainer.addEventListener("click", (e) => {
            const btn = e.target.closest(".flash-close");
            if (btn) {
                const flash = btn.parentElement;
                flash.style.transition = "opacity 0.3s, transform 0.3s";
                flash.style.opacity = "0";
                flash.style.transform = "translateX(20px)";
                flash.addEventListener("transitionend", () => flash.remove(), { once: true });
            }
        });
    }

    const params = new URLSearchParams(window.location.search);
    const title = params.get("uploaded");

    if (title) {
        const container = document.getElementById("flash-container");
        if (container) {
            const li = document.createElement("li");
            li.className = "flash success";

            li.innerHTML = `Document uploaded: ${title}<button class="flash-close" aria-label="Dismiss notification">&times;</button>`;

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

            renderTitle(title)
        });

    });
    
    function renderTitle(title) {
        const el = document.getElementById("doc-title");
        updateField(el, title);
    }

    function updateField(element, value) {
        element.innerHTML = "Title: " + value;
    }

});