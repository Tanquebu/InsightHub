import type {
  Dataset,
  DatasetInsights,
  DatasetProfile,
  Project,
  TokenResponse,
} from "./types";

const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const TOKEN_STORAGE_KEY = "insighthub_access_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function extractErrorDetail(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (
      body !== null &&
      typeof body === "object" &&
      "detail" in body &&
      typeof (body as { detail: unknown }).detail === "string"
    ) {
      return (body as { detail: string }).detail;
    }
  } catch {
    // corpo assente o non-JSON: usiamo il messaggio di fallback.
  }
  return fallback;
}

/**
 * Wrapper fetch centralizzato per le route autenticate.
 * Allega l'header Authorization se un token è presente in localStorage.
 * Su 401 pulisce il token salvato e reindirizza al login (sessione scaduta
 * o non valida) — un redirect "duro" via window.location è sufficiente per
 * l'MVP e funziona anche fuori dal contesto di un componente React.
 */
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearToken();
    if (
      typeof window !== "undefined" &&
      window.location.pathname !== "/login"
    ) {
      window.location.assign("/login");
    }
    throw new ApiError(401, "Sessione scaduta o non autorizzata.");
  }

  if (!response.ok) {
    const detail = await extractErrorDetail(response, response.statusText);
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

/**
 * Login: l'API si aspetta un body application/x-www-form-urlencoded
 * (OAuth2PasswordRequestForm), non JSON. Usa un fetch diretto (non il
 * wrapper `request`) perché un 401 qui è un errore di credenziali da
 * mostrare inline nel form di login, non una sessione scaduta da cui
 * fare redirect.
 */
export async function login(
  username: string,
  password: string,
): Promise<TokenResponse> {
  const form = new URLSearchParams();
  form.set("username", username);
  form.set("password", password);

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });

  if (!response.ok) {
    const detail = await extractErrorDetail(
      response,
      "Credenziali non valide.",
    );
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as TokenResponse;
}

export function listProjects(): Promise<Project[]> {
  return apiGet<Project[]>("/api/v1/projects");
}

export function listDatasets(projectId: number): Promise<Dataset[]> {
  return apiGet<Dataset[]>(`/api/v1/projects/${projectId}/datasets`);
}

export function getDataset(
  projectId: number,
  datasetId: number,
): Promise<Dataset> {
  return apiGet<Dataset>(
    `/api/v1/projects/${projectId}/datasets/${datasetId}`,
  );
}

export function getDatasetProfile(
  projectId: number,
  datasetId: number,
): Promise<DatasetProfile> {
  return apiGet<DatasetProfile>(
    `/api/v1/projects/${projectId}/datasets/${datasetId}/profile`,
  );
}

export function getDatasetInsights(
  projectId: number,
  datasetId: number,
): Promise<DatasetInsights> {
  return apiGet<DatasetInsights>(
    `/api/v1/projects/${projectId}/datasets/${datasetId}/insights`,
  );
}
