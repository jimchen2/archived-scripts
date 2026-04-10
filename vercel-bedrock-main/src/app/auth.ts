// src/components/auth.ts

export const login = (apiKey: string) => {
  localStorage.setItem('apiKey', apiKey);
};

export const logout = () => {
  localStorage.removeItem('apiKey');
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('apiKey');
};

export const getApiKey = () => {
  return localStorage.getItem('apiKey');
};
