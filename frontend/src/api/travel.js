/**
 * API communication module for TourAlly travel planner
 */

/**
 * Initiates a new trip request or adds feedback to an ongoing travel planning thread.
 * 
 * @param {string} message User message describing destination, budget, days, etc.
 * @param {string|null} threadId Optional existing thread/session ID
 * @returns {Promise<Object>} API response with itinerary, threadId, blocked status, etc.
 */
export async function startTrip(message, threadId = null) {
  const payload = { message };
  if (threadId) {
    payload.thread_id = threadId;
  }

  const response = await fetch('/api/travel', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to start trip planning session');
  }

  return response.json();
}

/**
 * Resumes a travel plan session after a human-in-the-loop pause.
 * 
 * @param {string} threadId Session identifier
 * @param {boolean} approved Set to true to finalise the itinerary, false to request changes
 * @param {string} feedback Optional textual revision notes
 * @returns {Promise<Object>} API response containing the next itinerary draft or completion status
 */
export async function approveTrip(threadId, approved, feedback = "") {
  const payload = {
    thread_id: threadId,
    approved,
    feedback
  };

  const response = await fetch('/api/travel/approve', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to send approval selection');
  }

  return response.json();
}

/**
 * Validates backend health status and checks for active API integrations.
 * 
 * @returns {Promise<Object>} health status summary object
 */
export async function checkHealth() {
  const response = await fetch('/api/health');
  if (!response.ok) {
    throw new Error('Backend health check returned an error status');
  }
  return response.json();
}
