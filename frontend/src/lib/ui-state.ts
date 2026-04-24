const PII_MASK_STORAGE_KEY = "resolvemesh_pii_masked";
const CASE_NOTIFICATIONS_STORAGE_KEY = "resolvemesh_case_notifications";
const MESH_AUTONOMY_STORAGE_KEY = "resolvemesh_mesh_autonomy";
const NOTIFICATIONS_VISIBILITY_STORAGE_KEY = "resolvemesh_notifications_visibility";
const SANDBOX_MODE_STORAGE_KEY = "resolvemesh_sandbox_mode";

export const PII_MASK_CHANGED_EVENT = "resolvemesh:pii-mask-changed";
export const CASE_NOTIFICATIONS_CHANGED_EVENT = "resolvemesh:case-notifications-changed";
export const UI_SETTINGS_CHANGED_EVENT = "resolvemesh:ui-settings-changed";

export type CaseNotificationKind = "normal" | "critical" | "spam";

export type CaseNotification = {
  id: string;
  disputeId: string;
  status: string;
  kind: CaseNotificationKind;
  label: string;
  createdAt: string;
  read: boolean;
};

function parseJSON<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback;

  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function emitEvent(name: string) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(name));
}

export function getPIIMaskEnabled(): boolean {
  if (typeof window === "undefined") return true;

  const stored = window.localStorage.getItem(PII_MASK_STORAGE_KEY);
  if (stored === "true") return true;
  if (stored === "false") return false;

  return true;
}

export function setPIIMaskEnabled(masked: boolean) {
  if (typeof window === "undefined") return;

  window.localStorage.setItem(PII_MASK_STORAGE_KEY, String(masked));
  emitEvent(PII_MASK_CHANGED_EVENT);
  emitEvent(UI_SETTINGS_CHANGED_EVENT);
}

function getBooleanSetting(storageKey: string, fallback: boolean): boolean {
  if (typeof window === "undefined") return fallback;

  const stored = window.localStorage.getItem(storageKey);
  if (stored === "true") return true;
  if (stored === "false") return false;

  return fallback;
}

function setBooleanSetting(storageKey: string, value: boolean) {
  if (typeof window === "undefined") return;

  window.localStorage.setItem(storageKey, String(value));
  emitEvent(UI_SETTINGS_CHANGED_EVENT);
}

export function getMeshAutonomyEnabled(): boolean {
  return getBooleanSetting(MESH_AUTONOMY_STORAGE_KEY, true);
}

export function setMeshAutonomyEnabled(enabled: boolean) {
  setBooleanSetting(MESH_AUTONOMY_STORAGE_KEY, enabled);
}

export function getNotificationsVisible(): boolean {
  return getBooleanSetting(NOTIFICATIONS_VISIBILITY_STORAGE_KEY, true);
}

export function setNotificationsVisible(enabled: boolean) {
  setBooleanSetting(NOTIFICATIONS_VISIBILITY_STORAGE_KEY, enabled);
}

export function getSandboxModeEnabled(): boolean {
  return getBooleanSetting(SANDBOX_MODE_STORAGE_KEY, false);
}

export function setSandboxModeEnabled(enabled: boolean) {
  setBooleanSetting(SANDBOX_MODE_STORAGE_KEY, enabled);
}

export function getCaseNotifications(): CaseNotification[] {
  if (typeof window === "undefined") return [];

  const stored = parseJSON<CaseNotification[]>(
    window.localStorage.getItem(CASE_NOTIFICATIONS_STORAGE_KEY),
    [],
  );

  return stored
    .filter((item) => item && typeof item.disputeId === "string")
    .sort((left, right) => Date.parse(right.createdAt) - Date.parse(left.createdAt));
}

export function classifyCase(status: string): {
  kind: CaseNotificationKind;
  label: string;
} {
  const normalized = status.toUpperCase();

  if (normalized.includes("SUSPECTED_FRAUD") || normalized.includes("FRAUD")) {
    return { kind: "spam", label: "spam case (suspected_fraud)" };
  }

  if (normalized.includes("CRITICAL") || normalized.includes("FLAG")) {
    return { kind: "critical", label: "critical case" };
  }

  return { kind: "normal", label: "normal case" };
}

export function addCaseNotification(input: {
  disputeId: string;
  status: string;
  createdAt?: string;
}) {
  if (typeof window === "undefined") return;

  const existing = getCaseNotifications();
  if (existing.some((notification) => notification.disputeId === input.disputeId)) {
    return;
  }

  const classified = classifyCase(input.status);
  const notification: CaseNotification = {
    id: `${input.disputeId}-${Date.now()}`,
    disputeId: input.disputeId,
    status: input.status,
    kind: classified.kind,
    label: classified.label,
    createdAt: input.createdAt ?? new Date().toISOString(),
    read: false,
  };

  const updated = [notification, ...existing].slice(0, 50);
  window.localStorage.setItem(CASE_NOTIFICATIONS_STORAGE_KEY, JSON.stringify(updated));
  emitEvent(CASE_NOTIFICATIONS_CHANGED_EVENT);
}

export function markAllCaseNotificationsRead() {
  if (typeof window === "undefined") return;

  const existing = getCaseNotifications();
  if (existing.every((notification) => notification.read)) {
    return;
  }

  const updated = existing.map((notification) => ({
    ...notification,
    read: true,
  }));

  window.localStorage.setItem(CASE_NOTIFICATIONS_STORAGE_KEY, JSON.stringify(updated));
  emitEvent(CASE_NOTIFICATIONS_CHANGED_EVENT);
}