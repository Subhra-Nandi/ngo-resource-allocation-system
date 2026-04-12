const TOKEN_KEY = "ngo_token";
const NGO_NAME_KEY = "ngo_name";

export function saveToken(token: string, ngoName: string) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(NGO_NAME_KEY, ngoName);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getNgoName(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(NGO_NAME_KEY);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(NGO_NAME_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}