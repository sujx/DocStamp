<template>
  <div class="card bg-surface border-default">
    <!-- Tab switcher -->
    <UTabs v-model="activeTab" :items="tabs" class="mb-4" />

    <!-- DB toolbar (always visible) -->
    <div class="flex items-center gap-2 mb-4 pb-3 border-b border-default">
      <span class="text-xs text-tertiary mr-1">{{ $t('companyLookup.dbCount', { n: dbCount }) }}</span>
      <div class="flex gap-1 ml-auto">
        <UButton color="neutral" variant="ghost" size="2xs" :loading="exportingDb" @click="exportDb">
          <UIcon name="i-heroicons-cloud-arrow-down" class="w-3 h-3 mr-0.5" />
          {{ $t('companyLookup.exportDb') }}
        </UButton>
        <UButton color="neutral" variant="ghost" size="2xs" :loading="importingDb" @click="triggerImport">
          <UIcon name="i-heroicons-cloud-arrow-up" class="w-3 h-3 mr-0.5" />
          {{ $t('companyLookup.importDb') }}
        </UButton>
        <UButton color="neutral" variant="ghost" size="2xs" @click="downloadTemplate">
          <UIcon name="i-heroicons-document-arrow-down" class="w-3 h-3 mr-0.5" />
          {{ $t('companyLookup.downloadTemplate') }}
        </UButton>
        <input ref="importInput" type="file" accept=".csv,.json" class="hidden" @change="importDb" />
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════
         TAB 1: Single Query
         ════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 0" class="flex flex-col sm:flex-row gap-3">
      <UInput
        v-model="singleName"
        :placeholder="$t('companyLookup.placeholder')"
        size="lg"
        class="flex-1"
        :disabled="singleLoading"
        @keyup.enter="doSingleLookup"
      />
      <UButton color="primary" size="lg" :loading="singleLoading" @click="doSingleLookup">
        <UIcon name="i-heroicons-magnifying-glass" class="w-4 h-4 mr-1.5" />
        {{ singleLoading ? $t("companyLookup.searching") : $t("companyLookup.search") }}
      </UButton>
    </div>

    <!-- Single: error -->
    <div
      v-if="singleError"
      class="mt-4 p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700"
    >
      {{ singleError }}
    </div>

    <!-- Single: result -->
    <div v-if="singleResult" class="mt-6">
      <div
        class="flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-lg"
        :class="singleResult.source === 'local' ? 'bg-green-50 border border-green-200' : 'bg-amber-50 border border-amber-200'"
      >
        <!-- Info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <p class="text-sm font-semibold text-primary truncate">{{ singleResult.name }}</p>
            <span
              class="shrink-0 text-xs px-2 py-0.5 rounded-full font-medium"
              :class="singleResult.source === 'local'
                ? 'bg-green-100 text-green-700'
                : 'bg-amber-100 text-amber-700'"
            >
              {{ singleResult.source === 'local' ? $t('companyLookup.sourceLocal') : $t('companyLookup.sourceWeb') }}
            </span>
            <span
              v-if="singleResult.confirmed"
              class="shrink-0 text-xs px-2 py-0.5 rounded-full font-medium bg-green-100 text-green-700"
            >
              <UIcon name="i-heroicons-check-circle" class="w-3 h-3 inline mr-0.5" />
              {{ $t('companyLookup.confirmed') }}
            </span>
          </div>
          <a
            :href="singleResult.website"
            target="_blank"
            rel="noopener noreferrer"
            class="text-sm text-brand-700 hover:underline break-all"
          >
            {{ singleResult.website }}
          </a>
        </div>

        <!-- Actions -->
        <div class="flex gap-1.5 shrink-0">
          <UButton size="xs" variant="ghost" color="neutral" @click="copyUrl(singleResult.website)">
            <UIcon name="i-heroicons-clipboard" class="w-3.5 h-3.5" />
            {{ $t('companyLookup.copy') }}
          </UButton>
          <UButton size="xs" variant="ghost" color="neutral" @click="openUrl(singleResult.website)">
            <UIcon name="i-heroicons-arrow-top-right-on-square" class="w-3.5 h-3.5" />
            {{ $t('companyLookup.open') }}
          </UButton>
        </div>
      </div>

      <!-- Confirm button (only for unconfirmed web results) -->
      <div v-if="!singleResult.confirmed && !editingSingle" class="mt-3 flex gap-2">
        <UButton
          color="primary"
          size="sm"
          :loading="singleConfirming"
          @click="doConfirm(singleResult)"
        >
          <UIcon name="i-heroicons-check" class="w-4 h-4 mr-1" />
          {{ $t('companyLookup.confirm') }}
        </UButton>
        <UButton color="neutral" variant="ghost" size="sm" @click="startEditSingle">
          <UIcon name="i-heroicons-pencil" class="w-4 h-4 mr-1" />
          {{ $t('companyLookup.manualEdit') }}
        </UButton>
      </div>

      <!-- Inline edit mode -->
      <div v-if="editingSingle" class="mt-3 p-3 rounded-lg bg-muted space-y-2">
        <UFormGroup :label="$t('companyLookup.editName')">
          <UInput v-model="editName" size="sm" />
        </UFormGroup>
        <UFormGroup :label="$t('companyLookup.editWebsite')">
          <UInput v-model="editWebsite" size="sm" />
        </UFormGroup>
        <div class="flex gap-2">
          <UButton color="primary" size="sm" :loading="singleConfirming" @click="doConfirmWithEdit">
            {{ $t('companyLookup.saveCorrection') }}
          </UButton>
          <UButton color="neutral" variant="ghost" size="sm" @click="editingSingle = false">
            Cancel
          </UButton>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════
         TAB 2: Batch Query
         ════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 1">
      <!-- Input area -->
      <div class="space-y-3">
        <UTextarea
          v-model="batchNames"
          :placeholder="$t('companyLookup.batchPlaceholder')"
          :rows="6"
          :disabled="batchRunning"
        />
        <!-- Sample hint -->
        <div class="flex items-center gap-2 text-xs text-tertiary">
          <UIcon name="i-heroicons-light-bulb" class="w-3.5 h-3.5" />
          <span>{{ $t('companyLookup.sampleHint') }}</span>
          <UButton size="2xs" variant="ghost" color="primary" @click="fillSample">{{ $t('companyLookup.fillSample') }}</UButton>
        </div>
        <div class="flex items-center gap-3">
          <UButton
            color="primary"
            size="lg"
            :loading="batchRunning"
            :disabled="!batchNames.trim()"
            @click="doBatchLookup"
          >
            <UIcon name="i-heroicons-magnifying-glass" class="w-4 h-4 mr-1.5" />
            {{ batchRunning ? $t('companyLookup.searching') : $t('companyLookup.search') }}
          </UButton>
          <span v-if="batchNames.trim()" class="text-xs text-tertiary">
            {{ batchNames.split('\n').filter(Boolean).length }} entries
          </span>
        </div>
      </div>

      <!-- Progress bar -->
      <div v-if="batchRunning" class="mt-4 space-y-2">
        <UProgress :value="batchProgress" size="sm" color="primary" />
        <p class="text-xs text-tertiary">{{ batchMessage || $t('companyLookup.searching') }}</p>
      </div>

      <!-- Error -->
      <div
        v-if="batchError"
        class="mt-4 p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700"
      >
        {{ batchError }}
      </div>

      <!-- Results table -->
      <div v-if="batchResults.length > 0" class="mt-6 space-y-3">
        <!-- Summary + actions bar -->
        <div class="flex flex-col sm:flex-row sm:items-center gap-2">
          <p class="text-sm text-secondary">
            {{ $t('companyLookup.foundResults', { n: batchResults.length }) }}
            ·
            {{ $t('companyLookup.localHit', {
              n: batchResults.filter(r => r.source === 'local').length,
              m: batchResults.filter(r => r.source !== 'local' && r.source !== 'error').length
            }) }}
          </p>
          <div class="flex gap-2 sm:ml-auto">
            <UButton
              v-if="unconfirmedCount > 0"
              color="primary"
              size="xs"
              :loading="batchConfirming"
              @click="doConfirmAll"
            >
              <UIcon name="i-heroicons-check" class="w-3.5 h-3.5 mr-1" />
              {{ $t('companyLookup.confirmAll') }} ({{ unconfirmedCount }})
            </UButton>
            <UButton color="neutral" variant="ghost" size="xs" @click="exportCsv">
              <UIcon name="i-heroicons-arrow-down-tray" class="w-3.5 h-3.5 mr-1" />
              {{ $t('companyLookup.exportCsv') }}
            </UButton>
          </div>

        </div>

        <!-- Table -->
        <div class="overflow-x-auto border border-default rounded-lg">
          <table class="w-full text-sm">
            <thead class="bg-muted text-left">
              <tr>
                <th class="px-3 py-2 font-medium text-tertiary w-10">#</th>
                <th class="px-3 py-2 font-medium text-tertiary">Company</th>
                <th class="px-3 py-2 font-medium text-tertiary">Website</th>
                <th class="px-3 py-2 font-medium text-tertiary w-24">Source</th>
                <th class="px-3 py-2 font-medium text-tertiary w-24">Status</th>
                <th class="px-3 py-2 font-medium text-tertiary w-28">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(r, i) in batchResults"
                :key="i"
                class="border-t border-default hover:bg-muted/50 transition-colors duration-150"
              >
                <td class="px-3 py-2 text-tertiary">{{ i + 1 }}</td>
                <td class="px-3 py-2 font-medium text-primary max-w-40 truncate" :title="r.name">
                  {{ r.name }}
                </td>
                <td class="px-3 py-2 max-w-48 truncate">
                  <a
                    v-if="r.website"
                    :href="r.website"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-brand-700 hover:underline text-xs break-all"
                  >
                    {{ r.website }}
                  </a>
                  <span v-else class="text-tertiary text-xs">—</span>
                </td>
                <td class="px-3 py-2">
                  <span
                    v-if="r.source !== 'error'"
                    class="text-xs px-1.5 py-0.5 rounded-full font-medium"
                    :class="r.source === 'local'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-amber-100 text-amber-700'"
                  >
                    {{ r.source === 'local' ? $t('companyLookup.sourceLocal') : $t('companyLookup.sourceWeb') }}
                  </span>
                  <span v-else class="text-xs text-red-600">Error</span>
                </td>
                <td class="px-3 py-2">
                  <span
                    v-if="r.confirmed"
                    class="text-xs text-green-700 flex items-center gap-0.5"
                  >
                    <UIcon name="i-heroicons-check-circle" class="w-3 h-3" />
                    {{ $t('companyLookup.confirmed') }}
                  </span>
                  <span v-else-if="r.source === 'local'" class="text-xs text-green-700">
                    {{ $t('companyLookup.confirmed') }}
                  </span>
                  <span v-else-if="r.source === 'web'" class="text-xs text-amber-600">
                    {{ $t('companyLookup.unconfirmed') }}
                  </span>
                  <span v-else class="text-xs text-red-600">
                    {{ r.error || 'N/A' }}
                  </span>
                </td>
                <td class="px-3 py-2">
                  <div v-if="r.website && r.source === 'web' && !r.confirmed" class="flex gap-1">
                    <UButton
                      size="2xs"
                      color="primary"
                      variant="ghost"
                      :loading="confirmingRows.has(i)"
                      @click="doConfirmRow(i, r)"
                    >
                      {{ $t('companyLookup.confirm') }}
                    </UButton>
                    <UButton
                      size="2xs"
                      color="neutral"
                      variant="ghost"
                      @click="copyUrl(r.website)"
                    >
                      <UIcon name="i-heroicons-clipboard" class="w-3 h-3" />
                    </UButton>
                  </div>
                  <div v-else-if="r.website" class="flex gap-1">
                    <UButton
                      size="2xs"
                      color="neutral"
                      variant="ghost"
                      @click="copyUrl(r.website)"
                    >
                      <UIcon name="i-heroicons-clipboard" class="w-3 h-3" />
                    </UButton>
                    <UButton
                      size="2xs"
                      color="neutral"
                      variant="ghost"
                      @click="openUrl(r.website)"
                    >
                      <UIcon name="i-heroicons-arrow-top-right-on-square" class="w-3 h-3" />
                    </UButton>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const toast = useToast();

