<template>
  <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <h2 class="text-2xl font-bold mb-1.5 text-balance text-primary" >
      {{ $t("status.title") }}
    </h2>
    <p class="text-sm mb-8 text-pretty text-secondary" >
      {{ $t("status.description") }}
    </p>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-4">
      <!-- Summary skeleton -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div
          v-for="i in 2" :key="'sum-'+i"
          class="rounded-lg p-5 animate-pulse"
          :style="{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border-default)', borderTop: '3px solid var(--color-border-default)', boxShadow: 'var(--shadow-card)' }"
        >
          <div class="h-3 w-20 rounded mb-2 bg-muted"  />
          <div class="h-8 w-20 rounded mb-2 bg-muted"  />
          <div class="h-3 w-24 rounded bg-muted"  />
        </div>
      </div>
      <!-- Chart skeleton row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div
          v-for="i in 2" :key="'chart-'+i"
          class="rounded-lg p-5 animate-pulse"
          :style="{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border-default)', boxShadow: 'var(--shadow-card)' }"
        >
          <div class="h-4 w-28 rounded mb-4 pb-3 border-b border-subtle" >
            <div class="h-4 w-28 rounded bg-muted"  />
          </div>
          <div class="h-80 rounded bg-muted"  />
        </div>
      </div>
      <!-- Line chart skeleton -->
      <div
        class="rounded-lg p-5 animate-pulse"
        :style="{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border-default)', boxShadow: 'var(--shadow-card)' }"
      >
        <div class="h-4 w-28 rounded mb-4 pb-3 border-b border-subtle" >
          <div class="h-4 w-28 rounded bg-muted"  />
        </div>
        <div class="h-72 rounded bg-muted"  />
      </div>
    </div>

    <!-- No data state -->
    <div v-else-if="!data || data.total === 0" class="py-20 text-center">
      <UIcon name="i-heroicons-chart-bar" class="size-12 mx-auto mb-4 text-tertiary"  />
      <p class="text-sm mb-4 text-secondary" >{{ $t("status.noData") }}</p>
      <UButton
        :label="$t('status.seedData')"
        :loading="seeding"
        color="brand"
        size="sm"
        @click="seedData"
      />
    </div>

    <!-- Dashboard content -->
    <template v-else>
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <div
          class="rounded-lg p-5"
          :style="{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border-default)', borderTop: '3px solid var(--color-brand-700)', boxShadow: 'var(--shadow-card)' }"
        >
          <p class="text-xs font-medium uppercase mb-2 text-tertiary" >
            {{ $t("status.totalCalls") }}
          </p>
          <p class="text-3xl font-bold tabular-nums text-brand-700" >{{ data.total.toLocaleString() }}</p>
          <p class="text-xs mt-2 text-tertiary" >{{ $t("status.days", { n: data.days }) }}</p>
        </div>
        <div
          class="rounded-lg p-5"
          :style="{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border-default)', borderTop: '3px solid var(--color-brand-700)', boxShadow: 'var(--shadow-card)' }"
        >
          <p class="text-xs font-medium uppercase mb-2 text-tertiary" >
            {{ $t("status.visitors") }}
          </p>
          <p class="text-3xl font-bold tabular-nums text-brand-700" >{{ data.unique_visitors.toLocaleString() }}</p>
          <p class="text-xs mt-2 text-tertiary" >{{ $t("status.days", { n: data.days }) }}</p>
        </div>
      </div>

      <!-- Charts row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <!-- Bar chart: module distribution -->
        <div
          class="rounded-lg p-5"
          :style="{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border-default)', boxShadow: 'var(--shadow-card)' }"
        >
          <h3 class="text-sm font-semibold mb-4 pb-3 border-b" :style="{ color: 'var(--color-text-primary)', borderColor: 'var(--color-border-subtle)' }">
            {{ $t("status.byModule") }}
          </h3>
          <VChart :option="barOption" autoresize class="w-full" style="height: 320px" />
        </div>

        <!-- Pie chart: module share -->
        <div
          class="rounded-lg p-5"
          :style="{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border-default)', boxShadow: 'var(--shadow-card)' }"
        >
          <h3 class="text-sm font-semibold mb-4 pb-3 border-b" :style="{ color: 'var(--color-text-primary)', borderColor: 'var(--color-border-subtle)' }">
            {{ $t("status.modulePie") }}
          </h3>
          <VChart :option="pieOption" autoresize class="w-full" style="height: 320px" />
        </div>
      </div>

      <!-- Line chart: daily trend -->
      <div
        class="rounded-lg p-5"
        :style="{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border-default)', boxShadow: 'var(--shadow-card)' }"
      >
        <h3 class="text-sm font-semibold mb-4 pb-3 border-b" :style="{ color: 'var(--color-text-primary)', borderColor: 'var(--color-border-subtle)' }">
          {{ $t("status.dailyTrend") }}
        </h3>
        <VChart :option="lineOption" autoresize class="w-full" style="height: 300px" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onMounted, ref } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { BarChart, LineChart, PieChart } from "echarts/charts";
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

