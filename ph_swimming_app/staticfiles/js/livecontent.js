document.addEventListener('DOMContentLoaded', () => {
    // --- Day navigation ---
    const dayPages = document.querySelectorAll('.day-page');
    let currentIndex = 0;

    function showDay(index) {
        dayPages.forEach((page, i) => {
            page.style.display = i === index ? 'block' : 'none';
        });
    }

    document.querySelectorAll('.prevBtn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentIndex > 0) {
                currentIndex--;
                showDay(currentIndex);
            }
        });
    });

    document.querySelectorAll('.nextBtn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentIndex < dayPages.length - 1) {
                currentIndex++;
                showDay(currentIndex);
            }
        });
    });

    // Ensure the initial day is shown only after the DOM is ready
    if (dayPages.length > 0) {
        showDay(currentIndex);
    }

    // --- Modal handling ---
    const modal = document.getElementById('activityModal');
    const closeModal = document.getElementById('closeModal');
    const assignBtn = document.getElementById('assignActivityBtn');
    const modalDay = document.getElementById('modalDay');
    const modalTime = document.getElementById('modalTime');
    const activitySelect = document.getElementById('activitySelect');

    // Add event listeners ONLY if the modal elements exist
    if (modal && closeModal && assignBtn) {
        closeModal.addEventListener('click', () => {
            modal.style.display = 'none';
        });

        window.addEventListener('click', (e) => {
            if (e.target === modal) modal.style.display = 'none';
        });

        document.querySelectorAll('.add-activity-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                modal.style.display = 'block';
                modalDay.value = btn.dataset.day;
                modalTime.value = btn.dataset.time;
            });
        });
        
        // --- Assign activity via AJAX and UI update ---
        assignBtn.addEventListener('click', () => {
            const day = modalDay.value;
            const time = modalTime.value;
            const activityId = activitySelect.value;
            const activityName = activitySelect.selectedOptions[0].text;

            if (!activityId) {
                showMessage("Please select an activity.", "alert-danger");
                return;
            }

            fetch('/add_session/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `session_day=${day}&start_time=${time}&activity=${activityId}`
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Update the UI
                    const table = document.querySelector(`.timetable[data-day="${day}"]`);
                    const cell = table.querySelector(`td[data-time="${time}"]`);
                    const btn = cell.nextElementSibling.querySelector(".add-activity-btn");
                    const row = cell.closest("tr");

                    if (cell) cell.textContent = activityName;
                    if (activityName.toLowerCase() === "lunch") {
                        row.classList.add("lunch-row");
                        if (btn) btn.remove();
                    } else if (btn) {
                        btn.style.display = 'none';
                    }

                    modal.style.display = 'none';
                    showMessage("Activity assigned successfully!", "alert-success");
                } else {
                    showMessage(data.message, "alert-danger");
                }
            })
            .catch(err => {
                console.error('AJAX error:', err);
                showMessage('An error occurred.', "alert-danger");
            });
        });
    }
});

// --- CSRF helper function ---
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Custom message display function to avoid alert()
function showMessage(message, className) {
    const messageContainer = document.getElementById('message-container');
    if (messageContainer) {
        messageContainer.innerHTML = `<div class="alert ${className}">${message}</div>`;
        setTimeout(() => {
            messageContainer.innerHTML = '';
        }, 3000);
    } else {
        console.warn('Message container not found. Message:', message);
    }
}
