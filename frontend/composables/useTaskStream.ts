/** SSE-based task progress composable.

Connects to /api/tasks/{id}/stream and provides reactive progress state.
Falls back gracefully on connection errors (browser will auto-retry SSE).

Usage:
    const { progress, status, message, result, error, connect, close } = useTaskStream(taskId);
    onMounted(() => connect());
    onUnmounted(() => close());
*/

import { ref, onUnmounted } from "vue";

export interface TaskProgress {
  progress: ReturnType<typeof ref<number>>;
  status: ReturnType<typeof ref<string>>;
  message: ReturnType<typeof ref<string>>;
  result: ReturnType<typeof ref<Record<string, unknown> | null>>;
  error: ReturnType<typeof ref<string | null>>;
  connect: () => void;
  close: () => void;
}

export function useTaskStream(taskId: string): TaskProgress {
  const progress = ref(0);
  const status = ref<string>("pending");
  const message = ref("");
  const result = ref<Record<string, unknown> | null>(null);
  const error = ref<string | null>(null);

  let eventSource: EventSource | null = null;

  function connect() {
    if (eventSource) return; // Already connected

    eventSource = new EventSource(`/api/tasks/${encodeURIComponent(taskId)}/stream`);

    eventSource.onmessage = (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        if (data.progress !== undefined) progress.value = data.progress;
        if (data.status) status.value = data.status;
        if (data.progress_message) message.value = data.progress_message;
        if (data.result_data) result.value = JSON.parse(data.result_data);
        if (data.error_message) error.value = data.error_message;

        // Auto-close on terminal states
        if (data.status === "success" || data.status === "failure") {
          close();
        }
      } catch {
        // Ignore parse errors on malformed events
      }
    };

    eventSource.onerror = () => {
      // Browser will auto-reconnect for SSE unless we close it
      if (status.value === "success" || status.value === "failure") {
        close();
      }
    };
  }

  function close() {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  }

  onUnmounted(() => close());

  return { progress, status, message, result, error, connect, close };
}