// ── Tabs ─────────────────────────────────────────────────────────────────
const activeTab = ref(0);
const tabs = computed(() => [
  { label: t("companyLookup.singleQuery") },
  { label: t("companyLookup.batchQuery") },
]);

// ── Single Query state ───────────────────────────────────────────────────
const singleName = ref("");
const singleLoading = ref(false);
const singleResult = ref<{
  name: string;
  website: string;
  source: string;
  confirmed: boolean;
} | null>(null);
const singleError = ref("");
const singleConfirming = ref(false);
const editingSingle = ref(false);
const editName = ref("");
const editWebsite = ref("");

async function doSingleLookup() {
  const name = singleName.value.trim();
  if (!name) return;

  singleError.value = "";
  singleResult.value = null;
  editingSingle.value = false;
  singleLoading.value = true;

  try {
    const resp = await axios.post("/api/v1/company-lookup", { name });
    singleResult.value = resp.data.data;
  } catch (e: any) {
    singleError.value = e.response?.data?.msg || e.message || "Lookup failed";
  } finally {
    singleLoading.value = false;
  }
}

function startEditSingle() {
  if (!singleResult.value) return;
  editName.value = singleResult.value.name;
  editWebsite.value = singleResult.value.website;
  editingSingle.value = true;
}

async function doConfirm(result: { name: string; website: string }) {
  singleConfirming.value = true;
  try {
    await axios.post("/api/v1/company-lookup/confirm", {
      name: result.name,
      website: result.website,
    });
    if (singleResult.value) {
      singleResult.value.confirmed = true;
      singleResult.value.source = "local";
    }
    toast.add({ title: t("companyLookup.confirmed"), color: "success" });
  } catch (e: any) {
    toast.add({
      title: e.response?.data?.msg || "Confirm failed",
      color: "error",
    });
  } finally {
    singleConfirming.value = false;
  }
}

