<template>
  <footer class="mt-16 border-t border-default bg-surface">
    <div class="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-10 sm:flex-row sm:justify-between sm:px-6">
      <div class="max-w-xs">
        <div class="flex items-center gap-2">
          <span class="seal-dot">印</span>
          <span class="font-official text-base font-extrabold text-primary">鹊随金印</span>
        </div>
        <p class="mt-2 text-xs leading-relaxed text-tertiary">{{ $t("landing.footer.tagline") }}</p>
      </div>

      <div class="flex flex-wrap gap-14">
        <div>
          <b class="mb-3 block text-[13px] text-primary">{{ $t("landing.footer.toolsTitle") }}</b>
          <NuxtLink
            v-for="tool in toolLinks"
            :key="tool.to"
            :to="tool.to"
            class="mb-2 block text-[13px] text-tertiary no-underline transition-colors duration-150 hover:text-brand-600"
          >{{ tool.label }}</NuxtLink>
        </div>

        <div>
          <b class="mb-3 block text-[13px] text-primary">{{ $t("landing.footer.resourcesTitle") }}</b>
          <a
            href="/GBT9704-2012.pdf"
            target="_blank"
            class="mb-2 block text-[13px] text-tertiary no-underline transition-colors duration-150 hover:text-brand-600"
          >{{ $t("landing.footer.standard") }}</a>
          <NuxtLink to="/tools" class="mb-2 block text-[13px] text-tertiary no-underline transition-colors duration-150 hover:text-brand-600">{{ $t("landing.footer.allTools") }}</NuxtLink>
          <NuxtLink to="/status" class="mb-2 block text-[13px] text-tertiary no-underline transition-colors duration-150 hover:text-brand-600">{{ $t("landing.footer.stats") }}</NuxtLink>
        </div>
      </div>
    </div>

    <div class="border-t border-subtle px-4 py-4 text-center text-[12px] text-tertiary sm:px-6">
      {{ $t("landing.footer.copyright") }}
      <template v-if="icp"> · {{ icp }}</template>
      ·
      <a
        :href="`mailto:${contact}`"
        class="text-tertiary no-underline transition-colors duration-150 hover:text-brand-600"
      >{{ contact }}</a>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { TOOLS } from "~/composables/tools.config";

const { t } = useI18n();

const FOOTER_KEYS = ["md2docx", "pdf-redact", "format-docx", "pdf-merge", "pdf-tools"];

const toolLinks = computed(() =>
  FOOTER_KEYS.map((key) => {
    const tool = TOOLS.find((x) => x.key === key)!;
    return { to: tool.to, label: t(tool.label) };
  }),
);

const icp = computed(() => t("landing.footer.icp"));
const contact = computed(() => t("landing.footer.contact"));
</script>