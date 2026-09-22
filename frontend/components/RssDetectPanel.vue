<template>
  <div class="card bg-surface border-default">
    <!-- Input -->
    <div class="flex flex-col sm:flex-row gap-3">
      <UInput
        v-model="url"
        :placeholder="$t('rssDetect.placeholder')"
        size="lg"
        class="flex-1"
        :disabled="detecting"
        @keyup.enter="doDetect"
      />
      <UButton color="primary" size="lg" :loading="detecting" @click="doDetect">
        <UIcon name="i-heroicons-magnifying-glass" class="w-4 h-4 mr-1.5" />
        {{ detecting ? $t("rssDetect.detecting") : $t("rssDetect.detect") }}
      </UButton>
    </div>

    <!-- Error -->
    <div v-if="errorMsg" class="mt-4 p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700">
      {{ errorMsg }}
    </div>

    <!-- Empty result -->
    <div v-if="results && results.length === 0" class="mt-6 text-center py-8 text-tertiary text-sm">
      <UIcon name="i-heroicons-magnifying-glass" class="w-10 h-10 mx-auto mb-2" />
      <p>{{ $t("rssDetect.noFeeds") }}</p>
    </div>

    <!-- Results -->
    <div v-if="results && results.length > 0" class="mt-6 space-y-2">
      <p class="text-sm text-secondary mb-3">{{ $t("rssDetect.foundFeeds", { n: results.length }) }}</p>
      <div
        v-for="(feed, i) in results" :key="i"
        class="flex items-center gap-3 p-3 rounded-lg bg-muted group"
      >
        <UIcon
          :name="feed.type === 'atom' ? 'i-heroicons-globe-alt' : 'i-heroicons-signal'"
          class="w-5 h-5 text-brand-700 shrink-0"
        />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium truncate text-primary">{{ feed.title || feed.url }}</p>
          <p class="text-xs text-tertiary truncate">{{ feed.url }}</p>
        </div>
        <div class="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150">
          <UButton size="xs" variant="ghost" color="neutral" @click="copyUrl(feed.url)">
            <UIcon name="i-heroicons-clipboard" class="w-3.5 h-3.5" />
            {{ $t("rssDetect.copy") }}
          </UButton>
          <UButton size="xs" variant="ghost" color="neutral" @click="openUrl(feed.url)">
            <UIcon name="i-heroicons-arrow-top-right-on-square" class="w-3.5 h-3.5" />
            {{ $t("rssDetect.open") }}
          </UButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";

const { t } = useI18n();
const toast = useToast();
const { extractError } = useError();

const url = ref("");
const detecting = ref(false);
const results = ref<{ url: string; title: string; type: string }[] | null>(null);
const errorMsg = ref("");

async function doDetect() {
  const u = url.value.trim();
  if (!u) return;
  errorMsg.value = "";
  detecting.value = true;
  results.value = null;

  try {
    const resp = await axios.post("/api/v1/rss-detect", { url: u });
    results.value = resp.data.data.feeds;
  } catch (e: any) {
    errorMsg.value = await extractError(e, "Detection failed");
  } finally {
    detecting.value = false;
  }
}

async function copyUrl(feedUrl: string) {
  await navigator.clipboard.writeText(feedUrl);
  toast.add({ title: t("rssDetect.copied"), color: "success" });
}

function openUrl(feedUrl: string) {
  window.open(feedUrl, "_blank");
}
</script>
