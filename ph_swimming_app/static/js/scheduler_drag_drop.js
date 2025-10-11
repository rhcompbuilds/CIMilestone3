document.addEventListener('DOMContentLoaded', () => {
    // --- Configuration Constants ---
    const SLOT_HEIGHT_PX = 62; 
    const DAY_CODE_TO_ABBR = {
        "1": "Mon", "2": "Tue", "3": "Wed", "4": "Thu",
        "5": "Fri", "6": "Sat", "7": "Sun",
    };
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const times = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'];
    
    /* INITIAL CONFIG */
    const config = document.getElementById('data-config');
    let IS_SUPERUSER = false;
    let IS_STAFF = false;
    
    if (config) {
        IS_SUPERUSER = config.dataset.isSuperuser === 'true'; 
        IS_STAFF = config.dataset.isStaff === 'true'; 
    } else {
        console.error("Configuration element #data-config not found. Check scheduler.html.");
    }

    /* DOM ELEMENTS */
    const timetableGrid = document.getElementById('timetable-grid');
    const activityContainer = document.getElementById('activity-container');
    const messageContainer = document.getElementById('message-container');
    const staffCanEdit = IS_SUPERUSER || IS_STAFF; 

    let draggedItem = null;

    /*--------------------------------*/
    /* HELPER FUNCTIONS
    /*--------------------------------*/

    /* CSRF TOKEN */
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

    /* MESSAGE DISPLAY */
    function showMessage(message, className) {
        if (messageContainer) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `alert ${className}`;
            msgDiv.textContent = message;
            messageContainer.innerHTML = ''; 
            messageContainer.appendChild(msgDiv);
            
            setTimeout(() => {
                msgDiv.remove();
            }, 3000);
        } else {
            console.log(`Message (${className}): ${message}`);
        }
    }

    /* DURATION CONVERSION */
    function getSlotsNeeded(durationString) {
        if (!durationString) return 1;
        
        const parts = durationString.split(':');
        
        if (parts.length < 2) return 1; 

        const hours = parseInt(parts[0], 10) || 0;
        const minutes = parseInt(parts[1], 10) || 0;
        const totalHours = hours + (minutes / 60); 
        
        // Duration is rounded to the nearest slot (hour)
        return Math.ceil(totalHours); 
    }
    
    /* SESSION CARDS */
    const createSessionCard = (activityId, activityName, duration, sessionId = null) => {
        const sessionCard = document.createElement('div');
        sessionCard.className = 'session-card';
        sessionCard.textContent = activityName;
        sessionCard.draggable = true;
        sessionCard.classList.add(`activity-${activityId}`); 
        sessionCard.dataset.activityId = activityId;
        sessionCard.dataset.durationHours = duration;
        if (sessionId) sessionCard.dataset.sessionId = sessionId; 
        
        const cardHeight = duration * SLOT_HEIGHT_PX;
        sessionCard.style.height = `${cardHeight}px`;
        
        return sessionCard;
    }
    
    /* ADD ACTIVITIES TO SLOTS */
    const occupySlots = (day, startTime, duration) => {
        const timeIndex = times.indexOf(startTime);
        for (let i = timeIndex; i < timeIndex + duration; i++) {
            const nextSlot = document.querySelector(`.time-slot[data-day="${day}"][data-time="${times[i]}"]`);
            if (nextSlot) {
                nextSlot.classList.add('occupied');
                if (i > timeIndex) {
                    nextSlot.classList.add('continuation-slot'); 
                    // CRITICAL: Ensure continuation slots are empty for correct rendering
                    // This prevents shorter sessions from trying to fill a slot already covered
                    // by a taller session's card.
                    if (nextSlot.children.length === 0) {
                        nextSlot.innerHTML = ''; 
                    }
                }
            }
        }
    }
    
    /* REMOVE ACTIVITIES FROM SLOTS */
    const unoccupySlots = (startSlot) => {
        const day = startSlot.dataset.day;
        const startTime = startSlot.dataset.time;
        const sessionCard = startSlot.querySelector('.session-card');
        const duration = parseInt(sessionCard?.dataset.durationHours || 1); 

        const timeIndex = times.indexOf(startTime);
        
        for (let i = timeIndex; i < timeIndex + duration; i++) {
            const nextSlot = document.querySelector(`.time-slot[data-day="${day}"][data-time="${times[i]}"]`);
            if (nextSlot) {
                nextSlot.classList.remove('occupied', 'continuation-slot');
                if (i === timeIndex) {
                    nextSlot.innerHTML = ''; 
                }
            }
        }
    };
    
    /*--------------------------------*/
    /* API's & CORE FUNCTION
    /*--------------------------------*/
    
    /* ACTIVITIES LIST FOR DRAG FUNTIONALITY */
    const fetchActivities = async () => {
        try {
            const response = await fetch('/api/activities/'); 
            const activities = await response.json();
            
            if (!Array.isArray(activities)) {
                activityContainer.innerHTML = 'Failed to load activities: unexpected format.';
                return;
            }
            
            activities.forEach(activity => {
                const activityItem = document.createElement('div');
                activityItem.className = 'activity-item';
                activityItem.setAttribute('draggable', true);
                activityItem.dataset.activityId = activity.id;
                activityItem.dataset.activityName = activity.activity_name;
                activityItem.dataset.durationHours = activity.duration || 1; 
                activityItem.textContent = activity.activity_name;
                activityItem.classList.add(`activity-${activity.id}`); 
                activityContainer.appendChild(activityItem);
            });
            
        } catch (error) {
            console.error('Failed to fetch activities:', error);
            activityContainer.innerHTML = 'Failed to load activities.';
        }
    };

    /* LOAD EXISTING SESSIONS (UPDATED FOR LUNCH LOCKING) */
    const fetchExistingSessions = async () => {
        try {
            const response = await fetch('/api/schedule/list/'); 
            const sessions = await response.json();

            sessions.forEach(session => {
                
                if (session.activity) { 
                    const rawDayCode = session.session_day;
                    const dayAbbr = DAY_CODE_TO_ABBR[rawDayCode] || rawDayCode; 
                    const rawTime = session.start_time;
                    // Time format fix: Strip seconds for DOM lookup
                    const time = rawTime.substring(0, 5); 
                    
                    const slot = document.querySelector(`.time-slot[data-day="${dayAbbr}"][data-time="${time}"]`);
                    
                    if (slot) {
                        const durationString = session.activity_duration;
                        const duration = getSlotsNeeded(durationString);
                        const activityId = session.activity;
                        const activityName = session.activity_name; // Get name for locking check

                        // CRITICAL FIX: Prevent overlap/double drawing for multi-hour sessions
                        if (slot.querySelector('.session-card')) {
                             // Slot is already occupied by a card (from an earlier, longer session). 
                             occupySlots(dayAbbr, time, duration);
                             return; 
                        }
                        
                        // Apply the locked-slot class based on the loaded session data (Lunch)
                        if (activityName.toLowerCase() === 'lunch' && duration === 1 && !IS_SUPERUSER) {
                            slot.classList.add('locked-slot');
                        }
                        
                        const sessionCard = createSessionCard(
                            activityId,
                            activityName, 
                            duration,
                            session.id
                        );
                        
                        slot.appendChild(sessionCard);
                        occupySlots(dayAbbr, time, duration);
                    }
                }
            });
        } catch (error) {
            console.error('Failed to fetch existing sessions:', error);
        }
    }

    /* SAVE A NEW SESSION (CREATE) */
    const saveSession = async (dayAbbr, time, activityId, activityName, duration, sessionCard) => {
        
        const sessionDayValue = dayAbbr;
        const apiTimeValue = time.length === 5 ? `${time}:00` : time;

        if (!sessionDayValue) {
            showMessage('Error: Could not determine day value for API.', 'error-message');
            unoccupySlots(sessionCard.parentNode);
            sessionCard.remove();
            return false;
        }

        try {
            const response = await fetch('/api/schedule/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'), 
                },
                body: JSON.stringify({
                    activity: activityId,
                    session_day: sessionDayValue, 
                    start_time: apiTimeValue,      
                }),
            });

            if (response.ok) {
                const data = await response.json();
                showMessage('Session created successfully!', 'success-message');
                sessionCard.dataset.sessionId = data.id || data.session_id; 
                return true; 
            } else {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.non_field_errors 
                    ? errorData.non_field_errors.join(' ') 
                    : (errorData.message || 'Failed to create session. Reverting.');

                console.error('Failed to create session:', errorData);
                showMessage(errorMessage, 'error-message');
                
                // Revert visual change on save failure
                unoccupySlots(sessionCard.parentNode);
                sessionCard.remove();
                return false; 
            }
        } catch (error) {
            console.error('Network error while saving session:', error);
            showMessage('Network error while saving session. Reverting.', 'error-message');
            unoccupySlots(sessionCard.parentNode);
            sessionCard.remove();
            return false; 
        }
    };

    /* DELETE SESSION */
    const deleteSession = async (sessionId) => {
        try {
            const response = await fetch(`/api/schedule/${sessionId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
            });
            if (response.ok) {
                showMessage('Session unscheduled successfully!', 'success-message');
                return true; // SUCCESS signal
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error('Failed to delete session:', errorData);
                showMessage(errorData.message || 'Error deleting session. Reload the page.', 'error-message');
                return false; // FAILURE signal
            }
        } catch (error) {
            console.error('Network error while deleting session:', error);
            showMessage('Network error while deleting session. Reload the page.', 'error-message');
            return false; // FAILURE signal
        }
    };

    /* (updateSession removed as it's no longer used for moving) */
    
    /* DRAG & DROP HANDLING */

    const setupSlotListeners = (slot) => {
        slot.addEventListener('dragover', (e) => {
            const isActivityDrag = draggedItem && draggedItem.classList.contains('activity-item');
            const isLocked = slot.classList.contains('locked-slot');
            
            if (!staffCanEdit) return;

            // Only superusers can drag anything over or into a locked slot
            if (isLocked && !IS_SUPERUSER) {
                e.dataTransfer.effectAllowed = 'none';
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
            
            const isLocked = slot.classList.contains('locked-slot');
            if (isLocked && !IS_SUPERUSER) {
                showMessage("Locked slot. Only superusers can modify it.", "error-message");
                return;
            }

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
                    showMessage("Only superusers can move sessions from the locked slot.", "error-message");
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

    const handleActivityDrop = (slot) => {
        const activityId = draggedItem.dataset.activityId;
        const activityName = draggedItem.dataset.activityName;
        const duration = parseInt(draggedItem.dataset.durationHours || 1); 
        const day = slot.dataset.day;
        const time = slot.dataset.time;
        const timeIndex = times.indexOf(time);
        const endIndex = timeIndex + duration;
        
        if (endIndex > times.length) {
            showMessage("Activity doesn't fit remaining slots.", "error-message");
            return;
        }
        for (let i = timeIndex; i < endIndex; i++) {
            const nextSlot = document.querySelector(`.time-slot[data-day="${day}"][data-time="${times[i]}"]`);
            if (nextSlot.classList.contains('locked-slot') && !IS_SUPERUSER) {
                showMessage("Cannot schedule in the locked slot.", "error-message");
                return;
            }
            if (nextSlot.querySelector('.session-card') || nextSlot.classList.contains('occupied')) {
                showMessage("Slot already occupied. Clear it first.", "error-message");
                return;
            }
        }
        
        const sessionCard = createSessionCard(activityId, activityName, duration);
        slot.appendChild(sessionCard);
        occupySlots(day, time, duration);
        saveSession(day, time, activityId, activityName, duration, sessionCard);
    };
    
    /* Reinstated DELETE + CREATE for robust moving */
    const handleSessionMove = (sessionCard, newSlot) => {
        const sessionId = sessionCard.dataset.sessionId;
        const duration = parseInt(sessionCard.dataset.durationHours || 1);
        const activityId = sessionCard.dataset.activityId;
        const activityName = sessionCard.textContent;
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

        /* UN-SCHEDULE/DELETE (DRAG TO ACTIVITY CONTAINER) */
        if (newSlot.id === 'activity-container' || newSlot.classList.contains('activity-item')) {
            if (confirm("Are you sure you want to unschedule this activity?")) {
                deleteSession(sessionId);
                unoccupySlots(oldSlot);
                sessionCard.remove();
            } else {
                sessionCard.style.display = ''; 
            }
            return;
        }

        /* MOVE SESSION (DELETE old, CREATE new) */
        if (newSlot.classList.contains('time-slot') && !newSlot.querySelector('.session-card')) {
            
            const oldDay = oldSlot.dataset.day; 
            const oldTime = oldSlot.dataset.time; 
            
            const newDay = newSlot.dataset.day;
            const newTime = newSlot.dataset.time;
            const timeIndex = times.indexOf(newTime);
            const endIndex = timeIndex + duration;

            if (endIndex > times.length) {
                showMessage("Activity doesn't fit new slots.", "error-message");
                sessionCard.style.display = '';
                return;
            }
            // Collision/Lock Check
            for (let i = timeIndex; i < endIndex; i++) {
                const nextSlot = document.querySelector(`.time-slot[data-day="${newDay}"][data-time="${times[i]}"]`);
                if (nextSlot === oldSlot) continue; 
                
                if (nextSlot.classList.contains('locked-slot') && !IS_SUPERUSER) {
                    showMessage("Cannot move into the locked slot.", "error-message");
                    sessionCard.style.display = '';
                    return;
                }
                // Check if target slot (and continuation slots) is occupied by another session
                if (nextSlot.querySelector('.session-card') || (nextSlot.classList.contains('occupied') && nextSlot !== oldSlot)) {
                    showMessage("New slot already occupied.", "error-message");
                    sessionCard.style.display = '';
                    return;
                }
            }

            // Stage 1: Visual Move & cleanup
            unoccupySlots(oldSlot);
            newSlot.appendChild(sessionCard);
            sessionCard.style.display = ''; 
            occupySlots(newDay, newTime, duration);
            
            // Stage 2: API Move (DELETE old, CREATE new)
            deleteSession(sessionId)
                .then(deleteSuccess => {
                    if (deleteSuccess) {
                        // Create new record at the new location
                        return saveSession(newDay, newTime, activityId, activityName, duration, sessionCard);
                    } else {
                        // If DELETE failed, rollback visually and stop
                        throw new Error('Previous DELETE failed. Rollback initiated.');
                    }
                })
                .then(createSuccess => {
                    if (!createSuccess) {
                        // If CREATE failed, rollback visually
                        throw new Error('New CREATE failed. Rollback initiated.');
                    }
                })
                .catch(error => {
                    console.error('Move transaction failed:', error);
                    // Rollback visual changes
                    unoccupySlots(newSlot);
                    oldSlot.appendChild(sessionCard);
                    occupySlots(oldDay, oldTime, duration);
                    showMessage('Move failed! Reverting visual changes.', 'error-message');
                });
        } else {
            sessionCard.style.display = ''; 
            showMessage("Invalid drop location.", "error-message");
        }
    };
    
    /* BUILD TIMETABLE (UNCHANGED) */
    const buildTimetable = () => {
        times.forEach(time => {
            const timeHeader = document.createElement('div');
            timeHeader.className = 'timetable-header time-label';
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

    // --- Initialise the page ---
    buildTimetable();
    fetchActivities();
    fetchExistingSessions();
});