<template>
  <div class="card bg-surface border-default">
    <FileUploader :accept="'.pdf'" :max-size="100" :label="$t('common.upload')" @file-selected="onFileSelected" />
    <template v-if="file">
      <UFormGroup :label="$t('pageDecorate.mode')" class="mt-4">
        <USelect v-model="mode" :options="modeOptions" size="sm" />
      </UFormGroup>
      <UFormGroup :label="$t('pageDecorate.text')" class="mt-3">
        <UInput v-model="textTemplate" size="sm" :placeholder="mode === 'page_number' ? '{n} / {total}' : $t('pageDecorate.textPlaceholder')" />
        <p class="text-xs mt-1 text-tertiary"><code>{n}</code> = {{ $t("pageDecorate.currentPage") }}, <code>{total}</code> = {{ $t("pageDecorate.totalPages") }}</p>
      </UFormGroup>
      <div class="grid grid-cols-2 gap-3 mt-3">
        <UFormGroup :label="$t('pageDecorate.position')"><USelect v-model="position" :options="positionOptions" size="sm" /></UFormGroup>
        <UFormGroup :label="$t('pageDecorate.fontSize')"><UInput v-model.number="fontSize" type="number" size="sm" :min="6" :max="72" /></UFormGroup>
      </div>
      <div class="grid grid-cols-2 gap-3 mt-3">
        <UFormGroup :label="$t('pageDecorate.color')"><UInput v-model="color" type="color" size="sm" class="h-9 w-16" /></UFormGroup>
        <UFormGroup :label="$t('pageDecorate.startNumber')"><UInput v-model.number="startNumber" type="number" size="sm" :min="1" /></UFormGroup>
      </div>
    </template>
    <div class="mt-6 flex gap-3">
      <UButton color="primary" :disabled="!file || !textTemplate" :loading="decorating" @click="decorate">
        <UIcon name="i-heroicons-document-check" class="w-4 h-4 mr-1.5" /> {{ decorating ? $t("common.processing") : $t("pageDecorate.decorate") }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
const { t } = useI18n(); const toast = useToast();
const file = ref<File | null>(null); const mode = ref("page_number"); const textTemplate = ref("{n}"); const position = ref("bottom-center"); const fontSize = ref(10); const color = ref("#000000"); const startNumber = ref(1); const decorating = ref(false);
const modeOptions = computed(() => [{ label: t("pageDecorate.pageNumber"), value: "page_number" }, { label: t("pageDecorate.header"), value: "header" }, { label: t("pageDecorate.footer"), value: "footer" }]);
const positionOptions = computed(() => [{ label: t("pageDecorate.topLeft"), value: "top-left" }, { label: t("pageDecorate.topCenter"), value: "top-center" }, { label: t("pageDecorate.topRight"), value: "top-right" }, { label: t("pageDecorate.bottomLeft"), value: "bottom-left" }, { label: t("pageDecorate.bottomCenter"), value: "bottom-center" }, { label: t("pageDecorate.bottomRight"), value: "bottom-right" }]);
function onFileSelected(f: File) { file.value = f; }
async function decorate() {
  if (!file.value) return; decorating.value = true;
  try {
    const fd = new FormData(); fd.append("file", file.value);
    fd.append("params", JSON.stringify({ mode: mode.value, text: textTemplate.value, position: position.value, font_size: fontSize.value, color: color.value, start_number: startNumber.value }));
    const resp = await axios.post("/api/v1/page-decorate", fd, { responseType: "blob" });
    const url = URL.createObjectURL(resp.data); const a = document.createElement("a"); a.href = url; a.download = `decorated_${file.value.name}`; a.click(); URL.revokeObjectURL(url);
    toast.add({ title: t("common.success"), color: "success" });
  } catch (e: any) { const msg = await e.response?.data?.text?.() || e.message; toast.add({ title: msg ? JSON.parse(msg).error || msg : e.message, color: "error" }); }
  finally { decorating.value = false; }
}
</script>

