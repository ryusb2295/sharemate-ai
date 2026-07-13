import { API_BASE_URL } from '@/constants/api';

type ApiRequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown;
  token?: string | null;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function getErrorMessage(payload: unknown): string {
  if (!payload || typeof payload !== 'object' || !('detail' in payload)) {
    return '요청을 처리하지 못했습니다.';
  }

  const detail = payload.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const firstError = detail[0];
    if (firstError && typeof firstError === 'object' && 'msg' in firstError) {
      return String(firstError.msg).replace(/^Value error, /, '');
    }
  }
  return '입력 내용을 확인해주세요.';
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  headers.set('Accept', 'application/json');
  if (options.body !== undefined && !isFormData) headers.set('Content-Type', 'application/json');
  if (options.token) headers.set('Authorization', `Bearer ${options.token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      body:
        options.body === undefined
          ? undefined
          : isFormData
            ? (options.body as FormData)
            : JSON.stringify(options.body),
      headers,
    });
  } catch {
    throw new ApiError(
      '서버에 연결할 수 없습니다. iPhone과 컴퓨터의 Wi-Fi 및 EXPO_PUBLIC_API_URL을 확인해주세요.'
    );
  }

  const payload = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(getErrorMessage(payload), response.status);
  return payload as T;
}
