<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ResultItem } from '@/types/result.d.ts'
import { ExternalLink, ChevronDown, ChevronUp, EyeOff, Eye, TrendingUp, TrendingDown, Sparkles } from 'lucide-vue-next'
import { formatDateTime } from '@/i18n'

interface Props {
  item: ResultItem
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'toggle-block', item: ResultItem): void
}>()
const { t } = useI18n()

const info = props.item.商品信息
const seller = props.item.卖家信息
const ai = props.item.ai_analysis
const priceInsight = props.item.price_insight

// 推荐分数 + 单点颜色
const matchScore = computed(() => ai?.value_score ?? 0)
const isRecommended = computed(() => ai?.is_recommended === true)

const recoDotClass = computed(() => {
  const s = matchScore.value
  if (s >= 80) return 'bg-emerald-500'   // jade
  if (s >= 50) return 'bg-amber-500'     // amber
  return 'bg-rose-500'                    // vermillion (non-recommend)
})

const recoLabelText = computed(() => {
  if (ai?.is_recommended === true) return t('results.card.strongRecommend')
  if (ai?.is_recommended === false) return t('results.card.notRecommended')
  return t('results.card.pending')
})

const imageUrl = info.商品图片列表?.[0] || info.商品主图链接 || ''
const crawlTime = props.item.爬取时间
  ? formatDateTime(props.item.爬取时间, { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  : t('common.unknown')

const isHidden = computed(() => props.item._effective_hidden === true || props.item._status === 'hidden')
const isRuleHidden = computed(() => props.item._hidden_reason === 'rule')
const canToggleBlock = computed(() => props.item._hidden_reason !== 'rule' && props.item._hidden_reason !== 'expired')
const hiddenLabel = computed(() => {
  if (props.item._hidden_reason === 'rule') return t('results.card.blacklisted')
  if (props.item._hidden_reason === 'expired') return t('results.card.expired')
  return t('results.card.hidden')
})

const sellerName = computed(() =>
  (seller?.卖家昵称 || info.卖家昵称 || t('results.card.anonymous')) as string
)

const expanded = ref(false)
const hasReason = computed(() => Boolean(ai?.reason && ai.reason.trim().length > 0))
const priceDiff = computed(() => {
  const own = Number(String(info.当前售价).replace(/[^\d.]/g, '')) || 0
  const avg = priceInsight?.market_avg_price ? Number(priceInsight.market_avg_price) : null
  if (!own || avg == null) return null
  return own - avg
})
</script>

<template>
  <article
    class="listing-card group relative flex flex-col overflow-hidden rounded-sm border border-slate-200 bg-white transition-all duration-150 hover:border-slate-900 hover:shadow-[inset_0_0_0_1px_rgb(15,23,42)]"
    :class="{ 'opacity-50': isHidden }"
  >
    <!-- Image 16:9 -->
    <a
      :href="info.商品链接"
      target="_blank"
      rel="noopener noreferrer"
      class="relative block aspect-[16/9] overflow-hidden bg-slate-100"
    >
      <div v-if="!imageUrl" class="absolute inset-0 bg-slate-200 animate-pulse"></div>
      <img
        v-else
        :src="imageUrl"
        :alt="info.商品标题"
        class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.04]"
        loading="lazy"
      />
      <!-- bottom gradient for legibility -->
      <div class="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-black/40 to-transparent pointer-events-none"></div>

      <!-- hidden overlay -->
      <div v-if="isHidden" class="absolute inset-0 bg-black/30 flex items-center justify-center">
        <span class="text-white/90 text-xs font-semibold uppercase tracking-wider">{{ hiddenLabel }}</span>
      </div>

      <!-- top-left chop: 优选 (jade green) -->
      <div v-if="isRecommended && !isHidden" class="absolute top-2 left-2">
        <span class="inline-block border border-emerald-600 bg-white/85 px-1.5 py-0.5 text-[9px] font-extrabold leading-none uppercase tracking-[0.18em] text-emerald-700">
          {{ t('results.card.curated') }} · RECOMMENDED
        </span>
      </div>
      <div v-if="isRuleHidden" class="absolute top-2 left-2">
        <span class="inline-block border border-slate-700 bg-slate-900/80 px-1.5 py-0.5 text-[9px] font-extrabold leading-none uppercase tracking-[0.18em] text-white">
          {{ t('results.card.blacklisted') }}
        </span>
      </div>

      <!-- top-right icon actions -->
      <div class="absolute top-2 right-2 flex gap-1">
        <button
          v-if="canToggleBlock"
          type="button"
          @click.prevent="emit('toggle-block', props.item)"
          :aria-label="isHidden ? t('results.card.unblock') : t('results.card.block')"
          class="w-7 h-7 grid place-items-center rounded-sm bg-white/85 text-slate-700 hover:bg-white hover:text-slate-900 shadow-sm transition-colors"
        >
          <EyeOff v-if="!isHidden" class="w-3.5 h-3.5" />
          <Eye v-else class="w-3.5 h-3.5" />
        </button>
        <span
          class="w-7 h-7 grid place-items-center rounded-sm bg-white/85 text-slate-700 group-hover:bg-white shadow-sm"
          :title="t('results.card.detail')"
        >
          <ExternalLink class="w-3.5 h-3.5" />
        </span>
      </div>
    </a>

    <!-- Body -->
    <div class="px-3 pt-2.5 pb-2 flex flex-col">
      <!-- Title 1 line -->
      <a
        :href="info.商品链接"
        target="_blank"
        rel="noopener noreferrer"
        class="text-[13px] font-semibold text-slate-900 hover:text-rose-600 truncate leading-tight"
        :title="info.商品标题"
      >
        {{ info.商品标题 }}
      </a>

      <!-- Price + recommend dot row -->
      <div class="mt-1.5 flex items-end justify-between gap-2">
        <div class="flex items-baseline gap-1 min-w-0">
          <span class="text-xl font-extrabold text-rose-600 tabular-nums tracking-tight">{{ info.当前售价 }}</span>
          <span v-if="info['商品原价']" class="text-[10px] text-slate-400 line-through tabular-nums">{{ info['商品原价'] }}</span>
        </div>
        <div class="flex items-center gap-1.5 shrink-0" :title="recoLabelText">
          <span class="inline-block w-2 h-2 rounded-full" :class="recoDotClass"></span>
          <span class="text-sm font-extrabold text-slate-900 tabular-nums">{{ matchScore }}</span>
          <span class="text-[10px] text-slate-400 font-bold">%</span>
        </div>
      </div>

      <!-- Meta row + expand toggle -->
      <div class="mt-1.5 flex items-center justify-between gap-2 text-[10px] text-slate-500 font-medium">
        <div class="flex items-center gap-1.5 min-w-0">
          <span class="truncate max-w-[110px]">{{ sellerName }}</span>
          <span class="text-slate-300">·</span>
          <span class="tabular-nums whitespace-nowrap">{{ crawlTime }}</span>
        </div>
        <button
          v-if="hasReason || priceInsight?.observation_count"
          type="button"
          @click="expanded = !expanded"
          class="inline-flex items-center gap-0.5 text-[10px] font-bold text-slate-600 hover:text-rose-600 transition-colors"
        >
          {{ expanded ? t('results.card.collapse') : t('results.card.expand') }}
          <ChevronUp v-if="expanded" class="w-3 h-3" />
          <ChevronDown v-else class="w-3 h-3" />
        </button>
      </div>

      <!-- Inline expanded content -->
      <div
        class="grid transition-all duration-200 ease-out"
        :class="expanded ? 'grid-rows-[1fr] mt-2 opacity-100' : 'grid-rows-[0fr] mt-0 opacity-0'"
      >
        <div class="overflow-hidden">
          <!-- divider -->
          <div class="border-t border-slate-100 pt-2">
            <!-- AI 推理 -->
            <div v-if="hasReason" class="mb-2">
              <div class="flex items-center gap-1 mb-1">
                <Sparkles class="w-3 h-3 text-emerald-600" />
                <span class="text-[9px] uppercase tracking-[0.18em] font-extrabold text-slate-400">{{ t('results.card.aiSection') }}</span>
              </div>
              <p class="text-[11px] leading-relaxed text-slate-700">{{ ai?.reason }}</p>
            </div>

            <!-- 价格行情 -->
            <div v-if="priceInsight?.observation_count" class="grid grid-cols-3 gap-1.5">
              <div class="rounded-sm border border-slate-100 bg-slate-50 px-2 py-1.5">
                <div class="flex items-center gap-1 text-[9px] uppercase tracking-wider text-slate-400 font-bold">
                  <TrendingUp class="w-2.5 h-2.5" /> {{ t('results.card.marketAvg') }}
                </div>
                <div class="mt-0.5 text-[12px] font-extrabold text-slate-900 tabular-nums">
                  {{ priceInsight.market_avg_price ? `¥${priceInsight.market_avg_price}` : '—' }}
                </div>
              </div>
              <div class="rounded-sm border border-slate-100 bg-slate-50 px-2 py-1.5">
                <div class="flex items-center gap-1 text-[9px] uppercase tracking-wider text-slate-400 font-bold">
                  <TrendingDown class="w-2.5 h-2.5" /> {{ t('results.card.historicalLow') }}
                </div>
                <div class="mt-0.5 text-[12px] font-extrabold text-slate-900 tabular-nums">
                  {{ priceInsight.min_price ? `¥${priceInsight.min_price}` : '—' }}
                </div>
              </div>
              <div class="rounded-sm border border-slate-100 bg-slate-50 px-2 py-1.5">
                <div class="text-[9px] uppercase tracking-wider text-slate-400 font-bold">
                  {{ t('results.card.diffLabel') }}
                </div>
                <div
                  class="mt-0.5 text-[12px] font-extrabold tabular-nums"
                  :class="priceDiff != null && priceDiff < 0 ? 'text-emerald-600' : 'text-slate-900'"
                >
                  <template v-if="priceDiff != null">{{ priceDiff < 0 ? '−' : '+' }}¥{{ Math.abs(priceDiff).toFixed(0) }}</template>
                  <template v-else>—</template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </article>
</template>
