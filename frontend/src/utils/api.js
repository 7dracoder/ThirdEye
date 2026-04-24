const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  // ── Person ──
  async createPerson(formData) {
    const res = await fetch(`${API_URL}/api/person`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error(`Failed to create person: ${res.statusText}`);
    return res.json();
  },

  async getPerson(id) {
    const res = await fetch(`${API_URL}/api/person/${id}`);
    if (!res.ok) throw new Error(`Person not found`);
    return res.json();
  },

  async addPhoto(personId, file) {
    const formData = new FormData();
    formData.append('photo', file);
    const res = await fetch(`${API_URL}/api/person/${personId}/photo`, { method: 'POST', body: formData });
    return res.json();
  },

  // ── Matches ──
  async getMatches(personId, limit = 50, offset = 0) {
    const res = await fetch(`${API_URL}/api/person/${personId}/matches?limit=${limit}&offset=${offset}`);
    return res.json();
  },

  // ── Timeline ──
  async getTimeline(personId) {
    const res = await fetch(`${API_URL}/api/person/${personId}/timeline`);
    return res.json();
  },

  // ── Map ──
  async getMapData(personId) {
    const res = await fetch(`${API_URL}/api/person/${personId}/map`);
    return res.json();
  },

  // ── Stats ──
  async getStats(personId) {
    const res = await fetch(`${API_URL}/api/person/${personId}/stats`);
    return res.json();
  },

  // ── Crowdsource ──
  async submitSighting(personId, formData) {
    const res = await fetch(`${API_URL}/api/sighting/${personId}`, { method: 'POST', body: formData });
    return res.json();
  },

  async getShareInfo(token) {
    const res = await fetch(`${API_URL}/api/share/${token}`);
    return res.json();
  },

  // ── Scan ──
  async triggerScan(personId) {
    const res = await fetch(`${API_URL}/api/person/${personId}/scan`, { method: 'POST' });
    return res.json();
  },

  // ── Health ──
  async health() {
    const res = await fetch(`${API_URL}/api/health`);
    return res.json();
  },
};

export const WS_URL = API_URL.replace('http', 'ws');
export { API_URL };
