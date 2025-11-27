<script setup lang="ts">
import type { VirtualFolder } from '@/types/ui'

defineProps<{
  openFolders: VirtualFolder[]
  activeFolderId: string | null
}>()

const emit = defineEmits<{
  (e: 'select', folderId: string): void
  (e: 'close', folderId: string): void
}>()
</script>

<template>
  <div class="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-2 overflow-hidden">
    <div class="shrink-0 text-xs font-medium text-slate-500">已打开文件夹</div>
    <div class="no-scrollbar flex flex-1 items-center gap-2 overflow-x-auto whitespace-nowrap h-9 pr-4 min-w-0">
      <div
        v-for="folder in openFolders"
        :key="folder.id"
        class="flex items-center gap-2 rounded-full border px-3 py-1 text-sm shadow-sm transition hover:border-slate-400"
        :class="folder.id === activeFolderId ? 'border-blue-400 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white text-slate-700'"
        style="flex: 0 1 clamp(100px, 12vw, 180px); min-width: 100px; max-width: 200px;"
      >
        <button
          class="flex min-w-0 flex-1 items-center gap-2 text-left"
          type="button"
          @click="emit('select', folder.id)"
        >
          <span class="inline-block h-2 w-2 rounded-full" :class="folder.color ?? 'bg-blue-400'"></span>
          <span class="truncate">{{ folder.name }}</span>
        </button>
        <button
          class="shrink-0 text-xs text-slate-400 hover:text-slate-600"
          type="button"
          @click="emit('close', folder.id)"
        >
          ×
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.no-scrollbar {
  scrollbar-width: none;
}
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
</style>
