const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message =
      data?.detail?.message ||
      (typeof data?.detail === 'string' ? data.detail : null) ||
      'Erro ao processar requisição na API.';
    throw new Error(message);
  }
  return data;
}

export const api = {
  getHealth: () => request('/health'),
  getExercises: () => request('/exercises'),
  getProfiles: () => request('/profiles'),
  getProfile: (profileId) => request(`/profiles/${profileId}`),
  createProfile: (payload) =>
    request('/profiles', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateProfile: (profileId, payload) =>
    request(`/profiles/${profileId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  deleteProfile: (profileId) =>
    request(`/profiles/${profileId}`, {
      method: 'DELETE',
    }),
  generateFullWorkout: (profileId, excludedExerciseIds) =>
    request(`/profiles/${profileId}/workouts/generate-full`, {
      method: 'POST',
      body: JSON.stringify({ excluded_exercise_ids: excludedExerciseIds }),
    }),
  regenerateWorkoutDay: (profileId, dayNumber, excludedExerciseIds) =>
    request(`/profiles/${profileId}/workouts/days/${dayNumber}/regenerate`, {
      method: 'POST',
      body: JSON.stringify({ excluded_exercise_ids: excludedExerciseIds }),
    }),
};
