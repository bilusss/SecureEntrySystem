const API_BASE_URL = '';  // Używamy proxy Vite - wszystko idzie przez ten sam origin

// Helper do obsługi błędów
const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Błąd serwera' }));
    throw new Error(error.detail || 'Wystąpił błąd');
  }
  
  // Dla statusów 204 (No Content) nie ma body
  if (response.status === 204) {
    return null;
  }
  
  return response.json();
};

// ============ AUTH ============

export const authApi = {
  login: async (email, password) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Ważne dla cookies
      body: JSON.stringify({ email, password }),
    });
    return handleResponse(response);
  },

  logout: async () => {
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    return handleResponse(response);
  },

  register: async (email, password) => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    });
    return handleResponse(response);
  },
};

// ============ EMPLOYEES ============

export const employeesApi = {
  list: async () => {
    const response = await fetch(`${API_BASE_URL}/api/employees/`, {
      method: 'GET',
      credentials: 'include',
    });
    return handleResponse(response);
  },

  create: async (employeeData, photoFile) => {
    const formData = new FormData();
    formData.append('email', employeeData.email);
    formData.append('first_name', employeeData.firstName);
    formData.append('last_name', employeeData.lastName);
    formData.append('photo', photoFile);

    const response = await fetch(`${API_BASE_URL}/api/employees/`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });
    return handleResponse(response);
  },

  update: async (employeeId, employeeData, photoFile = null) => {
    const formData = new FormData();
    if (employeeData.email) formData.append('email', employeeData.email);
    if (employeeData.firstName) formData.append('first_name', employeeData.firstName);
    if (employeeData.lastName) formData.append('last_name', employeeData.lastName);
    if (photoFile) formData.append('photo', photoFile);

    const response = await fetch(`${API_BASE_URL}/api/employees/${employeeId}`, {
      method: 'PUT',
      credentials: 'include',
      body: formData,
    });
    return handleResponse(response);
  },

  delete: async (employeeId) => {
    const response = await fetch(`${API_BASE_URL}/api/employees/${employeeId}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    return handleResponse(response);
  },

  generateQrCode: async (employeeId) => {
    const response = await fetch(`${API_BASE_URL}/api/employees/${employeeId}/generate_qr_code`, {
      method: 'POST',
      credentials: 'include',
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Błąd serwera' }));
      throw new Error(error.detail || 'Nie udało się wygenerować kodu QR');
    }
    
    // Zwróć blob zamiast JSON
    return await response.blob();
  },

  revokeQrCode: async (employeeId) => {
    const response = await fetch(`${API_BASE_URL}/api/employees/${employeeId}/revoke_qr_code`, {
      method: 'DELETE',
      credentials: 'include',
    });
    return handleResponse(response);
  },

  getPhotoUrl: (photoPath) => {
    if (!photoPath) return null;
    return `${API_BASE_URL}/uploads/${photoPath}`;
  },
};

// ============ ENTRIES ============

export const entriesApi = {
  verifyEntry: async (qrCodePayload, photoBlob) => {
    const formData = new FormData();
    formData.append('qr_code_payload', qrCodePayload);
    formData.append('photo', photoBlob, 'face.jpg');

    const response = await fetch(`${API_BASE_URL}/api/entries/`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(response);
  },

  generateReport: async () => {
    const response = await fetch(`${API_BASE_URL}/api/entries/generate-raport`, {
      method: 'POST',
      credentials: 'include',
    });
    return handleResponse(response);
  },
};

export default {
  auth: authApi,
  employees: employeesApi,
  entries: entriesApi,
};
