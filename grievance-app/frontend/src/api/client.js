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

// Language and Translation endpoints
export async function updatePreferredLangApi(lang) {
  return apiRequest('PATCH', '/auth/preferred-lang', { lang });
}

export async function translateTextApi(text, targetLang) {
  return apiRequest('POST', '/issues/translate-preview', { text, target_lang: targetLang });
}
