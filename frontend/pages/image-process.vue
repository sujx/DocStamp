<template>
  <div class="max-w-3xl mx-auto px-6 py-8">
    <PageHeader :title="$t('imageProcess.title')" :description="$t('imageProcess.description')" />

    <div class="card bg-surface border-default" >
      <FileUploader
        :accept="'.png,.jpg,.jpeg,.tiff,.tif,.webp'"
        :max-size="50"
        :label="$t('common.upload')"
        @file-selected="onFileSelected"
      />

      <template v-if="file">
        <UFormGroup :label="$t('imageProcess.action')" class="mt-4">
          <USelect v-model="action" :options="actionOptions" size="sm" @change="resetForm" />
        </UFormGroup>

        <!-- Resize -->
        <template v-if="action === 'resize'">
          <div class="grid grid-cols-2 gap-3 mt-3">
            <UFormGroup :label="$t('imageProcess.width')">
              <UInput v-model.number="resizeWidth" type="number" size="sm" :placeholder="$t('imageProcess.auto')" />
            </UFormGroup>
            <UFormGroup :label="$t('imageProcess.height')">
              <UInput v-model.number="resizeHeight" type="number" size="sm" :placeholder="$t('imageProcess.auto')" />
            </UFormGroup>
          </div>
          <label class="flex items-center gap-2 mt-2 text-sm cursor-pointer text-secondary" >
            <input v-model="keepAspect" type="checkbox" class="accent-[var(--color-brand-700)]" />
            {{ $t("imageProcess.keepAspect") }}
          </label>
        </template>

        <!-- Crop -->
        <template v-if="action === 'crop'">
          <div class="grid grid-cols-2 gap-3 mt-3">
            <UFormGroup :label="$t('imageProcess.left')">
              <UInput v-model.number="cropLeft" type="number" size="sm" />
            </UFormGroup>
            <UFormGroup :label="$t('imageProcess.top')">
              <UInput v-model.number="cropTop" type="number" size="sm" />
            </UFormGroup>
            <UFormGroup :label="$t('imageProcess.right')">
              <UInput v-model.number="cropRight" type="number" size="sm" />
            </UFormGroup>
            <UFormGroup :label="$t('imageProcess.bottom')">
              <UInput v-model.number="cropBottom" type="number" size="sm" />
            </UFormGroup>
          </div>
        </template>

        <!-- Convert -->
        <template v-if="action === 'convert'">
          <UFormGroup :label="$t('imageProcess.targetFormat')" class="mt-3">
            <USelect v-model="targetFormat" :options="formatOptions" size="sm" />
          </UFormGroup>
        </template>

        <!-- Compress -->
        <template v-if="action === 'compress'">
          <UFormGroup :label="$t('imageProcess.quality')" class="mt-3">
            <UInput v-model.number="compressQuality" type="range" size="sm" :min="1" :max="100" />
            <span class="text-sm ml-2 text-secondary" >{{ compressQuality }}%</span>
          </UFormGroup>
        </template>
      </template>

      <div class="mt-6 flex gap-3">
        <UButton color="primary" :disabled="!file" :loading="processing" @click="process">
          <UIcon name="i-heroicons-photo" class="w-4 h-4 mr-1.5" />
          {{ processing ? $t("common.processing") : $t("imageProcess.process") }}
        </UButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const toast = useToast();

const file = ref<File | null>(null);
const action = ref("resize");
const processing = ref(false);

// Resize
const resizeWidth = ref<number | null>(null);
const resizeHeight = ref<number | null>(null);
const keepAspect = ref(true);

// Crop
const cropLeft = ref(0);
const cropTop = ref(0);
const cropRight = ref<number | null>(null);
const cropBottom = ref<number | null>(null);

// Convert
const targetFormat = ref("png");

// Compress
const compressQuality = ref(80);

const actionOptions = computed(() => [
  { label: t("imageProcess.resize"), value: "resize" },
  { label: t("imageProcess.crop"), value: "crop" },
  { label: t("imageProcess.convert"), value: "convert" },
  { label: t("imageProcess.compress"), value: "compress" },
]);

const formatOptions = [
  { label: "PNG", value: "png" },
  { label: "JPEG", value: "jpeg" },
  { label: "TIFF", value: "tiff" },
];

function onFileSelected(f: File) {
  file.value = f;
}

function resetForm() {
  resizeWidth.value = null;
  resizeHeight.value = null;
  cropRight.value = null;
  cropBottom.value = null;
}

async function process() {
  if (!file.value) return;
  processing.value = true;
  try {
    const fd = new FormData();
    fd.append("file", file.value);

    const params: Record<string, any> = { action: action.value };
    if (action.value === "resize") {
      params.width = resizeWidth.value || 0;
      params.height = resizeHeight.value || 0;
      params.keep_aspect = keepAspect.value ? "true" : "false";
    } else if (action.value === "crop") {
      params.left = cropLeft.value;
      params.top = cropTop.value;
      params.right = cropRight.value || 0;
      params.bottom = cropBottom.value || 0;
    } else if (action.value === "convert") {
      params.target_format = targetFormat.value;
    } else if (action.value === "compress") {
      params.quality = compressQuality.value;
    }

    fd.append("params", JSON.stringify(params));

    const resp = await axios.post("/api/v1/image-process", fd, { responseType: "blob" });
    const url = URL.createObjectURL(resp.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `processed_${file.value.name}`;
    a.click();
    URL.revokeObjectURL(url);
    toast.add({ title: t("common.success"), color: "success" });
  } catch (e: any) {
    const msg = await e.response?.data?.text?.() || e.message;
    toast.add({ title: msg ? JSON.parse(msg).error || msg : e.message, color: "error" });
  } finally {
    processing.value = false;
  }
}
</script>

<style scoped>
.card {
  border: 1px solid;
  border-radius: 10px;
  padding: 24px;
}
</style>
