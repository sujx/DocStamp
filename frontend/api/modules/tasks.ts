/**
 * Task tracking and download API.
 *
 * @module api/modules/tasks
 */
import api from "../index";

export interface TaskRecord {
  id: string;
  task_type: string;
  queue: string;
  status: "pending" | "started" | "progress" | "success" | "failure";
  progress: number;
  progress_message?: string;
  result_data?: string;
  error_code?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface HealthResponse {
  status: string;
}

export const tasksApi = {
  /** Health check. */
  health: () => api.get<HealthResponse>("/api/v1/health").then((r) => r.data),

  /** Get a task's current status (polling). */
  status: (taskId: string) =>
    api.get<{ code: number; data: TaskRecord; requestId: string }>(
      `/api/v1/tasks/${encodeURIComponent(taskId)}`,
    ).then((r) => r.data.data),
};
