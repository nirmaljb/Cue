const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * API service for communicating with the REMIND-AR backend
 */

/**
 * Recognize a face from multiple base64 images
 * @param {string[]} imagesBase64 - Array of base64 encoded images
 */
export async function recognizeFace(imagesBase64) {
  const response = await fetch(`${API_URL}/recognize-face`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ images_base64: imagesBase64 }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Face recognition failed');
  }

  return response.json();
}

/**
 * Get HUD context for a person
 */
export async function getHUDContext(personId, status) {
  const response = await fetch(`${API_URL}/hud-context`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ person_id: personId, status }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get HUD context');
  }

  return response.json();
}

/**
 * Save a memory from audio recording
 */
export async function saveMemory(personId, audioBase64) {
  const response = await fetch(`${API_URL}/memory/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ person_id: personId, audio_base64: audioBase64 }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to save memory');
  }

  return response.json();
}

/**
 * Get pending people awaiting caregiver confirmation
 */
export async function getPendingPeople() {
  const response = await fetch(`${API_URL}/caregiver/pending`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get pending people');
  }

  return response.json();
}

/**
 * Confirm a person's identity
 */
export async function confirmPerson(personId, name, relation) {
  const response = await fetch(`${API_URL}/caregiver/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ person_id: personId, name, relation }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to confirm person');
  }

  return response.json();
}

/**
 * Delete a person
 */
export async function deletePerson(personId) {
  const response = await fetch(`${API_URL}/caregiver/person/${personId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete person');
  }

  return response.json();
}

/**
 * Health check
 */
export async function healthCheck() {
  const response = await fetch(`${API_URL}/health`);
  return response.json();
}

/**
 * Enroll a new person (pre-enrollment by caregiver)
 */
export async function enrollPerson(name, relation, contextualNote, imageBase64) {
  const response = await fetch(`${API_URL}/caregiver/enroll`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      relation,
      contextual_note: contextualNote,
      image_base64: imageBase64
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to enroll person');
  }

  return response.json();
}

/**
 * Get confirmed people in the system
 */
export async function getConfirmedPeople() {
  const response = await fetch(`${API_URL}/caregiver/confirmed`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get confirmed people');
  }

  return response.json();
}

/**
 * Update a person's details
 */
export async function updatePerson(personId, name, relation, contextualNote, imageBase64 = null) {
  const body = {
    person_id: personId,
    name,
    relation,
    contextual_note: contextualNote,
  };

  if (imageBase64) {
    body.image_base64 = imageBase64;
  }

  const response = await fetch(`${API_URL}/caregiver/person/${personId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update person');
  }

  return response.json();
}
