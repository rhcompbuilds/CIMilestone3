document.addEventListener('DOMContentLoaded', function() {
    // Modal-related elements
    const activityCards = document.querySelectorAll('.activity-card');
    const sessionModal = document.getElementById('sessionModal');
    const sessionList = document.getElementById('session-list');
    const closeBtn = document.querySelector('.close-btn');

    // Function to close modal
    function closeModal() {
        if (sessionModal) {
            sessionModal.style.display = 'none';
        }
    }

    // Set up modal close events
    if (sessionModal && closeBtn) {
        closeBtn.addEventListener('click', closeModal);
        window.addEventListener('click', function(event) {
            if (event.target === sessionModal) {
                closeModal();
            }
        });
    }

    // Function to fetch sessions and display modal
    function fetchAndDisplaySessions(activityId) {
        const url = `/bookings/api/sessions/${activityId}/`;
        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                sessionList.innerHTML = '';
                const sessions = data.sessions;
                if (sessions && sessions.length > 0) {
                    sessions.forEach(session => {
                        const listItem = document.createElement('li');

                        // Check if the session is fully booked
                        if (session.is_full) {
                            listItem.classList.add('fully-booked-item');
                            listItem.innerHTML = `
                                <strong>${session.session_day}</strong> at ${session.start_time} -
                                <span class="fully-booked">Fully Booked</span>
                            `;
                        } else {
                            // Display the link and remaining places for available sessions
                            listItem.innerHTML = `
                                <strong>${session.session_day}</strong> at ${session.start_time} -
                                <a href="/bookings/make/?session=${session.pk}">
                                    Book Now (${session.available_places} spaces left)
                                </a>
                            `;
                        }

                        sessionList.appendChild(listItem);
                    });
                } else {
                    sessionList.innerHTML = '<li>No sessions available for this activity.</li>';
                }
                if (sessionModal) sessionModal.style.display = 'block';
            })
            .catch(error => {
                console.error('Error fetching sessions:', error);
                sessionList.innerHTML = '<li>An error occurred. Please try again later.</li>';
                if (sessionModal) sessionModal.style.display = 'block';
            });
    }

    if (activityCards.length > 0) {
        activityCards.forEach(card => {
            card.addEventListener('click', function() {
                const activityId = this.getAttribute('data-activity-id');
                fetchAndDisplaySessions(activityId);
            });
        });
    }

    // --- New Logic for session_bookings.html ---
    const forms = document.querySelectorAll('.booking-action-form');
    const messageContainer = document.getElementById('message-container');

    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent the default form submission

            const formData = new FormData(form);
            const action = formData.get('action');
            const bookingId = formData.get('booking_id');

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                const row = document.getElementById(`booking-${bookingId}`);
                if (data.status === 'success') {
                    // Display the success message
                    const alertHtml = `<div class="alert alert-success alert-dismissible fade show" role="alert">${data.message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
                    messageContainer.innerHTML = alertHtml;
                    
                    // Handle the change on the front-end without a page reload
                    if (action === 'release') {
                        row.remove(); // Remove the row from the table
                    } else if (action === 'attend') {
                        const attendedCell = document.querySelector(`.attended-status-${bookingId}`);
                        if (attendedCell) {
                            attendedCell.textContent = 'Yes';
                        }
                    }
                } else {
                    const alertHtml = `<div class="alert alert-danger alert-dismissible fade show" role="alert">${data.message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
                    messageContainer.innerHTML = alertHtml;
                }
            })
            .catch(error => {
                const alertHtml = `<div class="alert alert-danger alert-dismissible fade show" role="alert">An error occurred: ${error.message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
                messageContainer.innerHTML = alertHtml;
                console.error('Fetch error:', error);
            });
        });
    });
});
