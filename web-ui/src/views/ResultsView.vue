<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useResults } from '@/composables/useResults'
import ResultsFilterBar from '@/components/results/ResultsFilterBar.vue'
import ResultsGrid from '@/components/results/ResultsGrid.vue'
import ResultsInsightsPanel from '@/components/results/ResultsInsightsPanel.vue'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { ChevronsDownUp, ChevronsUpDown } from 'lucide-vue-next'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const { t } = useI18n()

const {
  files,
  selectedFile,
  results,
  insights,
  filters,
  isLoading,
  error,
  refreshResults,
  exportSelectedResults,
  deleteSelectedFile,
  toggleItemBlock,
  blacklistKeywords,
  isSavingBlacklist,
  saveBlacklistRules,
  fileOptions,
  isFileOptionsReady,
} = useResults()

const isDeleteDialogOpen = ref(false)
const isBlacklistDialogOpen = ref(false)
const blacklistDraft = ref('')

// 全局 AI 分析展开/收起 切换 (默认展开)
const expandAllAi = ref(true)
function toggleExpandAll() {
  expandAllAi.value = !expandAllAi.value
}

const selectedTaskLabel = computed(() => {
  if (!selectedFile.value || fileOptions.value.length === 0) return null
  const match = fileOptions.value.find((option) => option.value === selectedFile.value)
  if (!match) return null
  return match.taskName || null
})

const recommendedCount = computed(() => {
  return (results.value || []).filter((item) => item?.ai_analysis?.is_recommended === true).length
})

const deleteConfirmText = computed(() => {
  return selectedTaskLabel.value
    ? t('results.filters.deleteDialogWithTask', { task: selectedTaskLabel.value })
    : t('results.filters.deleteDialogFallback')
})

function openDeleteDialog() {
  if (!selectedFile.value) {
    toast({
      title: t('results.filters.noResultToDelete'),
      variant: 'destructive',
    })
    return
  }
  isDeleteDialogOpen.value = true
}

function openBlacklistDialog() {
  if (!selectedFile.value) {
    toast({
      title: t('results.filters.noResultSelected'),
      variant: 'destructive',
    })
    return
  }
  blacklistDraft.value = blacklistKeywords.value.join('\n')
  isBlacklistDialogOpen.value = true
}

function handleExportResults() {
  if (!selectedFile.value) {
    toast({
      title: t('results.filters.noResultToExport'),
      variant: 'destructive',
    })
    return
  }
  exportSelectedResults()
}

async function handleDeleteResults() {
  if (!selectedFile.value) return
  try {
    await deleteSelectedFile(selectedFile.value)
    toast({ title: t('results.filters.resultDeleted') })
  } catch (e) {
    toast({
      title: t('results.filters.deleteFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isDeleteDialogOpen.value = false
  }
}

function parseBlacklistKeywords(input: string) {
  return input
    .split(/[\n,，]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

async function handleSaveBlacklistRules() {
  try {
    await saveBlacklistRules(parseBlacklistKeywords(blacklistDraft.value))
    toast({ title: t('results.filters.blacklistSaved') })
    isBlacklistDialogOpen.value = false
  } catch (e) {
    toast({
      title: t('results.filters.blacklistSaveFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}
</script>

<template>
  <div>
    <!-- Sticky header: single row, no wrap. h-12 (48px) -->
    <header class="sticky top-0 z-30 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 mb-4 bg-white/85 backdrop-blur border-b border-slate-200">
      <div class="h-12 flex items-center gap-3 min-w-0">
        <!-- LEFT: KPIs + 详细统计 -->
        <ResultsInsightsPanel
          :insights="insights"
          :selected-task-label="selectedTaskLabel"
          :recommended-count="recommendedCount"
        />

        <!-- 全部展开/收起 -->
        <button
          type="button"
          class="inline-flex items-center gap-1 px-2 h-7 rounded-sm border border-slate-200 text-slate-600 hover:border-slate-900 hover:text-slate-900 text-[11px] font-bold tracking-wide transition-colors flex-shrink-0"
          :title="expandAllAi ? t('results.controls.collapseAllAi') : t('results.controls.expandAllAi')"
          @click="toggleExpandAll"
        >
          <ChevronsDownUp v-if="expandAllAi" class="w-3.5 h-3.5" />
          <ChevronsUpDown v-else class="w-3.5 h-3.5" />
          {{ expandAllAi ? t('results.controls.collapseAllAi') : t('results.controls.expandAllAi') }}
        </button>

        <!-- Divider -->
        <div class="h-5 w-px bg-slate-200 flex-shrink-0"></div>

        <!-- MIDDLE+RIGHT: 任务 + 筛选 + 排序 + 操作 -->
        <ResultsFilterBar
          :files="files"
          :file-options="fileOptions"
          :is-ready="isFileOptionsReady"
          v-model:selectedFile="selectedFile"
          v-model:aiRecommendedOnly="filters.ai_recommended_only"
          v-model:keywordRecommendedOnly="filters.keyword_recommended_only"
          v-model:includeHidden="filters.include_hidden"
          v-model:sortBy="filters.sort_by"
          v-model:sortOrder="filters.sort_order"
          :is-loading="isLoading"
          @refresh="refreshResults"
          @manage-blacklist="openBlacklistDialog"
          @export="handleExportResults"
          @delete="openDeleteDialog"
        />
      </div>
    </header>

    <div v-if="error" class="app-alert-error mb-4" role="alert">
      <strong class="font-bold">{{ t('common.error') }}</strong>
      <span class="block sm:inline">{{ error.message }}</span>
    </div>

    <ResultsGrid :results="results" :is-loading="isLoading" :expand-all="expandAllAi" @toggle-block="toggleItemBlock" />

    <Dialog v-model:open="isDeleteDialogOpen">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>{{ t('results.filters.deleteDialogTitle') }}</DialogTitle>
          <DialogDescription>
            {{ deleteConfirmText }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isDeleteDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button variant="destructive" :disabled="isLoading" @click="handleDeleteResults">
            {{ t('results.filters.confirmDelete') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="isBlacklistDialogOpen">
      <DialogContent class="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>{{ t('results.filters.blacklistDialogTitle') }}</DialogTitle>
          <DialogDescription>
            {{ t('results.filters.blacklistDialogDescription') }}
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-2">
          <label class="text-sm font-medium text-slate-700">
            {{ t('results.filters.blacklistRulesLabel') }}
          </label>
          <Textarea
            v-model="blacklistDraft"
            class="min-h-[180px]"
            :placeholder="t('results.filters.blacklistRulesPlaceholder')"
          />
          <p class="text-xs leading-5 text-slate-500">
            {{ t('results.filters.blacklistRulesHint') }}
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isBlacklistDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button :disabled="isSavingBlacklist" @click="handleSaveBlacklistRules">
            {{ t('results.filters.confirmBlacklistSave') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
