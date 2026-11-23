<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
    <PageHeader
      :title="$t('status.title')"
      :description="$t('status.description')"
    />

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-4">
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div v-for="i in 2" :key="'sum-' + i" class="card">
          <UiSkeletonBlock width="5rem" height="0.75rem" class="mb-3" />
          <UiSkeletonBlock width="6rem" height="2rem" />
        </div>
      </div>
      <div class="card">
        <UiSkeletonBlock width="7rem" height="1rem" class="mb-4" />
        <UiSkeletonBlock height="20rem" />
      </div>
    </div>

    <!-- No data state -->
    <div v-else-if="!data || data.total === 0" class="py-16 text-center">
      <div class="icon-badge mx-auto mb-4">
        <UIcon name="i-heroicons-chart-bar" class="size-[18px]" />
      </div>
      <p class="mb-4 text-sm text-secondary">{{ $t("status.noData") }}</p>
      <UButton
        :label="$t('status.seedData')"
        :loading="seeding"
        color="primary"
        @click="seedData"
      />
    </div>

    <!-- Dashboard content -->
    <template v-else>
      <!-- Stat cards: 数字本身，不加装饰条 -->
      <div class="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div class="card">
          <p class="text-[13px] text-secondary">{{ $t("status.totalCalls") }}</p>
          <p class="mt-2 text-[32px] font-medium leading-none tabular-nums text-primary">{{ data.total.toLocaleString() }}</p>
          <p class="mt-2 text-[12px] tabular-nums text-tertiary">{{ $t("status.days", { n: data.days }) }}</p>
        </div>
        <div class="card">
          <p class="text-[13px] text-secondary">{{ $t("status.visitors") }}</p>
          <p class="mt-2 text-[32px] font-medium leading-none tabular-nums text-primary">{{ data.unique_visitors.toLocaleString() }}</p>
          <p class="mt-2 text-[12px] tabular-nums text-tertiary">{{ $t("status.days", { n: data.days }) }}</p>
        </div>
      </div>

      <!-- 主图：模块调用分布（占两栏），旁边是同一份数据的占比列表 -->
      <div class="mb-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div class="card lg:col-span-2">
          <h3 class="mb-4 border-b border-subtle pb-3 text-[15px] font-medium text-primary">
            {{ $t("status.byModule") }}
          </h3>
          <VChart :option="barOption" autoresize class="w-full" style="height: 360px" />
        </div>

        <div class="card">
          <h3 class="mb-4 border-b border-subtle pb-3 text-[15px] font-medium text-primary">
            {{ $t("status.modulePie") }}
          </h3>
          <ul class="space-y-2">
            <li v-for="row in shareRows" :key="row.key" class="flex items-center gap-3">
              <span class="w-24 shrink-0 truncate text-[12px] text-secondary">{{ row.label }}</span>
              <span class="h-1.5 min-w-0 flex-1 overflow-hidden rounded-full bg-raised">
                <span class="share-fill block h-1.5 rounded-full" :class="{ 'share-fill--lead': row.lead }" :style="{ width: row.value + '%' }" />
              </span>
              <span class="w-10 shrink-0 text-right text-[12px] tabular-nums text-primary">{{ row.value }}%</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- 趋势：比主图小一档，只有一条线 -->
      <div class="card">
        <h3 class="mb-4 border-b border-subtle pb-3 text-[15px] font-medium text-primary">
          {{ $t("status.dailyTrend") }}
        </h3>
        <VChart :option="lineOption" autoresize class="w-full" style="height: 240px" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, ref } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, LegendComponent, MarkPointComponent, TitleComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

// Register ECharts modules (tree-shakeable)
use([BarChart, LineChart, GridComponent, LegendComponent, MarkPointComponent, TitleComponent, TooltipComponent, CanvasRenderer]);

interface ModuleStat {
  module: string;
  label: string;
  count: number;
}

interface DailyPoint {
  date: string;
  count: number;
}

interface StatsData {
  total: number;
  by_module: ModuleStat[];
  daily_trend: DailyPoint[];
  unique_visitors: number;
  days: number;
}

const loading = ref(true);
const seeding = ref(false);
const data = ref<StatsData | null>(null);

const { t } = useI18n();

// 图表取色一律走 CSS 变量，页面里不留字面量色值。
// 三个 option 只在数据到位后（客户端）才被求值，SSR 阶段图表分支不渲染。
function palette() {
  const styles = getComputedStyle(document.documentElement);
  const read = (name: string) => styles.getPropertyValue(name).trim();
  return {
    ink: read("--color-text-secondary"),
    faint: read("--color-text-tertiary"),
    grid: read("--color-border-subtle"),
    accent: read("--color-brand-600"),
    surface: read("--color-surface"),
  };
}

