document.addEventListener('DOMContentLoaded', function() {
    const activityCards = document.querySelectorAll('.activity-card');
    const sessionModal = document.getElementById('sessionModal');
    const sessionList = document.getElementById('session-list');
    const closeBtn = document.querySelector('.close-btn');

    // This block of code will only run if the modal elements exist on the page.
    if (sessionModal && sessionList && closeBtn) {
        // Function to close modal
        function closeModal() {
            sessionModal.style.display = 'none';
        }

        // Set up modal close events
        closeBtn.addEventListener('click', closeModal);
        window.addEventListener('click', function(event) {
            if (event.target === sessionModal) {
                closeModal();
            }
        });

        // Function to fetch sessions and display modal
        function fetchAndDisplaySessions(activityId) {
            const url = `/bookings/api/sessions/${activityId}/`;
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
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
                    sessionModal.style.display = 'block';
                })
                .catch(error => {
                    console.error('Error fetching sessions:', error);
                    if (sessionList) {
                        sessionList.innerHTML = '<li>An error occurred. Please try again later.</li>';
                    }
                    if (sessionModal) {
                        sessionModal.style.display = 'block';
                    }
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
    }

    // Now, add the new logic for handling form submissions on the session_bookings.html page
    const bookingForms = document.querySelectorAll('.booking-form');
    if (bookingForms.length > 0) {
        bookingForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault(); // Prevent the default form submission

                const formData = new FormData(form);
                const bookingId = formData.get('booking_id');
                const action = formData.get('action');

                fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    const messageContainer = document.getElementById('message-container');
                    if (messageContainer) {
                         messageContainer.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                         setTimeout(() => {
                             messageContainer.innerHTML = '';
                         }, 3000);
                    }
                    // Remove the row from the table
                    const rowToRemove = document.getElementById(`booking-row-${bookingId}`);
                    if (rowToRemove) {
                        rowToRemove.remove();
                    }
                })
                .catch(error => {
                    console.error('Error submitting form:', error);
                    const messageContainer = document.getElementById('message-container');
                    if (messageContainer) {
                         messageContainer.innerHTML = `<div class="alert alert-danger">An error occurred: ${error.message}</div>`;
                    }
                });
            });
        });
    }
});