async function doConfirmWithEdit() {
  if (!singleResult.value) return;
  singleConfirming.value = true;
  try {
    await axios.post("/api/v1/company-lookup/confirm", {
      name: singleResult.value.name,
      website: singleResult.value.website,
      corrected_name: editName.value,
      corrected_website: editWebsite.value,
    });
    singleResult.value.name = editName.value;
    singleResult.value.website = editWebsite.value;
    singleResult.value.confirmed = true;
    singleResult.value.source = "local";
    editingSingle.value = false;
    toast.add({ title: t("companyLookup.confirmed"), color: "success" });
  } catch (e: any) {
    toast.add({
      title: e.response?.data?.msg || "Confirm failed",
      color: "error",
    });
  } finally {
    singleConfirming.value = false;
  }
}

// ── Batch Query state ────────────────────────────────────────────────────
const batchNames = ref("");
const batchRunning = ref(false);
const batchProgress = ref(0);
const batchMessage = ref("");
const batchError = ref("");
const batchResults = ref<
  Array<{
    name: string;
    website: string;
    source: string;
    confirmed: boolean;
    error?: string;
  }>
>([]);
const batchConfirming = ref(false);
const confirmingRows = ref(new Set<number>());

const unconfirmedCount = computed(() =>
  batchResults.value.filter((r) => r.source === "web" && !r.confirmed).length
);

