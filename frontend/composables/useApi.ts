/** Generic API composable for paginated list endpoints.

Provides loading state, pagination, and fetchList for list-type endpoints.
Used as a building block for feature-specific composables.

Usage:
    const { data, loading, pagination, fetchList } = useApiList<T>("/api/items");
    await fetchList({ status: "active" });
*/

import { ref } from "vue";
import axios from "axios";

export interface Pagination {
  page: number;
  size: number;
  total: number;
}

export function useApiList<T>(url: string) {
  const data = ref<T[]>([]);
  const loading = ref(false);
  const pagination = ref<Pagination>({ page: 1, size: 20, total: 0 });

  async function fetchList(params: Record<string, unknown> = {}) {
    loading.value = true;
    try {
      const res = await axios.get(url, {
        params: { ...params, page: pagination.value.page, size: pagination.value.size },
      });
      if (res.data?.data) {
        data.value = res.data.data.list || res.data.data;
        pagination.value.total = res.data.data.total || 0;
      }
    } finally {
      loading.value = false;
    }
  }

  function setPage(page: number) {
    pagination.value.page = page;
  }

  return { data, loading, pagination, fetchList, setPage };
}

/** Simple caching fetch wrapper using in-memory Map. */
const _cache = new Map<string, { data: unknown; expiry: number }>();

export function useCache(key: string, ttl = 300_000) {
  function get<T>(): T | null {
    const entry = _cache.get(key);
    if (entry && entry.expiry > Date.now()) {
      return entry.data as T;
    }
    _cache.delete(key);
    return null;
  }

  function set<T>(value: T): void {
    _cache.set(key, { data: value, expiry: Date.now() + ttl });
  }

  function invalidate(): void {
    _cache.delete(key);
  }

  return { get, set, invalidate };
}
