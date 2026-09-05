const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export function getToken() {
  return localStorage.getItem('token');
}

export function setToken(token) {
  localStorage.setItem('token', token);
}

export function clearToken() {
  localStorage.removeItem('token');
}

async function apiRequest(method, path, body = null, isFormData = false) {
  const headers = {};
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const options = {
    method,
    headers,
  };

  if (body) {
    if (isFormData) {
      options.body = body;
    } else {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
  }

  const response = await fetch(`${BASE_URL}${path}`, options);
  if (!response.ok) {
    let errorDetail = 'Request failed';
    try {
      const err = await response.json();
      errorDetail = err.detail || err.message || errorDetail;
    } catch {
      // Ignored
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const CIVIC_ZONES = [
  { id: 'central', name: 'Central Zone (Connaught Place)', lat: 28.6139, lng: 77.2090, postal_code: '110001' },
  { id: 'south', name: 'South Zone (Hauz Khas / Saket)', lat: 28.5494, lng: 77.2001, postal_code: '110016' },
  { id: 'north', name: 'North Zone (Civil Lines)', lat: 28.6812, lng: 77.2228, postal_code: '110054' },
  { id: 'east', name: 'East Zone (Mayur Vihar)', lat: 28.6083, lng: 77.2958, postal_code: '110091' },
  { id: 'west', name: 'West Zone (Rajouri Garden)', lat: 28.6415, lng: 77.1209, postal_code: '110027' },
];

// Auth endpoints
export async function login(mock_id_number, otp = '123456') {
  const data = await apiRequest('POST', '/auth/login', { mock_id_number, otp });
  if (data.access_token) {
    setToken(data.access_token);
  }
  return data;
}

export async function logoutApi() {
  try {
    await apiRequest('POST', '/auth/logout');
  } catch {
    // Ignore network error on logout
  } finally {
    clearToken();
  }
}

export async function register(mock_id_number, name) {
  return apiRequest('POST', '/auth/register', { mock_id_number, name });
}

export async function getMe() {
  return apiRequest('GET', '/auth/me');
}

// Citizen endpoints
export async function uploadIssue(formData) {
  return apiRequest('POST', '/issues/upload', formData, true);
}

export async function getPreview(imageId) {
  return apiRequest('GET', `/issues/${imageId}/preview`);
}

export async function confirmIssue(imageId, coords = null) {
  const body = coords ? { lat: coords.lat, lng: coords.lng } : null;
  return apiRequest('POST', `/issues/${imageId}/confirm`, body);
}

export async function getMyIssues() {
  return apiRequest('GET', '/issues/my-issues');
}

export async function trackIssue(clusterId) {
  return apiRequest('GET', `/issues/track/${clusterId}`);
}

export async function confirmResolution(clusterId, status) {
  return apiRequest('POST', '/issues/confirm-resolution', { cluster_id: clusterId, status });
}

// Admin endpoints
export async function getQueue(departmentId = null, status = null) {
  const params = new URLSearchParams();
  if (departmentId) params.append('department_id', departmentId);
  if (status) params.append('status', status);
  const qs = params.toString() ? `?${params.toString()}` : '';
  return apiRequest('GET', `/admin/queue${qs}`);
}

export async function getOfficers(departmentId = null) {
  const params = new URLSearchParams();
  if (departmentId) params.append('department_id', departmentId);
  const qs = params.toString() ? `?${params.toString()}` : '';
  return apiRequest('GET', `/admin/officers${qs}`);
}

export async function getIssueDetail(clusterId) {
  return apiRequest('GET', `/admin/issues/${clusterId}`);
}

export async function assignOfficer(clusterId, officerId) {
  const formData = new FormData();
  formData.append('officer_id', officerId);
  return apiRequest('POST', `/admin/issues/${clusterId}/assign`, formData, true);
}

export async function getHeatmapData() {
  return apiRequest('GET', '/admin/heatmap');
}

export async function dispatchContractor(clusterId) {
  return apiRequest('POST', `/admin/issues/${clusterId}/dispatch`);
}

export async function uploadCompletion(clusterId, formData) {
  return apiRequest('POST', `/admin/issues/${clusterId}/completion-evidence`, formData, true);
}

export async function closeIssue(clusterId) {
  return apiRequest('POST', `/admin/issues/${clusterId}/close`);
}

export async function reopenIssue(clusterId, reason) {
  const formData = new FormData();
  formData.append('reason', reason);
  return apiRequest('POST', `/admin/issues/${clusterId}/reopen`, formData, true);
}

// Contractor Email endpoints
export async function getContractorEmailStatus(clusterId) {
  return apiRequest('GET', `/contractor-email/${clusterId}`);
}

export async function draftContractorEmail(clusterId, officerId) {
  return apiRequest('POST', '/contractor-email/draft', { cluster_id: clusterId, officer_id: officerId });
}

export async function approveContractorEmail(draftId, adminId = 1) {
  return apiRequest('POST', '/contractor-email/approve', { draft_id: draftId, admin_id: adminId });
}

export async function sendContractorEmail(draftId) {
  return apiRequest('POST', '/contractor-email/send', { draft_id: draftId });
}

