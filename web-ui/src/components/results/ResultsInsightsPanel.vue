<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ResultInsights } from '@/types/result.d.ts'
import PriceTrendChart from './PriceTrendChart.vue'
import { formatDateTime } from '@/i18n'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { BarChart3 } from 'lucide-vue-next'

const props = defineProps<{
  insights: ResultInsights | null
  selectedTaskLabel?: string | null
  recommendedCount?: number
}>()
const { t } = useI18n()

const open = ref(false)

const totalCount = computed(() => props.insights?.market_summary.sample_count ?? 0)
const recommendedCountVal = computed(() => props.recommendedCount ?? 0)
const avgPrice = computed(() => props.insights?.market_summary.avg_price ?? null)

const latestSnapshotText = computed(() => {
  if (!props.insights?.latest_snapshot_at) return t('results.insights.noSnapshot')
  return formatDateTime(props.insights.latest_snapshot_at, {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
})

// 3 visible KPI on sticky bar (compact)
const kpis = computed(() => [
  { key: 'total', label: t('results.insights.totalLabel'), value: totalCount.value, accent: 'ink' as const },
  { key: 'recommended', label: t('results.insights.recommendedLabel'), value: recommendedCountVal.value, accent: 'vermillion' as const },
  { key: 'avg', label: t('results.insights.avgLabel'), value: avgPrice.value ? `¥${Number(avgPrice.value).toLocaleString()}` : '—', accent: 'ink' as const },
])

// Full stat blocks for the Dialog
const currentStats = computed(() => {
  const m = props.insights?.market_summary
  return [
    { label: t('results.insights.sampleCount', { count: m?.sample_count || 0 }), value: m?.sample_count ?? 0 },
    { label: t('results.insights.currentAvg'), value: m?.avg_price ? `¥${m.avg_price}` : '—' },
    { label: t('results.insights.currentMedian'), value: m?.median_price ? `¥${m.median_price}` : '—' },
    { label: t('results.insights.currentMin'), value: m?.min_price ? `¥${m.min_price}` : '—' },
    { label: t('results.insights.currentMax'), value: m?.max_price ? `¥${m.max_price}` : '—' },
  ]
})

const historyStats = computed(() => {
  const h = props.insights?.history_summary
  return [
    { label: t('results.insights.uniqueItems', { count: h?.unique_items || 0 }), value: h?.unique_items ?? 0 },
    { label: t('results.insights.historyAvg'), value: h?.avg_price ? `¥${h.avg_price}` : '—' },
    { label: t('results.insights.historyMin'), value: h?.min_price ? `¥${h.min_price}` : '—' },
    { label: t('results.insights.historyMax'), value: h?.max_price ? `¥${h.max_price}` : '—' },
  ]
})
</script>

<template>
  <!-- KPI 簇: 在 sticky bar 内部内联渲染 -->
  <div class="flex items-center gap-5">
    <div
      v-for="kpi in kpis"
      :key="kpi.key"
      class="flex items-baseline gap-1.5 whitespace-nowrap"
    >
      <span
        class="text-lg font-extrabold tabular-nums tracking-tight"
        :class="kpi.accent === 'vermillion' ? 'text-rose-600' : 'text-slate-900'"
      >
        {{ kpi.value }}
      </span>
      <span class="text-[10px] uppercase tracking-[0.18em] text-slate-400 font-bold">{{ kpi.label }}</span>
    </div>

    <button
      type="button"
      @click="open = true"
      class="ml-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-sm border border-rose-200 text-rose-600 hover:bg-rose-50 text-[11px] font-bold tracking-wide transition-colors"
      :title="t('results.insights.detailButton')"
    >
      <BarChart3 class="w-3.5 h-3.5" />
      {{ t('results.insights.detailButton') }}
    </button>
  </div>

  <!-- 详细统计 Dialog: 走势 + 当前快照 + 历史快照 -->
  <Dialog v-model:open="open">
    <DialogContent class="sm:max-w-[860px] max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2 text-base">
          <BarChart3 class="w-4 h-4 text-rose-600" />
          {{ t('results.insights.detailTitle') }}
          <span v-if="selectedTaskLabel" class="text-xs font-normal text-slate-500">— {{ selectedTaskLabel }}</span>
        </DialogTitle>
        <DialogDescription>
          {{ t('results.insights.subtitle') }} · {{ t('results.insights.latestSnapshot', { time: latestSnapshotText }) }}
        </DialogDescription>
      </DialogHeader>

      <!-- Trend chart -->
      <section class="mt-2">
        <p class="text-[10px] uppercase tracking-[0.2em] text-slate-400 font-bold mb-2">{{ t('results.insights.trendSection') }}</p>
        <div class="rounded-sm border border-slate-200 bg-slate-50/40 p-3">
          <PriceTrendChart :points="insights?.daily_trend || []" />
        </div>
      </section>

      <!-- Current snapshot -->
      <section class="mt-5">
        <p class="text-[10px] uppercase tracking-[0.2em] text-slate-400 font-bold mb-2">{{ t('results.insights.currentSection') }}</p>
        <div class="grid grid-cols-5 gap-2">
          <article
            v-for="stat in currentStats"
            :key="stat.label"
            class="rounded-sm border border-slate-200 bg-white px-3 py-2"
          >
            <p class="text-[9px] uppercase tracking-wider text-slate-400 font-bold truncate">{{ stat.label }}</p>
            <p class="mt-1 text-sm font-extrabold text-slate-900 tabular-nums">{{ stat.value }}</p>
          </article>
        </div>
      </section>

      <!-- History snapshot -->
      <section class="mt-4 mb-2">
        <p class="text-[10px] uppercase tracking-[0.2em] text-slate-400 font-bold mb-2">{{ t('results.insights.historySection') }}</p>
        <div class="grid grid-cols-4 gap-2">
          <article
            v-for="stat in historyStats"
            :key="stat.label"
            class="rounded-sm border border-slate-200 bg-white px-3 py-2"
          >
            <p class="text-[9px] uppercase tracking-wider text-slate-400 font-bold truncate">{{ stat.label }}</p>
            <p class="mt-1 text-sm font-extrabold text-slate-900 tabular-nums">{{ stat.value }}</p>
          </article>
        </div>
      </section>
    </DialogContent>
  </Dialog>
</template>
