<template>
  <div class="pt-3">
    <h2 class="text-2xl font-bold mb-1 text-balance">{{ $t("pdfEditor.title") }}</h2>
    <p class="text-sm mb-5 text-pretty" :style="{ color: 'var(--color-text-secondary)' }">{{ $t("pdfEditor.description") }}</p>

    <!-- Mode selector -->
    <div class="flex gap-4 mb-4">
      <label v-for="m in modes" :key="m.value" class="flex items-center gap-1.5 text-sm cursor-pointer" :style="{ color: 'var(--color-text-primary)' }">
        <input type="radio" v-model="mode" :value="m.value" class="accent-green-700" />
        {{ m.label }}
      </label>
    </div>

    <FileUploader
      ref="uploader"
      accept=".pdf"
      icon="i-heroicons-document"
      :hint="mode === 'delete' ? $t('pdfEditor.clickToSelect') : mode === 'reorder' ? $t('pdfEditor.dragToReorder') : ''"
      @file-selected="onFileSelected"
      @reset="onReset"
    />

    <!-- Delete mode -->
    <template v-if="mode === 'delete' && pageThumbs.length">
      <div class="mt-4">
        <p class="text-xs mb-3" :style="{ color: 'var(--color-text-tertiary)' }">{{ $t("pdfEditor.clickToSelect") }}</p>
        <div class="grid gap-3" style="grid-template-columns: repeat(auto-fill,minmax(100px,1fr));">
          <div
            v-for="p in pageThumbs" :key="p.page_no"
            class="rounded-md overflow-hidden border-2 cursor-pointer transition-colors duration-150"
            :class="deleteSet.has(p.page_no) ? 'border-red-500' : 'border-neutral-200'"
            @click="toggleDeletePage(p.page_no)"
          >
            <img :src="p.thumb" class="w-full object-contain" style="height:130px; background:#f4f2e4;" @error="(e) => (e.target as HTMLImageElement).style.display='none'" />
            <div class="text-xs text-center py-1" :style="{ backgroundColor: 'var(--color-surface)' }">{{ $t("pdfEditor.page") }} {{ p.page_no }}</div>
          </div>
        </div>
        <p v-if="deleteSet.size" class="text-sm mt-3" :style="{ color: 'var(--color-brand-700)' }">
          {{ $t("pdfEditor.selectedToDelete", { n: deleteSet.size, m: pageThumbs.length - deleteSet.size }) }}
        </p>
      </div>
      <UButton v-if="pageThumbs.length" color="primary" :loading="isProcessing" block class="mt-4" @click="doDelete">
        {{ $t("pdfEditor.deleteBtn") }}
      </UButton>
    </template>

    <!-- Insert mode -->
    <template v-if="mode === 'insert' && pageThumbs.length">
      <div class="mt-4 p-4 rounded-lg" :style="{ backgroundColor: 'var(--color-surface)' }">
        <UFormGroup :label="$t('pdfEditor.insertFile')">
          <FileUploader ref="insertUploader" accept=".pdf" icon="i-heroicons-document" @file-selected="insertFile = $event" @reset="insertFile = null" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4 mt-4">
          <UFormGroup :label="$t('pdfEditor.atPosition')">
            <UInput v-model.number="insertPosition" type="number" :min="0" :max="pageThumbs.length" :placeholder="$t('pdfEditor.atPositionHint')" />
          </UFormGroup>
          <UFormGroup :label="$t('pdfEditor.insertPages')">
            <UInput v-model="insertPagesStr" :placeholder="$t('pdfEditor.insertPagesHint')" />
          </UFormGroup>
        </div>
        <UButton color="primary" :loading="isProcessing" block class="mt-4" @click="doInsert">
          {{ $t("pdfEditor.insertBtn") }}
        </UButton>
      </div>
    </template>

    <!-- Reorder mode -->
    <template v-if="mode === 'reorder' && pageThumbs.length">
      <div class="mt-4">
        <div class="grid gap-3" style="grid-template-columns: repeat(auto-fill,minmax(100px,1fr));">
          <div
            v-for="(p, idx) in pageThumbs" :key="p.page_no"
            class="rounded-md overflow-hidden border cursor-grab bg-white transition-all duration-150"
            :class="{ 'opacity-50 scale-95': dragIdx===idx }"
            :style="dragOverIdx===idx ? { borderColor:'#008a3d' } : { borderColor:'#e8e6d8' }"
            draggable="true"
            @dragstart="onDragStart(idx)" @dragover.prevent="onDragOver(idx)"
            @drop="onDrop(idx)" @dragend="dragIdx=null"
          >
            <img :src="p.thumb" class="w-full object-contain" style="height:130px; background:#f4f2e4;" @error="(e) => (e.target as HTMLImageElement).style.display='none'" />
            <div class="flex items-center justify-between px-1 py-0.5" :style="{ backgroundColor: 'var(--color-surface)' }">
              <UButton size="xs" variant="ghost" color="neutral" icon="i-heroicons-chevron-up" :disabled="idx===0" @click="movePage(idx,-1)" />
              <span class="text-xs text-pretty" :style="{ color: 'var(--color-text-tertiary)' }">{{ idx+1 }}</span>
              <UButton size="xs" variant="ghost" color="neutral" icon="i-heroicons-chevron-down" :disabled="idx===pageThumbs.length-1" @click="movePage(idx,1)" />
            </div>
          </div>
        </div>
      </div>
      <UButton v-if="pageThumbs.length" color="primary" :loading="isProcessing" block class="mt-4" @click="doReorder">
        {{ $t("pdfEditor.reorderBtn") }}
      </UButton>
    </template>

    <p v-if="pageCount !== null" class="text-xs mt-3" :style="{ color: 'var(--color-text-tertiary)' }">{{ $t("pdfEditor.originalPages") }}: {{ pageCount }}</p>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import FileUploader from "./FileUploader.vue";

