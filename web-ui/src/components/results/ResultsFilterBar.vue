<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { RefreshCcw, ListFilter, Download, Trash2, ChevronsUpDown, EyeOff } from 'lucide-vue-next'

interface FileOption {
  value: string
  label: string
  taskName?: string
}

interface Props {
  files: string[]
  fileOptions?: FileOption[]
  selectedFile: string | null
  aiRecommendedOnly: boolean
  keywordRecommendedOnly: boolean
  includeHidden: boolean
  sortBy: 'crawl_time' | 'publish_time' | 'price' | 'keyword_hit_count'
  sortOrder: 'asc' | 'desc'
  isLoading: boolean
  isReady: boolean
}

const props = defineProps<Props>()
const { t } = useI18n()

const options = computed(() => {
  if (!props.isReady) return []
  if (props.fileOptions && props.fileOptions.length > 0) return props.fileOptions
  return props.files.map((file) => ({ value: file, label: file }))
})

const selectedLabel = computed(() => {
  if (!props.isReady) return t('results.filters.loadingTaskNames')
  if (options.value.length === 0) return t('results.filters.noResults')
  if (!props.selectedFile) return t('results.filters.chooseResult')
  const match = options.value.find((option) => option.value === props.selectedFile)
  return match ? match.label : t('results.filters.taskNameLabel', { task: t('common.unnamed') })
})

const isSelectDisabled = computed(() => !props.isReady || options.value.length === 0)

const emit = defineEmits<{
  (e: 'update:selectedFile', value: string): void
  (e: 'update:aiRecommendedOnly', value: boolean): void
  (e: 'update:keywordRecommendedOnly', value: boolean): void
  (e: 'update:includeHidden', value: boolean): void
  (e: 'update:sortBy', value: 'crawl_time' | 'publish_time' | 'price' | 'keyword_hit_count'): void
  (e: 'update:sortOrder', value: 'asc' | 'desc'): void
  (e: 'refresh'): void
  (e: 'export'): void
  (e: 'delete'): void
  (e: 'manage-blacklist'): void
}>()

type FilterMode = 'all' | 'ai' | 'keyword'

const filterMode = computed<FilterMode>(() => {
  if (props.aiRecommendedOnly) return 'ai'
  if (props.keywordRecommendedOnly) return 'keyword'
  return 'all'
})

function setFilterMode(mode: FilterMode | string) {
  const m = mode as FilterMode
  emit('update:aiRecommendedOnly', m === 'ai')
  emit('update:keywordRecommendedOnly', m === 'keyword')
}

function toggleHidden() {
  emit('update:includeHidden', !props.includeHidden)
}

function toggleSortOrder() {
  emit('update:sortOrder', props.sortOrder === 'asc' ? 'desc' : 'asc')
}
</script>

