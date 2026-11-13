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
            class="flex min-h-[44px] items-center text-[13px] text-tertiary no-underline transition-colors duration-150 hover:text-brand-600"
          >{{ tool.label }}</NuxtLink>
        </div>

        <div>
          <b class="mb-3 block text-[13px] text-primary">{{ $t("landing.footer.resourcesTitle") }}</b>
          <a
            href="/GBT9704-2012.pdf"
            target="_blank"
            rel="noopener"
            class="flex min-h-[44px] items-center text-[13px] text-tertiary no-underline transition-colors duration-150 hover:text-brand-600"
          >{{ $t("landing.footer.standard") }}</a>
          <NuxtLink to="/tools" class="flex min-h-[44px] items-center text-[13px] text-tertiary no-underline transition-colors duration-150 hover:text-brand-600">{{ $t("landing.footer.allTools") }}</NuxtLink>
          <NuxtLink to="/status" class="flex min-h-[44px] items-center text-[13px] text-tertiary no-underline transition-colors duration-150 hover:text-brand-600">{{ $t("landing.footer.stats") }}</NuxtLink>
          <NuxtLink to="/guide/pdf-redact" class="flex min-h-[44px] items-center text-[13px] text-tertiary no-underline transition-colors duration-150 hover:text-brand-600">{{ $t("landing.footer.guide") }}</NuxtLink>
        </div>
      </div>
    </div>

    <div class="border-t border-subtle px-4 py-2 text-center text-[12px] text-tertiary sm:px-6">
      {{ $t("landing.footer.copyright") }}
      <template v-if="icp"> · {{ icp }}</template>
      ·
      <a
        :href="`mailto:${contact}`"
        class="inline-flex min-h-[44px] items-center text-tertiary no-underline transition-colors duration-150 hover:text-brand-600"
      >{{ contact }}</a>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { TOOLS, FOOTER_TOOL_KEYS, type ToolDef } from "~/composables/tools.config";

const { t } = useI18n();

const toolLinks = computed(() =>
  FOOTER_TOOL_KEYS.map((key) => TOOLS.find((x) => x.key === key))
    .filter((tool): tool is ToolDef => Boolean(tool))
    .map((tool) => ({ to: tool.to, label: t(tool.label) })),
);

const icp = computed(() => t("landing.footer.icp"));
const contact = computed(() => t("landing.footer.contact"));
</script>