const rankedModules = computed(() =>
  [...(data.value?.by_module || [])]
    .filter((m) => m.count > 0)
    .sort((a, b) => b.count - a.count),
);

const SHARE_TOP = 8;

const shareRows = computed(() => {
  const ranked = rankedModules.value;
  const total = ranked.reduce((sum, m) => sum + m.count, 0);
  if (!total) return [];
  const pct = (n: number) => Math.max(2, Math.round((n / total) * 100));
  const head = ranked.slice(0, SHARE_TOP).map((m, i) => ({
    key: m.module,
    label: m.label,
    value: pct(m.count),
    lead: i === 0,
  }));
  const rest = ranked.slice(SHARE_TOP);
  if (!rest.length) return head;
  return [
    ...head,
    {
      key: "other",
      label: t("status.otherModules", { n: rest.length }),
      value: pct(rest.reduce((sum, m) => sum + m.count, 0)),
      lead: false,
    },
  ];
});

const barOption = computed(() => {
  const c = palette();
  const modules = rankedModules.value;
  const leader = modules[0]?.module;
  return {
    tooltip: { trigger: "axis" as const, axisPointer: { type: "shadow" as const } },
    grid: { left: 104, right: 24, top: 8, bottom: 24 },
    xAxis: {
      type: "value" as const,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: c.grid } },
      axisLabel: { color: c.faint, fontSize: 11 },
    },
    yAxis: {
      type: "category" as const,
      data: modules.map((m) => m.label).reverse(),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: c.ink, fontSize: 12 },
    },
    series: [{
      type: "bar",
      data: modules.map((m) => ({
        value: m.count,
        itemStyle: { color: m.module === leader ? c.accent : c.ink, opacity: m.module === leader ? 1 : 0.32 },
      })).reverse(),
      barMaxWidth: 16,
    }],
  };
});

const lineOption = computed(() => {
  const c = palette();
  const trend = data.value?.daily_trend || [];
  const peak = trend.reduce((max, d) => (d.count > max ? d.count : max), 0);
  return {
    tooltip: { trigger: "axis" as const },
    grid: { left: 48, right: 24, top: 16, bottom: 24 },
    xAxis: {
      type: "category" as const,
      data: trend.map((d) => d.date.slice(5)), // MM-DD
      boundaryGap: false,
      axisLine: { lineStyle: { color: c.grid } },
      axisTick: { show: false },
      axisLabel: { color: c.faint, fontSize: 11 },
    },
    yAxis: {
      type: "value" as const,
      minInterval: 1,
      splitLine: { lineStyle: { color: c.grid } },
      axisLabel: { color: c.faint, fontSize: 11 },
    },
    series: [{
      type: "line",
      data: trend.map((d) => d.count),
      smooth: true,
      symbol: "circle",
      symbolSize: 6,
      showSymbol: false,
      lineStyle: { color: c.ink, width: 2 },
      itemStyle: { color: c.ink },
      areaStyle: { color: c.ink, opacity: 0.06 },
      // 唯一一处强调色：最忙的那天
      markPoint: peak
        ? {
            symbol: "circle",
            symbolSize: 8,
            itemStyle: { color: c.accent },
            label: { show: false },
            data: [{ coord: [trend.findIndex((d) => d.count === peak), peak] }],
          }
        : undefined,
    }],
  };
});

// ── Seed test data ──────────────────────────────────────────────────

async function seedData() {
  seeding.value = true;
  try {
    await axios.post("/api/v1/stats/seed");
    const resp = await axios.get("/api/v1/stats/overview");
    if (resp.data?.data) {
      data.value = resp.data.data;
    }
  } catch (e) {
    console.error("Failed to seed data:", e);
  } finally {
    seeding.value = false;
  }
}

// ── Data fetching ──────────────────────────────────────────────────

onMounted(async () => {
  try {
    const resp = await axios.get("/api/v1/stats/overview");
    if (resp.data?.data) {
      data.value = resp.data.data;
    }
  } catch (e) {
    console.error("Failed to load stats:", e);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.share-fill {
  background: var(--color-text-secondary);
  opacity: 0.35;
}

.share-fill--lead {
  background: var(--color-brand-600);
  opacity: 1;
}
</style>
