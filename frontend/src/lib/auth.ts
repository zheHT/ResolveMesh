export type AuthUser = {
  id: string;
  email: string;
};

const AUTH_STORAGE_KEY = "resolvemesh_auth_user";

export function getAuthUser(): AuthUser | null {
  if (typeof window === "undefined") return null;

  const stored = window.sessionStorage.getItem(AUTH_STORAGE_KEY);
  if (!stored) return null;

  try {
    return JSON.parse(stored) as AuthUser;
  } catch {
    window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

export function setAuthUser(user: AuthUser) {
  if (typeof window === "undefined") return;

  window.sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
}

export function clearAuthUser() {
  if (typeof window === "undefined") return;

  window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
}