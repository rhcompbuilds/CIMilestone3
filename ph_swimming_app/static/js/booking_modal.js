/*document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('bookingModal');
  const modalActivityName = document.getElementById('modal-activity-name');
  const modalActivityDescription = document.getElementById('modal-activity-description');
  const activityIdInput = document.getElementById('activity-id-input');
  const closeBtn = document.querySelector('.close-btn');

  document.querySelectorAll('.activity-card').forEach(card => {
    card.addEventListener('click', function() {
      const activityId = this.getAttribute('data-activity-id');
      const activityName = this.getAttribute('data-activity-name');
      const activityDescription = this.getAttribute('data-activity-description');
      
      modalActivityName.textContent = activityName;
      modalActivityDescription.textContent = activityDescription;
      activityIdInput.value = activityId;
      
      modal.style.display = 'block';
    });
  });

  closeBtn.addEventListener('click', function() {
    modal.style.display = 'none';
  });

  window.addEventListener('click', function(event) {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });
});*/

document.addEventListener('DOMContentLoaded', function() {
    const sessionModal = document.getElementById('sessionModal');
    const sessionList = document.getElementById('session-list');
    const closeBtn = document.querySelector('.close-btn');

    document.querySelectorAll('.activity-card').forEach(card => {
        card.addEventListener('click', function() {
            const activityId = this.getAttribute('data-activity-id');
            const url = `/bookings/api/sessions/${activityId}/`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    sessionList.innerHTML = ''; // Clear previous sessions
                    const sessions = JSON.parse(data.sessions);
                    if (sessions.length > 0) {
                        sessions.forEach(session => {
                            const sessionData = session.fields;
                            const listItem = document.createElement('li');
                            listItem.innerHTML = `
                                <strong>${sessionData.session_day}</strong> at ${sessionData.start_time} - 
                                <a href="/bookings/make/?session=${session.pk}">Book Now</a>
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
                });
        });
    });

    closeBtn.addEventListener('click', function() {
        sessionModal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === sessionModal) {
            sessionModal.style.display = 'none';
        }
    });
});