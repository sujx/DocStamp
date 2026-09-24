<template>
  <div v-if="!session && !report" class="card bg-surface border-default">
    <FileUploader
      :key="uploaderKey"
      accept=".pdf"
      icon="i-heroicons-document"
      :hint="$t('pdfRedact.hint')"
      @file-selected="onFileSelected"
    />

    <div v-if="uploading" class="mt-5">
      <p class="mb-2 text-xs text-secondary">{{ $t("pdfRedact.uploading") }}</p>
      <UProgress :value="progress" :max="100" color="primary" />
    </div>
  </div>

  <div v-else-if="session" class="grid gap-4 lg:grid-cols-[6rem_minmax(0,1fr)_20rem]">
    <aside class="flex gap-2 overflow-x-auto lg:max-h-[36rem] lg:flex-col lg:overflow-y-auto">
      <button
        v-for="n in pageCount"
        :key="n"
        type="button"
        class="shrink-0 overflow-hidden rounded border-2 transition-colors duration-150"
        :class="n === current ? 'border-brand-700' : 'border-default'"
        :aria-label="$t('pdfRedact.pageOf', { page: n, total: pageCount })"
        @click="current = n"
      >
        <img :src="thumbUrl(n)" class="block h-20 w-auto bg-white" loading="lazy" alt="" />
      </button>
    </aside>

    <div class="card bg-surface border-default">
      <div class="mb-3 flex flex-wrap items-center gap-1.5">
        <UButton
          size="xs"
          variant="soft"
          color="neutral"
          icon="i-heroicons-chevron-left"
          :disabled="current <= 1"
          :aria-label="$t('pdfRedact.prevPage')"
          @click="current -= 1"
        />
        <span class="px-1 text-sm tabular-nums text-secondary">
          {{ $t("pdfRedact.pageOf", { page: current, total: pageCount }) }}
        </span>
        <UButton
          size="xs"
          variant="soft"
          color="neutral"
          icon="i-heroicons-chevron-right"
          :disabled="current >= pageCount"
          :aria-label="$t('pdfRedact.nextPage')"
          @click="current += 1"
        />

        <span class="grow" />

        <UButton
          size="xs"
          variant="ghost"
          color="neutral"
          icon="i-heroicons-minus-small"
          :aria-label="$t('pdfRedact.zoomOut')"
          @click="zoom = Math.max(0.5, zoom / 1.25)"
        />
        <span class="text-xs tabular-nums text-tertiary">{{ Math.round(zoom * 100) }}%</span>
        <UButton
          size="xs"
          variant="ghost"
          color="neutral"
          icon="i-heroicons-plus-small"
          :aria-label="$t('pdfRedact.zoomIn')"
          @click="zoom = Math.min(3, zoom * 1.25)"
        />
        <UButton size="xs" variant="ghost" color="neutral" @click="zoom = 1">
          {{ $t("pdfRedact.zoomReset") }}
        </UButton>
      </div>

      <p class="mb-2 text-xs text-tertiary">{{ $t("pdfRedact.drawHint") }}</p>

      <PdfRedactCanvas
        :page-url="pageUrl"
        :page-no="current"
        :marks="pageMarks"
        :selected-id="selectedId"
        :zoom="zoom"
        @create="onCreate"
        @update="onUpdate"
        @remove="removeMark"
        @select="selectedId = $event"
      />
    </div>

    <aside class="flex flex-col gap-3">
      <PdfRedactMarkList
        :marks="marks"
        :selected-id="selectedId"
        :searching="searching"
        @select="selectMark"
        @remove="removeMark"
        @undo="undoMark"
        @clear="clearMarks"
        @search="onSearch"
      />

      <div class="card bg-surface border-default">
        <UFormGroup :label="$t('pdfRedact.mosaicBlock')">
          <USelect v-model.number="mosaicBlock" :options="mosaicOptions" size="sm" />
        </UFormGroup>
        <UButton
          class="mt-3"
          color="primary"
          block
          icon="i-heroicons-eye-slash"
          :loading="applying"
          :disabled="!marks.length"
          @click="apply"
        >
          {{ applying ? $t("common.processing") : $t("pdfRedact.apply") }}
        </UButton>
      </div>
    </aside>
  </div>

  <div v-if="report" class="card bg-surface border-default" :class="session ? 'mt-4' : ''">
    <h2 class="text-base font-semibold text-primary">{{ $t("pdfRedact.reportTitle") }}</h2>

    <dl class="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-4">
      <div>
        <dt class="text-xs text-tertiary">{{ $t("pdfRedact.reportMarks") }}</dt>
        <dd class="text-lg font-semibold tabular-nums text-primary">{{ report.total_marks }}</dd>
      </div>
      <div>
        <dt class="text-xs text-tertiary">{{ $t("pdfRedact.reportApplied") }}</dt>
        <dd class="text-lg font-semibold tabular-nums text-primary">{{ report.applied }}</dd>
      </div>
      <div>
        <dt class="text-xs text-tertiary">{{ $t("pdfRedact.reportImageMarks") }}</dt>
        <dd class="text-lg font-semibold tabular-nums text-primary">{{ report.image_marks }}</dd>
      </div>
    </dl>

    <UAlert
      class="mt-4"
      :color="report.verified ? 'success' : 'warning'"
      variant="soft"
      :icon="report.verified ? 'i-heroicons-check-badge' : 'i-heroicons-exclamation-triangle'"
      :title="report.verified
        ? $t('pdfRedact.reportVerified')
        : $t('pdfRedact.reportLeftover', { n: report.leftover_regions.length })"
    />

    <UAlert
      class="mt-2"
      color="warning"
      variant="outline"
      icon="i-heroicons-lock-closed"
      :title="$t('pdfRedact.irreversible')"
    />

    <div class="mt-4 flex flex-wrap items-center gap-3">
      <UButton v-if="session" color="primary" icon="i-heroicons-arrow-down-tray" :loading="downloading" @click="download">
        {{ $t("pdfRedact.download") }}
      </UButton>
      <span v-else class="text-xs text-tertiary">{{ $t("pdfRedact.cleaned") }}</span>
      <UButton variant="ghost" color="neutral" @click="newFile">{{ $t("pdfRedact.newFile") }}</UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import PdfRedactCanvas from "./PdfRedactCanvas.vue";
