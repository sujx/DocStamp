<template>
  <div class="pt-3">
    <h2 class="text-2xl font-bold mb-1 text-balance">{{ $t("printSplit.title") }}</h2>
    <p class="text-sm mb-5 text-pretty" :style="{ color: 'var(--color-text-secondary)' }">{{ $t("printSplit.description") }}</p>

    <FileUploader
      ref="uploader"
      accept=".pdf"
      icon="i-heroicons-document"
      @file-selected="selectedFile = $event"
      @reset="onReset"
    />

    <div v-if="selectedFile && !task" class="p-4 mt-4 rounded-lg" :style="{ backgroundColor: 'var(--color-surface)' }">
      <div class="grid grid-cols-2 gap-4 mb-4">
        <UFormGroup :label="$t('printSplit.batchSize')">
          <UInput v-model.number="batchSize" type="number" :min="1" :max="500" />
        </UFormGroup>
        <UFormGroup :label="$t('printSplit.interval')">
          <div class="flex items-center gap-2">
            <UInput v-model.number="intervalVal" type="number" :min="1" class="flex-1" />
            <div class="flex gap-1">
              <UButton size="xs" :variant="intervalUnit==='sec'?'solid':'ghost'" :color="intervalUnit==='sec'?'primary':'neutral'" @click="intervalUnit='sec'">{{ $t("printSplit.seconds") }}</UButton>
              <UButton size="xs" :variant="intervalUnit==='min'?'solid':'ghost'" :color="intervalUnit==='min'?'primary':'neutral'" @click="intervalUnit='min'">{{ $t("printSplit.minutes") }}</UButton>
            </div>
          </div>
        </UFormGroup>
      </div>
      <UButton color="primary" :loading="isSplitting" block @click="startSplit">
        {{ $t("printSplit.startSplit") }}
      </UButton>
    </div>

    <!-- Progress -->
    <div v-if="task" class="p-4 mt-4 rounded-lg" :style="{ backgroundColor: 'var(--color-surface)' }">
      <UProgress :value="downloaded" :max="task.batch_count" color="primary" class="mb-3" />
      <p class="text-sm mb-3" :style="{ color: 'var(--color-text-secondary)' }">
        {{ $t("printSplit.downloaded") }}: {{ downloaded }} / {{ task.batch_count }}
        <span v-if="!allDone && !isPaused" class="ml-2">({{ $t("printSplit.nextDownload") }}: {{ countdown }}s)</span>
        <span v-else-if="isPaused" class="ml-2 font-medium" style="color: #f59e0b;">{{ $t("printSplit.paused") }}</span>
        <span v-else class="ml-2 font-medium" :style="{ color: 'var(--color-brand-700)' }"><UIcon name="i-heroicons-check-circle" class="w-4 h-4 inline" /> {{ $t("printSplit.allDone") }}</span>
      </p>
      <div class="flex gap-2">
        <UButton v-if="!isPaused && !allDone" color="warning" size="sm" @click="pause">{{ $t("printSplit.pause") }}</UButton>
        <UButton v-if="isPaused" color="primary" size="sm" @click="resume">{{ $t("printSplit.resume") }}</UButton>
        <UButton color="error" size="sm" variant="ghost" @click="stop">{{ $t("printSplit.stop") }}</UButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import FileUploader from "./FileUploader.vue";

const { t } = useI18n();

const selectedFile = ref<File | null>(null);
const batchSize = ref(60);
const intervalVal = ref(60);
const intervalUnit = ref("sec");
const isSplitting = ref(false);
const task = ref<any>(null);
const downloaded = ref(0);
const countdown = ref(0);
const isPaused = ref(false);
let timer: ReturnType<typeof setInterval> | null = null;

function onReset() {
  selectedFile.value = null;
  stop();
}

async function startSplit() {
  if (!selectedFile.value) return;
  isSplitting.value = true;
  try {
    const fd = new FormData();
    fd.append("file", selectedFile.value);
    fd.append("batch_size", String(batchSize.value));
    fd.append("interval", String(intervalUnit.value === "min" ? intervalVal.value * 60 : intervalVal.value));
    const resp = await axios.post("/api/print-split", fd);
    task.value = resp.data;
    downloaded.value = 0;
    scheduleNext();
  } catch (e: any) {
    useToast().add({ title: e.response?.data?.error || e.message, color: "error" });
  } finally { isSplitting.value = false; }
}

function scheduleNext() {
  if (!task.value) return;
  const interval = intervalUnit.value === "min" ? intervalVal.value * 60 : intervalVal.value;
  countdown.value = interval;
  timer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0 && !isPaused.value) {
      clearInterval(timer!);
      downloadNext();
    }
  }, 1000);
}

async function downloadNext() {
  if (!task.value || downloaded.value >= task.value.batch_count) return;
  const batchNo = downloaded.value + 1;
  try {
    const resp = await axios.get(`/api/print-split/${task.value.task_id}/batch/${batchNo}`, { responseType: "blob" });
    const url = URL.createObjectURL(resp.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `batch_${batchNo}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    downloaded.value++;
  } catch (e: any) {
    useToast().add({ title: e.response?.data?.error || e.message, color: "error" });
  }
  if (downloaded.value < task.value.batch_count) scheduleNext();
}

const allDone = computed(() => task.value && downloaded.value >= task.value.batch_count);

function pause() { isPaused.value = true; if (timer) clearInterval(timer); }
function resume() { isPaused.value = false; scheduleNext(); }
function stop() {
  if (timer) clearInterval(timer);
  task.value = null;
  isPaused.value = false;
  downloaded.value = 0;
}
</script>
