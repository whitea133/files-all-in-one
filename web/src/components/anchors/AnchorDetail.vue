<script setup lang="ts">
import type { AnchorItem } from '@/types/ui'

const props = defineProps<{
  anchor: AnchorItem | null
}>()

const emit = defineEmits<{
  (e: 'untag', tag: string): void
}>()
</script>

<template>
  <div class="flex h-full flex-col bg-slate-50">
    <div class="border-b border-slate-200 px-4 py-3">
      <div class="text-sm font-semibold text-slate-800">文件信息</div>
      <div class="text-xs text-slate-500">点击列表中的资料锚点查看详情</div>
    </div>
    <div v-if="anchor" class="flex-1 overflow-y-auto p-4 space-y-4">
      <div class="space-y-1">
        <div class="text-sm font-semibold text-slate-800">{{ anchor.title }}</div>
        <div class="text-xs text-slate-500">创建者：{{ anchor.creator }}</div>
        <div class="text-xs text-slate-500">更新：{{ anchor.updatedAt }}</div>
      </div>

      <div class="space-y-1">
        <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">摘要</div>
        <p class="rounded-md border border-slate-200 bg-white p-3 text-sm leading-relaxed text-slate-700">
          {{ anchor.summary || '暂无摘要，可从接口或手动输入补全。' }}
        </p>
      </div>

      <div class="space-y-1">
        <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">标签</div>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="tag in anchor.tags"
            :key="tag"
            class="flex items-center gap-1 rounded-full bg-blue-50 px-3 py-1 text-xs text-blue-700"
          >
            <span class="truncate">{{ tag }}</span>
            <button
              class="text-slate-400 hover:text-red-500"
              type="button"
              @click.stop="emit('untag', tag)"
            >
              ×
            </button>
          </span>
          <span v-if="!anchor.tags.length" class="text-xs text-slate-400">暂无标签</span>
        </div>
      </div>

      <div class="space-y-1">
        <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">附件</div>
        <div class="rounded-md border border-dashed border-slate-200 bg-white p-3 text-sm text-slate-600">
          {{ anchor.attachments ? `已有 ${anchor.attachments} 个附件` : '暂无附件' }}
        </div>
      </div>
    </div>
    <div v-else class="flex flex-1 items-center justify-center text-sm text-slate-400">
      未选择资料锚点
    </div>
  </div>
</template>