import PdfRedactMarkList from "./PdfRedactMarkList.vue";
import type { MarkBox, RedactMark } from "~/composables/usePdfRedactMarks";
import { addKeywordMarks, createMarkHistory, nextMarkId } from "~/composables/usePdfRedactMarks";

// 与后端 file_security.MAX_FILE_SIZE 一致；上传前先拦，省得白传 100 MB。
const MAX_UPLOAD_BYTES = 100 * 1024 * 1024;
const PREVIEW_DPI = 110;
// 后端 MIN_DPI 就是 40；缩略图只要认得出页面。
const THUMB_DPI = 40;

interface Report {
  total_marks: number;
  applied: number;
  image_marks: number;
  leftover_regions: { mark: number; page: number }[];
  verified: boolean;
}

const { t } = useI18n();
const apiBase = useRuntimeConfig().public.apiBase;
const { showError } = useApiError();
const { downloadBlob } = useDownload();

const uploaderKey = ref(0);
const uploading = ref(false);
const progress = ref(0);

const session = ref<string | null>(null);
const originalName = ref("");
const pageCount = ref(0);
const current = ref(1);
const zoom = ref(1);

const marks = ref<RedactMark[]>([]);
const selectedId = ref<string | null>(null);
let history = createMarkHistory();
const searching = ref(false);
const applying = ref(false);
const downloading = ref(false);
const mosaicBlock = ref(8);
const report = ref<Report | null>(null);

const mosaicOptions = computed(() => [
  { label: t("pdfRedact.mosaicFine"), value: 4 },
  { label: t("pdfRedact.mosaicMedium"), value: 8 },
  { label: t("pdfRedact.mosaicCoarse"), value: 16 },
]);

const pageUrl = computed(() => `${apiBase}/pdf-redact/page/${session.value}/${current.value}?dpi=${PREVIEW_DPI}`);
const pageMarks = computed(() => marks.value.filter((mark) => mark.page === current.value));

function thumbUrl(pageNo: number) {
  return `${apiBase}/pdf-redact/page/${session.value}/${pageNo}?dpi=${THUMB_DPI}`;
}

/** 换文档时标记和撤销历史一起作废，否则撤销会把上一个 PDF 的框带回来。 */
function resetMarks() {
  marks.value = [];
  selectedId.value = null;
  history = createMarkHistory();
}

async function onFileSelected(f: File) {
  if (f.size > MAX_UPLOAD_BYTES) {
    useToast().add({ title: t("pdfRedact.tooLarge"), color: "warning" });
    uploaderKey.value += 1;
    return;
  }

  uploading.value = true;
  progress.value = 0;
  try {
    const fd = new FormData();
    fd.append("file", f);
    const resp = await axios.post("/api/v1/pdf-redact/open", fd, {
      onUploadProgress: (evt) => {
        progress.value = evt.total ? Math.round((evt.loaded / evt.total) * 100) : 0;
      },
    });
    session.value = resp.data.session;
    originalName.value = resp.data.original_name;
    pageCount.value = resp.data.page_count;
    current.value = 1;
    zoom.value = 1;
    resetMarks();
    report.value = null;
  } catch (e) {
    showError(e);
    uploaderKey.value += 1;
  } finally {
    uploading.value = false;
  }
}

