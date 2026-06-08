/**
 * Shared TypeScript types used across components and composables.
 *
 * @module types/common
 */

export interface FileItem {
  file: File;
  id: string;
  name: string;
  size: number;
}

export interface Pagination {
  page: number;
  size: number;
  total: number;
}

export interface ApiError {
  code: number;
  msg: string;
  requestId: string;
}

export interface TaskProgress {
  taskId: string;
  status: "pending" | "started" | "progress" | "success" | "failure";
  progress: number;
  message: string;
  result: Record<string, unknown> | null;
  error: string | null;
}

/** Standard API list response wrapper. */
export interface ApiListResponse<T> {
  code: number;
  data: {
    list: T[];
    total: number;
  };
  requestId: string;
}