const { t } = useI18n();
const { downloadBlob, showError } = useDownload();

const modes = [
  { value: "delete", label: t("pdfEditor.modeDelete") },
  { value: "insert", label: t("pdfEditor.modeInsert") },
  { value: "reorder", label: t("pdfEditor.modeReorder") },
];

const mode = ref("delete");
const selectedFile = ref<File | null>(null);
const insertFile = ref<File | null>(null);
const pageCount = ref<number | null>(null);
const pageThumbs = ref<{page_no:number;width:number;height:number;thumb:string}[]>([]);
const deleteSet = ref(new Set<number>());
const insertPosition = ref(0);
const insertPagesStr = ref("");
const isProcessing = ref(false);
const dragIdx = ref<number|null>(null);
const dragOverIdx = ref<number|null>(null);

async function onFileSelected(f: File) {
  selectedFile.value = f;
  deleteSet.value = new Set();
  try {
    const fd = new FormData();
    fd.append("file", f);
    const resp = await axios.post("/api/pdf-editor/info", fd);
    pageCount.value = resp.data.total_pages;
    pageThumbs.value = resp.data.pages;
  } catch (e: any) {
    showError(e);
  }
}

function onReset() {
  selectedFile.value = null;
  pageCount.value = null;
  pageThumbs.value = [];
}

function toggleDeletePage(n: number) {
  const s = new Set(deleteSet.value);
  s.has(n) ? s.delete(n) : s.add(n);
  deleteSet.value = s;
}

function movePage(idx: number, dir: number) {
  const ni = idx + dir;
  if (ni < 0 || ni >= pageThumbs.value.length) return;
  const item = pageThumbs.value.splice(idx, 1)[0];
  pageThumbs.value.splice(ni, 0, item);
}
function onDragStart(idx: number) { dragIdx.value = idx; }
function onDragOver(idx: number) { dragOverIdx.value = idx; }
function onDrop(idx: number) {
  if (dragIdx.value != null && dragIdx.value !== idx) {
    const item = pageThumbs.value.splice(dragIdx.value, 1)[0];
    pageThumbs.value.splice(idx, 0, item);
  }
  dragIdx.value = null; dragOverIdx.value = null;
}

async function doDelete() {
  if (!selectedFile.value || !deleteSet.value.size) return;
  isProcessing.value = true;
  try {
    const fd = new FormData();
    fd.append("file", selectedFile.value);
    fd.append("pages", JSON.stringify([...deleteSet.value]));
    const resp = await axios.post("/api/pdf-editor/delete", fd, { responseType: "blob" });
    downloadBlob(resp.data, `edited_${selectedFile.value.name}`, t("common.success"));
  } catch (e) { showError(e); } finally { isProcessing.value = false; }
}

async function doInsert() {
  if (!selectedFile.value || !insertFile.value) {
    useToast().add({ title: t("pdfEditor.insertFileRequired"), color: "warning" });
    return;
  }
  isProcessing.value = true;
  try {
    const fd = new FormData();
    fd.append("file", selectedFile.value);
    fd.append("insert_file", insertFile.value);
    fd.append("at_position", String(insertPosition.value));
    if (insertPagesStr.value.trim()) fd.append("insert_pages", JSON.stringify(insertPagesStr.value.split(",").map(s=>parseInt(s.trim()))));
    const resp = await axios.post("/api/pdf-editor/insert", fd, { responseType: "blob" });
    downloadBlob(resp.data, `merged_${selectedFile.value.name}`, t("common.success"));
  } catch (e) { showError(e); } finally { isProcessing.value = false; }
}

async function doReorder() {
  if (!selectedFile.value) return;
  isProcessing.value = true;
  try {
    const fd = new FormData();
    fd.append("file", selectedFile.value);
    fd.append("order", JSON.stringify(pageThumbs.value.map(p => p.page_no)));
    const resp = await axios.post("/api/pdf-editor/reorder", fd, { responseType: "blob" });
    downloadBlob(resp.data, `reordered_${selectedFile.value.name}`, t("common.success"));
  } catch (e) { showError(e); } finally { isProcessing.value = false; }
}
</script>
