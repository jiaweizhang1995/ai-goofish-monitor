<script setup lang="ts">
import type { ResultItem } from '@/types/result.d.ts'
import { useI18n } from 'vue-i18n'
import ResultCard from './ResultCard.vue'

interface Props {
  results: ResultItem[]
  isLoading: boolean
  expandAll?: boolean
}

withDefaults(defineProps<Props>(), { expandAll: true })
const { t } = useI18n()

const emit = defineEmits<{
  (e: 'toggle-block', item: ResultItem): void
}>()
const skeletonItems = Array.from({ length: 12 }, (_, index) => index)
</script>

<template>
  <div :aria-busy="isLoading">
    <div
      v-if="isLoading"
      class="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
      aria-live="polite"
    >
      <div
        v-for="item in skeletonItems"
        :key="item"
        class="rounded-sm border border-slate-200 bg-white overflow-hidden"
      >
        <div class="aspect-[16/9] animate-pulse bg-slate-200/70"></div>
        <div class="space-y-2 p-3">
          <div class="h-4 w-4/5 animate-pulse rounded bg-slate-200/70"></div>
          <div class="flex items-center justify-between">
            <div class="h-6 w-1/3 animate-pulse rounded bg-slate-200/70"></div>
            <div class="h-4 w-12 animate-pulse rounded bg-slate-200/70"></div>
          </div>
          <div class="h-3 w-1/2 animate-pulse rounded bg-slate-200/70"></div>
        </div>
      </div>
    </div>
    <div v-else-if="results.length === 0" class="rounded-sm border border-slate-200 bg-white text-center py-12 text-slate-500">
      {{ t('results.grid.empty') }}
    </div>
    <div v-else class="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <ResultCard
        v-for="item in results"
        :key="item.商品信息.商品ID"
        :item="item"
        :expand-all="expandAll"
        @toggle-block="emit('toggle-block', $event)"
      />
    </div>
  </div>
</template>
