document.addEventListener('DOMContentLoaded', function() {
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
});