// Register ECharts modules (tree-shakeable)
use([BarChart, LineChart, PieChart, GridComponent, LegendComponent, TitleComponent, TooltipComponent, CanvasRenderer]);

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

// ── Chart options (computed) ──────────────────────────────────────

const barOption = computed(() => ({
  tooltip: { trigger: "axis" as const },
  grid: { left: 100, right: 20, top: 10, bottom: 20 },
  xAxis: {
    type: "value" as const,
    axisLabel: { color: "#757265" },
  },
  yAxis: {
    type: "category" as const,
    data: (data.value?.by_module || []).map((m) => m.label).reverse(),
    axisLabel: { color: "#5c5c5c", fontSize: 12 },
  },
  series: [{
    type: "bar",
    data: (data.value?.by_module || []).map((m) => m.count).reverse(),
    itemStyle: {
      color: "#008a3d",
      borderRadius: [0, 4, 4, 0],
    },
    barMaxWidth: 28,
  }],
}));

const pieOption = computed(() => ({
  tooltip: { trigger: "item" as const },
  legend: {
    orient: "vertical" as const,
    right: 10,
    top: "center",
    textStyle: { color: "#5c5c5c", fontSize: 11 },
    itemWidth: 8,
    itemHeight: 8,
  },
  series: [{
    type: "pie",
    radius: ["40%", "70%"],
    center: ["35%", "50%"],
    data: (data.value?.by_module || []).filter((m) => m.count > 0).map((m) => ({
      name: m.label,
      value: m.count,
    })),
    label: { show: false },
    emphasis: {
      label: { show: true, fontWeight: "bold" },
    },
    itemStyle: { borderRadius: 4, borderColor: "#fff", borderWidth: 2 },
  }],
  color: [
    "#008a3d", "#22c55e", "#4ade80", "#86efac",
    "#f59e0b", "#ef4444", "#3b82f6", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#06b6d4",
    "#84cc16", "#a855f7", "#e11d48", "#0ea5e9",
  ],
}));

const lineOption = computed(() => ({
  tooltip: { trigger: "axis" as const },
  grid: { left: 50, right: 20, top: 10, bottom: 20 },
  xAxis: {
    type: "category" as const,
    data: (data.value?.daily_trend || []).map((d) => d.date.slice(5)), // MM-DD
    axisLabel: { color: "#8c8a7a", fontSize: 11 },
  },
  yAxis: {
    type: "value" as const,
    minInterval: 1,
    axisLabel: { color: "#757265" },
  },
  series: [{
    type: "line",
    data: (data.value?.daily_trend || []).map((d) => d.count),
    smooth: true,
    lineStyle: { color: "#008a3d", width: 2 },
    itemStyle: { color: "#008a3d" },
    areaStyle: {
      color: {
        type: "linear",
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: "rgba(0,138,61,0.15)" },
          { offset: 1, color: "rgba(0,138,61,0.01)" },
        ],
      },
    },
  }],
}));

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
