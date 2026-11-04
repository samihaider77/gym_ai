import type { User } from './types';

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const TOKEN_KEY = 'gymai.token';
const USER_KEY = 'gymai.user';

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

function storage(): Storage | null {
  try {
    return typeof window === 'undefined' ? null : window.localStorage;
  } catch {
    return null;
  }
}

export const session = {
  token: () => storage()?.getItem(TOKEN_KEY) ?? null,
  user: (): User | null => {
    try {
      const raw = storage()?.getItem(USER_KEY);
      return raw ? (JSON.parse(raw) as User) : null;
    } catch {
      return null;
    }
  },
  save(token: string, user: User) {
    storage()?.setItem(TOKEN_KEY, token);
    storage()?.setItem(USER_KEY, JSON.stringify(user));
  },
  clear() {
    storage()?.removeItem(TOKEN_KEY);
    storage()?.removeItem(USER_KEY);
  },
};

function errorMessage(body: unknown, status: number): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail[0]?.msg) {
      const field = Array.isArray(detail[0].loc) ? detail[0].loc[detail[0].loc.length - 1] : '';
      return field ? `${String(field).replace(/_/g, ' ')}: ${detail[0].msg}` : detail[0].msg;
    }
  }
  if (status >= 500) return 'The server had a problem. Try again in a moment.';
  return 'Something went wrong. Try again.';
}

type Query = Record<string, string | number | boolean | null | undefined>;

export async function api<T>(
  path: string,
  options: { method?: string; body?: unknown; query?: Query; signal?: AbortSignal } = {},
): Promise<T> {
  const url = new URL(`${API_URL}/api/v1${path}`);
  Object.entries(options.query ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, String(value));
  });
  const token = session.token();
  let response: Response;
  try {
    response = await fetch(url, {
      method: options.method ?? 'GET',
      signal: options.signal,
      headers: {
        ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  } catch (error) {
    if ((error as Error).name === 'AbortError') throw error;
    throw new ApiError('Can’t reach the server. Is the backend running on port 8000?', 0);
  }
  if (response.status === 401 && token) {
    session.clear();
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
    }
  }
  if (response.status === 204) return undefined as T;
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(errorMessage(body, response.status), response.status);
  return body as T;
}

/** Media paths from the API are site-relative ("/exercise-media/..."), served from public/. */
export function mediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  return path;
}
