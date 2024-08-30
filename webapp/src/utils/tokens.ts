export const getToken = (): string | null => {
  return localStorage.getItem('aicacia-api-token');
};

export const setToken = (token: string): void => {
  localStorage.setItem('aicacia-api-token', token);
};

export const removeToken = (): void => {
  localStorage.removeItem('aicacia-api-token');
};