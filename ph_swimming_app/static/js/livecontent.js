document.addEventListener('DOMContentLoaded', () => {
    // --- Day navigation ---
    const dayPages = document.querySelectorAll('.day-page');
    let currentIndex = 0;

    function showDay(index) {
        dayPages.forEach((page, i) => {
            page.style.display = i === index ? 'block' : 'none';
        });
    }

    document.getElementById('prevBtn').addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            showDay(currentIndex);
        }
    });

    document.getElementById('nextBtn').addEventListener('click', () => {
        if (currentIndex < dayPages.length - 1) {
            currentIndex++;
            showDay(currentIndex);
        }
    });

    showDay(currentIndex);

    // --- Modal handling ---
    const modal = document.getElementById('activityModal');
    const closeModal = document.getElementById('closeModal');
    const assignBtn = document.getElementById('assignActivityBtn');
    const modalDay = document.getElementById('modalDay');
    const modalTime = document.getElementById('modalTime');
    const activitySelect = document.getElementById('activitySelect');

    document.querySelectorAll('.add-activity-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            modal.style.display = 'block';
            modalDay.value = btn.dataset.day;
            modalTime.value = btn.dataset.time;
        });
    });

    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });

    // --- Assign activity via AJAX ---
    assignBtn.addEventListener('click', () => {
        const day = modalDay.value;
        const time = modalTime.value;
        const activityId = activitySelect.value;

        if (!activityId) {
            alert('Please select an activity.');
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
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the table cell
                const table = document.querySelector(`.timetable[data-day="${day}"]`);
                const cell = table.querySelector(`td[data-time="${time}"]`);
                if (cell) cell.textContent = activitySelect.selectedOptions[0].text;
                modal.style.display = 'none';
            } else {
                alert(data.message);
            }
        })
        .catch(err => {
            console.error('AJAX error:', err);
            alert('An error occurred.');
        });
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
});