<template>
  <!-- Wraps all scoping + actions; sits in parent flex bar as single flex-1 item.
       Never wraps internally — overflow-x-auto as safety net at <1280px. -->
  <div class="flex items-center gap-2 flex-1 min-w-0 overflow-hidden">

    <!-- 任务 -->
    <span class="text-[10px] uppercase tracking-[0.2em] text-slate-400 font-bold flex-shrink-0">{{ t('results.filters.taskShort') }}</span>
    <Select
      :model-value="props.selectedFile || undefined"
      @update:model-value="(value) => emit('update:selectedFile', value as string)"
    >
      <SelectTrigger class="!w-[180px] h-7 text-xs font-semibold border-slate-200 rounded-sm flex-shrink-0" :disabled="isSelectDisabled">
        <span class="truncate">{{ selectedLabel }}</span>
      </SelectTrigger>
      <SelectContent>
        <SelectItem v-for="option in options" :key="option.value" :value="option.value">
          {{ option.label }}
        </SelectItem>
      </SelectContent>
    </Select>

    <!-- 筛选 mode (single Select replacing 4 pills) -->
    <Select
      :model-value="filterMode"
      @update:model-value="(value) => setFilterMode(value as string)"
    >
      <SelectTrigger class="!w-[120px] h-7 text-xs font-semibold border-slate-200 rounded-sm flex-shrink-0">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">{{ t('results.filters.tabAll') }}</SelectItem>
        <SelectItem value="ai">{{ t('results.filters.aiOnly') }}</SelectItem>
        <SelectItem value="keyword">{{ t('results.filters.keywordOnly') }}</SelectItem>
      </SelectContent>
    </Select>

    <!-- 已屏蔽 toggle (small icon) -->
    <button
      type="button"
      class="h-7 w-7 grid place-items-center rounded-sm border transition-colors flex-shrink-0"
      :class="props.includeHidden ? 'bg-slate-900 border-slate-900 text-white' : 'border-slate-200 text-slate-500 hover:border-slate-900'"
      :title="t('results.filters.includeHidden')"
      :aria-label="t('results.filters.includeHidden')"
      @click="toggleHidden"
    >
      <EyeOff class="w-3.5 h-3.5" />
    </button>

    <!-- 排序 -->
    <Select
      :model-value="props.sortBy"
      @update:model-value="(value) => emit('update:sortBy', value as any)"
    >
      <SelectTrigger class="!w-[120px] h-7 text-xs font-semibold border-slate-200 rounded-sm flex-shrink-0">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="crawl_time">{{ t('results.filters.sortByCrawlTime') }}</SelectItem>
        <SelectItem value="publish_time">{{ t('results.filters.sortByPublishTime') }}</SelectItem>
        <SelectItem value="price">{{ t('results.filters.sortByPrice') }}</SelectItem>
        <SelectItem value="keyword_hit_count">{{ t('results.filters.sortByKeywordHits') }}</SelectItem>
      </SelectContent>
    </Select>
    <button
      type="button"
      class="h-7 w-7 grid place-items-center rounded-sm border border-slate-200 text-slate-600 hover:border-slate-900 transition-colors flex-shrink-0"
      :title="props.sortOrder === 'desc' ? t('results.filters.desc') : t('results.filters.asc')"
      @click="toggleSortOrder"
    >
      <ChevronsUpDown class="w-3.5 h-3.5" />
    </button>

    <!-- 弹性占位, 把操作推到最右 -->
    <div class="flex-1 min-w-0"></div>

    <!-- 操作 icons -->
    <div class="flex items-center gap-1 flex-shrink-0">
      <button
        type="button"
        class="w-7 h-7 grid place-items-center rounded-sm border border-slate-200 text-slate-600 hover:border-slate-900 transition-colors disabled:opacity-40"
        :disabled="props.isLoading"
        :title="t('common.refresh')"
        :aria-label="t('common.refresh')"
        @click="emit('refresh')"
      >
        <RefreshCcw class="w-3.5 h-3.5" :class="props.isLoading ? 'animate-spin' : ''" />
      </button>
      <button
        type="button"
        class="w-7 h-7 grid place-items-center rounded-sm border border-slate-200 text-slate-600 hover:border-slate-900 transition-colors disabled:opacity-40"
        :disabled="props.isLoading || !props.selectedFile"
        :title="t('results.filters.manageBlacklist')"
        :aria-label="t('results.filters.manageBlacklist')"
        @click="emit('manage-blacklist')"
      >
        <ListFilter class="w-3.5 h-3.5" />
      </button>
      <button
        type="button"
        class="w-7 h-7 grid place-items-center rounded-sm border border-slate-200 text-slate-600 hover:border-slate-900 transition-colors disabled:opacity-40"
        :disabled="props.isLoading || !props.selectedFile"
        :title="t('results.filters.exportCsv')"
        :aria-label="t('results.filters.exportCsv')"
        @click="emit('export')"
      >
        <Download class="w-3.5 h-3.5" />
      </button>
      <button
        type="button"
        class="w-7 h-7 grid place-items-center rounded-sm border border-rose-200 text-rose-600 hover:bg-rose-50 transition-colors disabled:opacity-40"
        :disabled="props.isLoading || !props.selectedFile"
        :title="t('results.filters.deleteResult')"
        :aria-label="t('results.filters.deleteResult')"
        @click="emit('delete')"
      >
        <Trash2 class="w-3.5 h-3.5" />
      </button>
    </div>
  </div>
</template>
