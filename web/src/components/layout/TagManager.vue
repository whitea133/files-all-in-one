<script setup lang="ts">
import type { TagItem } from '@/types/ui'

defineProps<{
  tags: TagItem[]
  selectedTagIds: string[]
}>()

const emit = defineEmits<{
  (e: 'toggle', tagId: string): void
  (e: 'context', payload: { id: string; x: number; y: number }): void
}>()
</script>

<template>
  <div class="flex flex-col border-t border-slate-200 bg-[#f2f2f2]">
    <div class="flex items-center justify-between px-4 py-2">
      <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
        标签
      </div>
      <span class="text-[11px] text-slate-400">点击标签以筛选</span>
    </div>
    <div class="max-h-44 overflow-y-auto px-4 pb-4">
      <div class="flex flex-wrap gap-2">
        <button
          v-for="tag in tags"
          :key="tag.id"
          class="flex items-center gap-2 rounded-full border px-3 py-1 text-xs transition"
          :class="selectedTagIds.includes(tag.id) ? 'border-blue-400 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'"
          type="button"
          @click="emit('toggle', tag.id)"
          @contextmenu.prevent="emit('context', { id: tag.id, x: $event.clientX, y: $event.clientY })"
        >
          <span class="inline-block h-2 w-2 rounded-full" :class="tag.color ?? 'bg-emerald-400'"></span>
          <span class="truncate">{{ tag.name }}</span>
          <span v-if="tag.usage !== undefined" class="text-[11px] text-slate-400">({{ tag.usage }})</span>
        </button>
      </div>
    </div>
  </div>
</template>
