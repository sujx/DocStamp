<template>
  <div class="pt-3">
    <h2 class="text-2xl font-bold mb-1 text-balance">{{ $t("properties.title") }}</h2>
    <p class="text-sm mb-5 text-pretty" :style="{ color: 'var(--color-text-secondary)' }">{{ $t("properties.description") }}</p>

    <!-- Mode toggle -->
    <div class="flex gap-4 mb-4">
      <label class="flex items-center gap-1.5 text-sm cursor-pointer" :style="{ color: 'var(--color-text-primary)' }">
        <input type="radio" v-model="batchMode" :value="false" class="accent-green-700" />
        {{ $t("properties.singleUpload") }}
      </label>
      <label class="flex items-center gap-1.5 text-sm cursor-pointer" :style="{ color: 'var(--color-text-primary)' }">
        <input type="radio" v-model="batchMode" :value="true" class="accent-green-700" />
        {{ $t("properties.batchUpload") }}
      </label>
    </div>

    <!-- Upload -->
    <div v-if="batchMode">
      <label class="block mb-4">
        <UButton color="primary" variant="soft" as="span">
          <UIcon name="i-heroicons-document-plus" class="w-4 h-4 mr-1" />
          {{ $t("properties.selectFiles") }}
        </UButton>
        <input type="file" multiple accept=".docx,.xlsx,.pptx" class="hidden" @change="onBatchFiles" />
      </label>
      <div v-if="batchFiles.length" class="flex flex-wrap gap-1.5 mb-4">
        <span
          v-for="(f, i) in batchFiles" :key="i"
          class="inline-flex items-center gap-1 px-2 py-1 text-xs rounded font-medium"
          style="background: rgba(0,138,61,0.07); color: #008a3d;"
        >
          {{ f.name }}
          <button class="hover:text-red-600" @click="batchFiles.splice(i,1)">&times;</button>
        </span>
      </div>
    </div>
    <FileUploader
      v-else
      ref="singleUploader"
      accept=".docx,.xlsx,.pptx"
      icon="i-heroicons-document-text"
      @file-selected="selectedFile = $event"
      @reset="selectedFile = null"
    />

    <!-- Properties form -->
    <div v-if="hasFile" class="p-4 mt-4 rounded-lg" :style="{ backgroundColor: 'var(--color-surface)' }">
      <!-- Time mode -->
      <div class="flex gap-4 mb-4">
        <label class="flex items-center gap-1.5 text-sm cursor-pointer" :style="{ color: 'var(--color-text-primary)' }">
          <input type="radio" v-model="timeMode" value="unified" class="accent-green-700" />
          {{ $t("properties.unifiedTime") }}
        </label>
        <label class="flex items-center gap-1.5 text-sm cursor-pointer" :style="{ color: 'var(--color-text-primary)' }">
          <input type="radio" v-model="timeMode" value="separate" class="accent-green-700" />
          {{ $t("properties.separateTime") }}
        </label>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <UFormGroup :label="$t('properties.creator')">
          <UInput v-model="props.creator" :placeholder="$t('properties.creatorPlaceholder')" />
        </UFormGroup>
        <UFormGroup :label="$t('properties.lastModifiedBy')">
          <UInput v-model="props.lastModifiedBy" :placeholder="$t('properties.lastModifiedByPlaceholder')" />
        </UFormGroup>
        <UFormGroup v-if="timeMode === 'separate'" :label="$t('properties.created')">
          <UInput v-model="props.created" type="datetime-local" />
        </UFormGroup>
        <UFormGroup v-if="timeMode === 'separate'" :label="$t('properties.modified')">
          <UInput v-model="props.modified" type="datetime-local" />
        </UFormGroup>
        <UFormGroup v-if="timeMode === 'unified'" :label="$t('properties.unifiedTimeLabel')" class="md:col-span-2">
          <UInput v-model="props.unifiedTime" type="datetime-local" />
        </UFormGroup>
      </div>

      <UButton color="primary" :loading="isProcessing" block @click="modify">
        {{ $t("properties.modify") }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import FileUploader from "./FileUploader.vue";

const { t } = useI18n();
const { downloadBlob, showError } = useDownload();

const batchMode = ref(false);
const timeMode = ref("unified");
const selectedFile = ref<File | null>(null);
const batchFiles = ref<File[]>([]);
const isProcessing = ref(false);
const props = reactive({
  creator: "",
  lastModifiedBy: "",
  unifiedTime: "",
  created: "",
  modified: "",
});

const hasFile = computed(() => batchMode.value ? batchFiles.value.length > 0 : !!selectedFile.value);

function onBatchFiles(evt: Event) {
  const files = (evt.target as HTMLInputElement).files;
  if (files) batchFiles.value = Array.from(files);
}

async function modify() {
  isProcessing.value = true;
  try {
    const fd = new FormData();
    if (batchMode.value) {
      for (const f of batchFiles.value) fd.append("files", f);
      fd.append("unify_time", "true");
      if (timeMode.value === "unified") {
        fd.append("unified_time", props.unifiedTime);
      } else {
        if (props.created) fd.append("created", props.created);
        if (props.modified) fd.append("modified", props.modified);
      }
      if (props.creator) fd.append("creator", props.creator);
      if (props.lastModifiedBy) fd.append("last_modified_by", props.lastModifiedBy);
      const resp = await axios.post("/api/properties/batch", fd, { responseType: "blob" });
      downloadBlob(resp.data, "batch_modified.zip", t("common.success"));
    } else {
      fd.append("file", selectedFile.value!);
      fd.append("unify_time", String(timeMode.value === "unified"));
      if (timeMode.value === "unified") {
        fd.append("unified_time", props.unifiedTime);
      } else {
        if (props.created) fd.append("created", props.created);
        if (props.modified) fd.append("modified", props.modified);
      }
      if (props.creator) fd.append("creator", props.creator);
      if (props.lastModifiedBy) fd.append("last_modified_by", props.lastModifiedBy);
      const resp = await axios.post("/api/properties", fd, { responseType: "blob" });
      downloadBlob(resp.data, selectedFile.value!.name, t("common.success"));
    }
  } catch (e) {
    showError(e);
  } finally {
    isProcessing.value = false;
  }
}
</script>