let batchEventSource: EventSource | null = null;

function fillSample() {
  batchNames.value = [
    "腾讯科技有限公司",
    "阿里巴巴集团控股有限公司",
    "华为技术有限公司",
    "北京字节跳动科技有限公司",
    "小米科技有限责任公司",
  ].join("\n");
}

async function doBatchLookup() {
  const names = batchNames.value
    .split("\n")
    .map((n) => n.trim())
    .filter(Boolean);

  if (!names.length) return;

  batchError.value = "";
  batchResults.value = [];
  batchProgress.value = 0;
  batchMessage.value = `${names.length} companies, please wait...`;
  batchRunning.value = true;

  try {
    const resp = await axios.post("/api/v1/company-lookup/batch", { names }, { timeout: 120000 });
    const payload = resp.data;
    const data = payload.data || payload;

    // Synchronous results (all batches now go through this path)
    if (data.results) {
      batchResults.value = data.results;
      batchRunning.value = false;
      return;
    }

    // >10: async — connect SSE stream
    const taskId = data.task_id;
    batchEventSource = new EventSource(
      `/api/v1/tasks/${encodeURIComponent(taskId)}/stream`
    );

    batchEventSource.onmessage = (e: MessageEvent) => {
      try {
        const d = JSON.parse(e.data);
        if (d.progress !== undefined) batchProgress.value = d.progress;
        if (d.status) {
          if (d.status === "success" && d.result_data) {
            batchResults.value = JSON.parse(d.result_data);
            batchRunning.value = false;
            batchEventSource?.close();
          } else if (d.status === "failure") {
            batchError.value = d.error_message || "Batch lookup failed";
            batchRunning.value = false;
            batchEventSource?.close();
          }
        }
        if (d.progress_message) batchMessage.value = d.progress_message;
      } catch {
        // Ignore parse errors
      }
    };

    batchEventSource.onerror = () => {
      if (!batchRunning.value) batchEventSource?.close();
    };
  } catch (e: any) {
    batchError.value = e.response?.data?.msg || e.message || "Batch lookup failed";
    batchRunning.value = false;
  }
}

