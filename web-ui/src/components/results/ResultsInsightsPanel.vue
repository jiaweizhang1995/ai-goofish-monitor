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

// Detail dialog content
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
  <!-- LEFT cluster (KPIs + 详细统计) — single row, never wraps -->
  <div class="flex items-center gap-4 flex-shrink-0">
    <!-- KPI 1 — Total -->
    <div class="flex items-baseline gap-1 whitespace-nowrap">
      <span class="text-base font-extrabold tabular-nums tracking-tight text-slate-900">{{ totalCount }}</span>
      <span class="text-[10px] uppercase tracking-[0.2em] text-slate-400 font-bold">{{ t('results.insights.totalLabel') }}</span>
    </div>

    <!-- KPI 2 — Recommended (vermillion accent) -->
    <div class="flex items-baseline gap-1 whitespace-nowrap">
      <span class="text-base font-extrabold tabular-nums tracking-tight text-rose-600">{{ recommendedCountVal }}</span>
      <span class="text-[10px] uppercase tracking-[0.2em] text-slate-400 font-bold">{{ t('results.insights.recommendedLabel') }}</span>
    </div>

    <!-- KPI 3 — Avg price -->
    <div class="flex items-baseline gap-1 whitespace-nowrap">
      <span class="text-base font-extrabold tabular-nums tracking-tight text-slate-900">
        {{ avgPrice ? `¥${Number(avgPrice).toLocaleString()}` : '—' }}
      </span>
      <span class="text-[10px] uppercase tracking-[0.2em] text-slate-400 font-bold">{{ t('results.insights.avgLabel') }}</span>
    </div>

    <!-- 详细统计 -->
    <button
      type="button"
      @click="open = true"
      class="inline-flex items-center gap-1 px-2 h-7 rounded-sm border border-rose-200 text-rose-600 hover:bg-rose-50 hover:border-rose-300 text-[11px] font-bold tracking-wide transition-colors flex-shrink-0"
      :title="t('results.insights.detailButton')"
    >
      <BarChart3 class="w-3.5 h-3.5" />
      {{ t('results.insights.detailButton') }}
    </button>
  </div>

  <!-- 详细统计 Dialog -->
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

      <section class="mt-2">
        <p class="text-[10px] uppercase tracking-[0.2em] text-slate-400 font-bold mb-2">{{ t('results.insights.trendSection') }}</p>
        <div class="rounded-sm border border-slate-200 bg-slate-50/40 p-3">
          <PriceTrendChart :points="insights?.daily_trend || []" />
        </div>
      </section>

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