function onCreate(box: MarkBox) {
  const mark: RedactMark = { ...box, id: nextMarkId(), source: "manual" };
  history.push(marks.value);
  marks.value.push(mark);
  selectedId.value = mark.id;
}

function onUpdate(id: string, box: MarkBox) {
  const index = marks.value.findIndex((mark) => mark.id === id);
  if (index < 0) return;
  history.push(marks.value);
  marks.value[index] = { ...marks.value[index], ...box };
}

function removeMark(id: string) {
  history.push(marks.value);
  marks.value = marks.value.filter((mark) => mark.id !== id);
  if (selectedId.value === id) selectedId.value = null;
}

function clearMarks() {
  if (!marks.value.length) return;
  history.push(marks.value);
  marks.value = [];
  selectedId.value = null;
}

function undoMark() {
  const previous = history.undo();
  if (!previous) return;
  marks.value = previous;
  selectedId.value = null;
}

function selectMark(id: string) {
  selectedId.value = id;
  const mark = marks.value.find((item) => item.id === id);
  if (mark) current.value = mark.page;
}

async function onSearch(pattern: string, regex: boolean) {
  if (!session.value) return;
  searching.value = true;
  try {
    const resp = await axios.post("/api/v1/pdf-redact/search", {
      sid: session.value,
      pattern,
      regex,
    });
    const matches = resp.data.matches as ({ text: string } & MarkBox)[];
    const toast = useToast();

    if (!matches.length) {
      const scanned = resp.data.no_text_pages as number[];
      toast.add({
        title: scanned.length ? t("pdfRedact.scannedOnly") : t("pdfRedact.noMatches"),
        color: "warning",
      });
      return;
    }

    const boxes = matches.map(({ page, x, y, w, h }) => ({ page, x, y, w, h }));
    const before = marks.value.length;
    const next = addKeywordMarks(marks.value, boxes);
    if (next !== marks.value) history.push(marks.value);
    marks.value = next;
    current.value = matches[0].page;
    toast.add({
      title: resp.data.truncated
        ? t("pdfRedact.searchTruncated", { n: matches.length })
        : t("pdfRedact.foundCount", { n: marks.value.length - before }),
      color: "success",
    });
  } catch (e) {
    showError(e);
  } finally {
    searching.value = false;
  }
}

async function apply() {
  if (!session.value || !marks.value.length) return;
  applying.value = true;
  try {
    const resp = await axios.post("/api/v1/pdf-redact/apply", {
      sid: session.value,
      marks: marks.value.map(({ page, x, y, w, h }) => ({ page, x, y, w, h })),
      mosaicBlock: mosaicBlock.value,
    });
    report.value = resp.data as Report;
  } catch (e) {
    showError(e);
  } finally {
    applying.value = false;
  }
}

async function download() {
  if (!session.value) return;
  downloading.value = true;
  try {
    const resp = await axios.get(`/api/v1/pdf-redact/download/${session.value}`, { responseType: "blob" });
    const stem = originalName.value.replace(/\.pdf$/i, "") || "document";
    // 后端在响应结束后就删掉整个会话目录，所以这里必须把本地会话一并作废。
    session.value = null;
    downloadBlob(resp.data, `redacted_${stem}.pdf`, t("common.success"));
  } catch (e) {
    showError(e);
  } finally {
    downloading.value = false;
  }
}

/** 释放服务端会话；卸载时用 beacon，浏览器不保证普通请求能发出去。 */
function closeSession(beacon = false) {
  const sid = session.value;
  if (!sid) return;
  session.value = null;
  const body = JSON.stringify({ sid });
  if (beacon && navigator.sendBeacon) {
    navigator.sendBeacon(`${apiBase}/pdf-redact/close`, new Blob([body], { type: "application/json" }));
    return;
  }
  axios.post("/api/v1/pdf-redact/close", { sid }).catch(() => {});
}

function newFile() {
  closeSession();
  uploaderKey.value += 1;
  originalName.value = "";
  pageCount.value = 0;
  current.value = 1;
  zoom.value = 1;
  resetMarks();
  report.value = null;
}

onBeforeUnmount(() => closeSession(true));
</script>