async function doConfirmRow(index: number, result: { name: string; website: string }) {
  confirmingRows.value.add(index);
  try {
    await axios.post("/api/v1/company-lookup/confirm", {
      name: result.name,
      website: result.website,
    });
    batchResults.value[index].confirmed = true;
    batchResults.value[index].source = "local";
    toast.add({ title: t("companyLookup.confirmed"), color: "success" });
  } catch (e: any) {
    toast.add({
      title: e.response?.data?.msg || "Confirm failed",
      color: "error",
    });
  } finally {
    confirmingRows.value.delete(index);
  }
}

async function doConfirmAll() {
  batchConfirming.value = true;
  const toConfirm = batchResults.value
    .map((r, i) => ({ ...r, _idx: i }))
    .filter((r) => r.source === "web" && !r.confirmed && r.website);

  let succeeded = 0;
  for (const r of toConfirm) {
    try {
      await axios.post("/api/v1/company-lookup/confirm", {
        name: r.name,
        website: r.website,
      });
      batchResults.value[r._idx].confirmed = true;
      batchResults.value[r._idx].source = "local";
      succeeded++;
    } catch {
      // Skip individual failures
    }
  }

  toast.add({
    title: `${succeeded}/${toConfirm.length} confirmed`,
    color: succeeded === toConfirm.length ? "success" : "warning",
  });
  batchConfirming.value = false;
}

function exportCsv() {
  const header = "Name,Website,Source,Confirmed";
  const rows = batchResults.value.map(
    (r) =>
      `"${r.name}","${r.website}","${r.source}","${r.confirmed ? "Yes" : "No"}"`
  );
  const csv = [header, ...rows].join("\n");

  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "company-lookup-results.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

const exportingDb = ref(false);
const importingDb = ref(false);
const dbCount = ref(0);
const importInput = ref<HTMLInputElement | null>(null);

function triggerImport() {
  importInput.value?.click();
}

function downloadTemplate() {
  const csv = "name,website\n腾讯科技有限公司,https://www.tencent.com\n阿里巴巴集团控股有限公司,https://www.alibaba.com\n华为技术有限公司,https://www.huawei.com\n";
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "company_import_template.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function fetchDbCount() {
  try {
    const resp = await axios.get("/api/v1/company-lookup/export?format=json");
    dbCount.value = resp.data.data?.length || 0;
  } catch { /* ignore */ }
}
onMounted(() => fetchDbCount());

async function exportDb() {
  exportingDb.value = true;
  try {
    const resp = await axios.get("/api/v1/company-lookup/export", { responseType: "blob" });
    const url = URL.createObjectURL(new Blob([resp.data], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "company_records.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.add({ title: t("companyLookup.exportDb") + " OK", color: "success" });
  } catch (e: any) {
    toast.add({ title: extractError(e), color: "error" });
  } finally {
    exportingDb.value = false;
  }
}

async function importDb() {
  const file = importInput.value?.files?.[0];
  if (!file) return;
  importingDb.value = true;
  try {
    const form = new FormData();
    form.append("file", file);
    const resp = await axios.post("/api/v1/company-lookup/import", form);
    const data = resp.data.data;
    if (data.errors?.length) {
      toast.add({
        title: `${t("companyLookup.importSuccess", { n: data.imported })} · ${t("companyLookup.importErrors", { n: data.skipped })}`,
        color: data.imported > 0 ? "warning" : "error",
      });
    } else {
      toast.add({ title: t("companyLookup.importSuccess", { n: data.imported }), color: "success" });
    }
  } catch (e: any) {
    toast.add({ title: extractError(e), color: "error" });
  } finally {
    importingDb.value = false;
    if (importInput.value) importInput.value.value = "";
    fetchDbCount();
  }
}

function extractError(e: any): string {
  return e.response?.data?.msg || e.message || "Unknown error";
}

// ── Shared helpers ───────────────────────────────────────────────────────
async function copyUrl(url: string) {
  await navigator.clipboard.writeText(url);
  toast.add({ title: t("companyLookup.copied"), color: "success" });
}

function openUrl(url: string) {
  window.open(url, "_blank");
}

// Cleanup SSE on unmount
onUnmounted(() => {
  batchEventSource?.close();
});
</script>
