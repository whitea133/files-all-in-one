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
  <div class="flex flex-col border border-slate-300 bg-[#f2f2f2]">
    <div class="flex items-center justify-between px-4 py-2">
      <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
        标签
      </div>
      <span class="text-[11px] text-slate-400">点击标签以筛选</span>
    </div>
    <div class="max-h-44 overflow-y-auto px-4 pb-4">
      <div class="flex flex-wrap items-start gap-2">
        <button
          v-for="tag in tags"
          :key="tag.id"
          class="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs transition max-w-[200px] cursor-pointer"
          :class="selectedTagIds.includes(tag.id) ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white text-slate-600 hover:border-blue-300 hover:text-blue-700'"
          type="button"
          @click="emit('toggle', tag.id)"
          @contextmenu.prevent="emit('context', { id: tag.id, x: $event.clientX, y: $event.clientY })"
          @mouseenter="(e) => { if (!selectedTagIds.includes(tag.id)) { (e.currentTarget as HTMLButtonElement).classList.add('border-blue-300','text-blue-700') } }"
          @mouseleave="(e) => { if (!selectedTagIds.includes(tag.id)) { (e.currentTarget as HTMLButtonElement).classList.remove('border-blue-300','text-blue-700') } }"
        >
          <span class="truncate">{{ tag.name }}</span>
          <span v-if="tag.usage !== undefined" class="text-[11px] text-slate-400">({{ tag.usage }})</span>
        </button>
      </div>
    </div>
  </div>
</template>
