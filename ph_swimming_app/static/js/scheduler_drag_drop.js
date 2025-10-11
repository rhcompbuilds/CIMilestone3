document.addEventListener('DOMContentLoaded', () => {
    // 🌟 UPDATED: Read configuration from the data-config element 🌟
    const config = document.getElementById('data-config');
    if (!config) {
        console.error("Configuration element #data-config not found. Check scheduler.html for data-config div.");
        // Define fallback values to allow the rest of the script to run
        var IS_SUPERUSER = false;
        var IS_STAFF = false;
        var times = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'];
    } else {
        // Parse the stored data attributes, converting string 'true'/'false' to booleans
        var IS_SUPERUSER = config.dataset.isSuperuser === 'true'; 
        var IS_STAFF = config.dataset.isStaff === 'true'; 
        var times = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'];
    }
    
    
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const timetableGrid = document.getElementById('timetable-grid');
    const activityContainer = document.getElementById('activity-container');
    const messageContainer = document.getElementById('message-container');
    const staffCanEdit = IS_SUPERUSER || IS_STAFF; 

    let draggedItem = null;

    // --- CSRF Token Helper Function ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // --- showMessage: Implemented for visual feedback ---
    function showMessage(message, className) {
        if (messageContainer) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `alert ${className}`;
            msgDiv.textContent = message;
            messageContainer.innerHTML = ''; // Clear previous messages
            messageContainer.appendChild(msgDiv);
            
            // Auto-hide the message after 3 seconds
            setTimeout(() => {
                msgDiv.remove();
            }, 3000);
        } else {
            console.log(`Message (${className}): ${message}`);
        }
    }

   // --- Fetch Activities ---
const fetchActivities = async () => {
    try {
        const response = await fetch('/api/activities/'); 
        const activities = await response.json();
        
        console.log("Activities loaded:", activities);

        if (!Array.isArray(activities)) {
            console.error('API did not return a list of activities:', activities);
            activityContainer.innerHTML = 'Failed to load activities: Server returned an unexpected response format.';
            return; // Exit the function if the data is invalid
        }
        
        activities.forEach(activity => {
            const activityItem = document.createElement('div');
            activityItem.className = 'activity-item';
            activityItem.setAttribute('draggable', true);
            activityItem.setAttribute('data-activity-id', activity.id);
            activityItem.setAttribute('data-activity-name', activity.activity_name);
            activityItem.setAttribute('data-duration-hours', activity.duration || 1); 
            activityItem.textContent = activity.activity_name;
            
            // Add color class for coloring in CSS
            activityItem.classList.add(`activity-${activity.id}`); 
            
            activityContainer.appendChild(activityItem);
        });
        
    } catch (error) {
        // This catch block handles network errors or JSON parsing errors.
        console.error('Failed to fetch activities:', error);
        activityContainer.innerHTML = 'Failed to load activities.';
    }
};
    
    // --- Helper to create a session card ---
    const createSessionCard = (activityId, activityName, duration, sessionId = null) => {
        const sessionCard = document.createElement('div');
        sessionCard.className = 'session-card';
        sessionCard.textContent = activityName;
        sessionCard.draggable = true;
        sessionCard.classList.add(`activity-${activityId}`); 
        sessionCard.dataset.activityId = activityId;
        sessionCard.dataset.durationHours = duration;
        if (sessionId) sessionCard.dataset.sessionId = sessionId; 
        
        return sessionCard;
    }

    // --- Helper to visually occupy slots ---
    const occupySlots = (day, startTime, duration) => {
        const timeIndex = times.indexOf(startTime);
        for (let i = timeIndex; i < timeIndex + duration; i++) {
            const nextSlot = document.querySelector(`.time-slot[data-day="${day}"][data-time="${times[i]}"]`);
            if (nextSlot) {
                nextSlot.classList.add('occupied');
                if (i > timeIndex) {
                    nextSlot.classList.add('continuation-slot'); 
                }
            }
        }
    }
    
    // --- unoccupySlots ---
    const unoccupySlots = (startSlot) => {
        const day = startSlot.dataset.day;
        const startTime = startSlot.dataset.time;
        // Find the session card within the slot to get the duration
        const sessionCard = startSlot.querySelector('.session-card');
        // Use the correct attribute name for duration
        const duration = parseInt(sessionCard?.dataset.durationHours || 1); 

        const timeIndex = times.indexOf(startTime);
        
        for (let i = timeIndex; i < timeIndex + duration; i++) {
            const nextSlot = document.querySelector(`.time-slot[data-day="${day}"][data-time="${times[i]}"]`);
            if (nextSlot) {
                nextSlot.classList.remove('occupied', 'continuation-slot');
                if (i === timeIndex) { // Only clear the card from the starting slot
                    nextSlot.innerHTML = ''; 
                }
            }
        }
    };

    // --- Build Timetable Grid ---
    const buildTimetable = () => {
        times.forEach(time => {
            const timeHeader = document.createElement('div');
            timeHeader.className = 'timetable-header';
            timeHeader.textContent = time;
            timetableGrid.appendChild(timeHeader);

            days.forEach(day => {
                const slot = document.createElement('div');
                slot.className = 'time-slot';
                slot.setAttribute('data-day', day);
                slot.setAttribute('data-time', time);
                
                setupSlotListeners(slot);
                timetableGrid.appendChild(slot);
            });
        });
    };

    // --- Helper to convert "HH:MM:SS" duration string to number of 1-hour slots ---
function getSlotsNeeded(durationString) {
    if (!durationString) return 1;
    
    const cleanedDuration = durationString.split(' ')[0]; 
    const parts = cleanedDuration.split(':');
    
    if (parts.length < 2) return 1; 

    const hours = parseInt(parts[0], 10) || 0;
    const minutes = parseInt(parts[1], 10) || 0;
    const totalHours = hours + (minutes / 60); 
    
    return Math.ceil(totalHours); 
}

    // --- Fetch Existing Sessions ---
    const fetchExistingSessions = async () => {
    try {
        const response = await fetch('/api/schedule/list/'); 
        const sessions = await response.json();

        sessions.forEach(session => {
            
            if (session.activity) { 
                const day = session.session_day;
                const rawTime = session.start_time;
                const time = rawTime.substring(0, 5);
                const slot = document.querySelector(`.time-slot[data-day="${day}"][data-time="${time}"]`);
                
                if (slot) {
                    const durationString = session.activity_duration;
                    const duration = getSlotsNeeded(durationString);
                    const activityId = session.activity;
                    
                    const sessionCard = createSessionCard(
                        activityId,
                        session.activity_name, 
                        duration,
                        session.id
                    );
                    
                    slot.appendChild(sessionCard);
                    occupySlots(day, time, duration);
                }
            }
        });
    } catch (error) {
        console.error('Failed to fetch existing sessions:', error);
    }
    }
    
    // --- Event Listeners ---
    const setupSlotListeners = (slot) => {
        slot.addEventListener('dragover', (e) => {
            const isActivityDrag = draggedItem && draggedItem.classList.contains('activity-item');
            const isLocked = slot.classList.contains('locked-slot');
            
            if (!staffCanEdit) return;

            if (isActivityDrag && isLocked && !IS_SUPERUSER) {
                return; 
            }
            
            e.preventDefault();
            slot.classList.add('drag-over');
        });

        slot.addEventListener('dragleave', () => slot.classList.remove('drag-over'));

        slot.addEventListener('drop', (e) => {
            e.preventDefault();
            slot.classList.remove('drag-over');

            if (!draggedItem || !staffCanEdit) return;

            if (draggedItem.classList.contains('activity-item')) {
                handleActivityDrop(slot);
            } else if (draggedItem.classList.contains('session-card')) {
                handleSessionMove(draggedItem, slot);
            }
        });
    };
    
    document.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('activity-item') || e.target.classList.contains('session-card')) {
            draggedItem = e.target;
            e.dataTransfer.effectAllowed = 'move';
            e.target.classList.add('dragging');
            
            if (e.target.classList.contains('session-card')) {
                if (e.target.parentNode.classList.contains('locked-slot') && !IS_SUPERUSER) {
                    e.dataTransfer.effectAllowed = 'none';
                    draggedItem = null;
                    showMessage("Only superusers can move sessions from the lunch slot.", "error-message");
                    return;
                }
                e.dataTransfer.setData('text/plain', e.target.dataset.sessionId);
                setTimeout(() => e.target.style.display = 'none', 0);
            }
        }
    });
    
    document.addEventListener('dragend', (e) => {
        if (draggedItem) {
            draggedItem.classList.remove('dragging');
            draggedItem.style.display = ''; 
            draggedItem = null;
        }
    });

    // --- Logic to handle dropping a new activity ---
    const handleActivityDrop = (slot) => {
        const activityId = draggedItem.dataset.activityId;
        const activityName = draggedItem.dataset.activityName;
        const duration = parseInt(draggedItem.dataset.durationHours || 1); 
        const day = slot.dataset.day;
        const time = slot.dataset.time;
        const timeIndex = times.indexOf(time);
        const endIndex = timeIndex + duration;
        
        // 1. Check for timetable fit and locked slots/conflicts
        if (endIndex > times.length) {
            showMessage("Activity doesn't fit remaining slots.", "error-message");
            return;
        }
        for (let i = timeIndex; i < endIndex; i++) {
            const nextSlot = document.querySelector(`.time-slot[data-day="${day}"][data-time="${times[i]}"]`);
            if (nextSlot.classList.contains('locked-slot') && !IS_SUPERUSER) {
                showMessage("Cannot schedule in the locked lunch slot.", "error-message");
                return;
            }
            if (nextSlot.querySelector('.session-card')) {
                showMessage("Slot already occupied. Clear it first.", "error-message");
                return;
            }
        }

        // 2. Apply visual changes
        occupySlots(day, time, duration);

        // 3. Create the session card and save
        const sessionCard = createSessionCard(activityId, activityName, duration);
        slot.appendChild(sessionCard);
        saveSession(day, time, activityId, activityName, duration, sessionCard);
    };
    
    // --- 3. handleSessionMove: Implemented for moving/deleting sessions ---
    const handleSessionMove = (sessionCard, newSlot) => {
        const sessionId = sessionCard.dataset.sessionId;
        const duration = parseInt(sessionCard.dataset.durationHours || 1);
        const oldSlot = sessionCard.parentNode;
        
        if (!sessionId) {
            showMessage("Error: Session ID missing for move operation.", "error-message");
            sessionCard.style.display = '';
            return;
        }
        
        if (oldSlot === newSlot) {
            sessionCard.style.display = ''; 
            return;
        }

        // --- UN-SCHEDULE/DELETE ---
        if (newSlot.id === 'activity-container' || newSlot.classList.contains('activity-item')) {
            if (confirm("Are you sure you want to unschedule this activity?")) {
                deleteSession(sessionId);
                unoccupySlots(oldSlot);
                sessionCard.remove();
            } else {
                sessionCard.style.display = ''; // Restore visibility if cancelled
            }
            return;
        }

        // --- MOVE SESSION ---
        if (newSlot.classList.contains('time-slot') && !newSlot.querySelector('.session-card')) {
            
            const newDay = newSlot.dataset.day;
            const newTime = newSlot.dataset.time;
            const timeIndex = times.indexOf(newTime);
            const endIndex = timeIndex + duration;

            // Check new target slots for conflicts/locks
            if (endIndex > times.length) {
                showMessage("Activity doesn't fit new slots.", "error-message");
                sessionCard.style.display = '';
                return;
            }
            for (let i = timeIndex; i < endIndex; i++) {
                const nextSlot = document.querySelector(`.time-slot[data-day="${newDay}"][data-time="${times[i]}"]`);
                if (nextSlot.classList.contains('locked-slot') && !IS_SUPERUSER) {
                    showMessage("Cannot move into the locked lunch slot.", "error-message");
                    sessionCard.style.display = '';
                    return;
                }
                if (nextSlot.querySelector('.session-card')) {
                    showMessage("New slot already occupied.", "error-message");
                    sessionCard.style.display = '';
                    return;
                }
            }

            // Perform the move visually
            unoccupySlots(oldSlot);
            newSlot.appendChild(sessionCard);
            sessionCard.style.display = ''; 
            occupySlots(newDay, newTime, duration);

            // Update the database
            updateSession(sessionId, newDay, newTime); 

        } else {
            sessionCard.style.display = ''; // Restore visibility if drop was invalid
            showMessage("Invalid drop location.", "error-message");
        }
    };

    // --- API Call to Save Session (Create) ---
    const saveSession = async (day, time, activityId, activityName, duration, sessionCard) => {
        try {
            const response = await fetch('/api/schedule/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'), 
                },
                body: JSON.stringify({
                    activity: activityId,
                    session_day: day,      
                    start_time: time,      
                }),
            });

            if (response.ok) {
                const data = await response.json();
                showMessage('Session created successfully!', 'success-message');
                sessionCard.dataset.sessionId = data.id || data.session_id; 
                sessionCard.textContent = activityName; // Set name for visibility
                occupySlots(day, time, duration);

            } else {
                const errorData = await response.json();
                const errorMessage = errorData.non_field_errors 
                    ? errorData.non_field_errors.join(' ') 
                    : (errorData.message || 'Failed to create session. Reverting.');

                console.error('Failed to create session:', errorData);
                showMessage(errorMessage, 'error-message');
                
                // Revert visual change on save failure
                unoccupySlots(sessionCard.parentNode);
                sessionCard.remove();
            }
        } catch (error) {
            console.error('Network error while saving session:', error);
            showMessage('Network error while saving session. Reverting.', 'error-message');
            // Revert visual change on network failure
            unoccupySlots(sessionCard.parentNode);
            sessionCard.remove();
        }
    };
    
    // --- 5. API Call to Delete Session (Unschedule) ---
    const deleteSession = async (sessionId) => {
        try {
            const response = await fetch(`/api/schedule/delete/${sessionId}/`, { 
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
            });
            if (response.ok) {
                showMessage('Session unscheduled successfully!', 'success-message');
            } else {
                const errorData = await response.json();
                console.error('Failed to delete session:', errorData);
                showMessage(errorData.message || 'Error deleting session. Reload the page.', 'error-message');
            }
        } catch (error) {
            console.error('Network error while deleting session:', error);
            showMessage('Network error while deleting session. Reload the page.', 'error-message');
        }
    };

    // --- 4. API Call to Update Session (Move) ---
    const updateSession = async (sessionId, newDay, newTime) => {
        try {
            const response = await fetch(`/api/schedule/update/${sessionId}/`, { 
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    session_day: newDay,
                    start_time: newTime,
                }),
            });
            
            if (response.ok) {
                showMessage('Session moved successfully!', 'success-message');
            } else {
                const errorData = await response.json();
                console.error('Failed to update session:', errorData);
                showMessage(errorData.message || 'Error moving session. Reload the page.', 'error-message');
            }
        } catch (error) {
            console.error('Network error while updating session:', error);
            showMessage('Network error while moving session. Reload the page.', 'error-message');
        }
    };


    // --- Initialise the page ---
    buildTimetable();
    fetchActivities();
    fetchExistingSessions(); // Load existing data after building the grid
});