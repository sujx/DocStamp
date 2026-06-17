<template>
  <div class="pt-3">
    <h2 class="text-2xl font-bold mb-1 text-balance">{{ $t("img2pdf.title") }}</h2>
    <p class="text-sm mb-5 text-pretty text-secondary" >{{ $t("img2pdf.description") }}</p>

    <label class="block mb-4">
      <UButton color="primary" variant="soft" as="span">
        <UIcon name="i-heroicons-photo" class="w-4 h-4 mr-1" />
        {{ $t("common.upload") }}
      </UButton>
      <input type="file" multiple accept=".png,.jpg,.jpeg,.tiff,.tif" class="hidden" @change="onFilesSelected" />
    </label>

    <div v-if="images.length" class="mb-4">
      <p class="text-xs mb-3 text-tertiary" >
        <UIcon name="i-heroicons-arrows-pointing-out" class="w-3.5 h-3.5 inline mr-1" />
        {{ $t("img2pdf.dragHint") }}
      </p>
      <div class="grid gap-3" style="grid-template-columns: repeat(auto-fill, minmax(140px,1fr));">
        <div
          v-for="(img, idx) in images" :key="img.id"
          class="relative rounded-md overflow-hidden border cursor-grab bg-white transition-transform duration-150"
          :class="[{ 'opacity-50 scale-95': dragIdx === idx }, dragOverIdx === idx ? 'border-brand-700' : 'border-default']"
          draggable="true"
          @dragstart="onDragStart(idx)"
          @dragover.prevent="onDragOver(idx)"
          @drop="onDrop(idx)"
          @dragend="dragIdx = null"
        >
          <img :src="img.thumb" class="w-full h-36 object-cover block" />
          <div class="flex items-center justify-center gap-0.5 p-0.5">
            <UButton size="xs" variant="ghost" color="neutral" icon="i-heroicons-chevron-up" :disabled="idx===0" :aria-label="$t('a11y.moveUp')" @click="moveImage(idx,-1)" />
            <span class="text-xs px-1 text-tertiary" >{{ $t("img2pdf.page", { n: idx+1 }) }}</span>
            <UButton size="xs" variant="ghost" color="neutral" icon="i-heroicons-chevron-down" :disabled="idx===images.length-1" :aria-label="$t('a11y.moveDown')" @click="moveImage(idx,1)" />
          </div>
          <UButton size="xs" variant="ghost" color="neutral" icon="i-heroicons-x-mark" :aria-label="$t('a11y.removeFile')" class="!absolute top-1 right-1" @click="removeImage(idx)" />
        </div>
      </div>
    </div>

    <div v-if="images.length" class="p-4 rounded-lg mt-4 bg-surface" >
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <UFormGroup :label="$t('img2pdf.pageSize')">
          <USelect v-model="pageSize" :options="pageSizeOptions" />
        </UFormGroup>
        <UFormGroup :label="$t('img2pdf.filename')">
          <UInput v-model="outputFilename" :placeholder="defaultFilename" />
        </UFormGroup>
      </div>
      <UButton color="primary" :loading="isProcessing" block @click="merge">
        {{ $t("img2pdf.merge") }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const { downloadBlob, showError } = useDownload();

let idCounter = 0;
function todayStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

const images = ref<{id:number;file:File;thumb:string}[]>([]);
const pageSize = ref("original");
const isProcessing = ref(false);
const dragIdx = ref<number|null>(null);
const dragOverIdx = ref<number|null>(null);
const outputFilename = ref("");

const defaultFilename = computed(() => `Merged_${todayStr()}.pdf`);
const pageSizeOptions = [
  { value: "original", label: t("img2pdf.pageSizeOriginal") },
  { value: "a4", label: t("img2pdf.pageSizeA4") },
  { value: "letter", label: t("img2pdf.pageSizeLetter") },
];

function onFilesSelected(evt: Event) {
  const files = (evt.target as HTMLInputElement).files;
  if (!files) return;
  for (const f of files) {
    const reader = new FileReader();
    reader.onload = (e) => {
      images.value.push({ id: ++idCounter, file: f, thumb: e.target!.result as string });
    };
    reader.readAsDataURL(f);
  }
}

function removeImage(idx: number) { images.value.splice(idx, 1); }
function moveImage(idx: number, dir: number) {
  const ni = idx + dir;
  if (ni < 0 || ni >= images.value.length) return;
  const item = images.value.splice(idx, 1)[0];
  images.value.splice(ni, 0, item);
}
function onDragStart(idx: number) { dragIdx.value = idx; }
function onDragOver(idx: number) { dragOverIdx.value = idx; }
function onDrop(idx: number) {
  if (dragIdx.value != null && dragIdx.value !== idx) {
    const item = images.value.splice(dragIdx.value, 1)[0];
    images.value.splice(idx, 0, item);
  }
  dragIdx.value = null;
  dragOverIdx.value = null;
}

async function merge() {
  if (!images.value.length) return;
  isProcessing.value = true;
  try {
    const fd = new FormData();
    for (const img of images.value) fd.append("files", img.file);
    fd.append("order", JSON.stringify([...Array(images.value.length).keys()]));
    fd.append("page_size", pageSize.value);
    const fname = outputFilename.value.trim() || defaultFilename.value;
    fd.append("filename", fname);
    const resp = await axios.post("/api/v1/img2pdf", fd, { responseType: "blob" });
    downloadBlob(resp.data, fname, t("common.success"));
  } catch (e) {
    showError(e);
  } finally { isProcessing.value = false; }
}
</script>
