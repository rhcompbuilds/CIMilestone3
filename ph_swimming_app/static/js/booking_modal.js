document.addEventListener('DOMContentLoaded', function() {
    const activityCards = document.querySelectorAll('.activity-card');
    const sessionModal = document.getElementById('sessionModal');
    const sessionList = document.getElementById('session-list');
    const closeBtn = document.querySelector('.close-btn');

    if (sessionModal && closeBtn) {
        closeBtn.addEventListener('click', function() {
            sessionModal.style.display = 'none';
        });

        window.addEventListener('click', function(event) {
            if (event.target === sessionModal) {
                sessionModal.style.display = 'none';
            }
        });
    }

    if (activityCards.length > 0) {
        activityCards.forEach(card => {
            card.addEventListener('click', function() {
                const activityId = this.getAttribute('data-activity-id');
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
                        
                        // This is the corrected line. It directly accesses the sessions array.
                        const sessions = data.sessions; 
                        
                        if (sessions && sessions.length > 0) {
                            sessions.forEach(session => {
                                const listItem = document.createElement('li');
                                
                                let bookingLinkHtml = '';
                                if (session.is_full) {
                                    bookingLinkHtml = '<span style="color: red; font-weight: bold;">Fully Booked</span>';
                                } else {
                                    bookingLinkHtml = `<a href="/bookings/make/?session=${session.pk}">Book Now (${session.available_places} spaces left)</a>`;
                                }

                                listItem.innerHTML = `
                                    <strong>${session.session_day}</strong> at ${session.start_time} - ${bookingLinkHtml}
                                `;
                                sessionList.appendChild(listItem);
                            });
                        } else {
                            sessionList.innerHTML = '<li>No sessions available for this activity.</li>';
                        }
                        sessionModal.style.display = 'block';
                    })
                    .catch(error => {
                        console.error('Error fetching sessions:', error);
                        sessionList.innerHTML = '<li>An error occurred. Please try again later.</li>';
                        sessionModal.style.display = 'block';
                    });
            });
        });
    }
});