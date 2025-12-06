<script setup lang="ts">
import type { VirtualFolder } from '@/types/ui'
import folderIcon from '@/components/icons/floder_icon.svg'
import recycleIcon from '@/components/icons/recycle_icon.svg'
import libraryIcon from '@/components/icons/library.svg'

defineProps<{
  openFolders: VirtualFolder[]
  activeFolderId: string | null
}>()

const emit = defineEmits<{
  (e: 'select', folderId: string): void
  (e: 'close', folderId: string): void
  (e: 'context', payload: { id: string; x: number; y: number; index: number }): void
}>()
</script>

<template>
  <div class="flex items-center gap-2 border-b border-slate-200 bg-[#f2f2f2] px-4 py-1.5 overflow-hidden">
    <div class="no-scrollbar flex flex-1 items-center gap-2 overflow-x-auto whitespace-nowrap h-8 pr-4 min-w-0">
      <div
        v-for="folder in openFolders"
        :key="folder.id"
        class="flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm shadow-sm transition hover:border-slate-400 h-8"
        :class="folder.id === activeFolderId ? 'border-blue-400 bg-blue-50 text-blue-800' : 'border-slate-200 bg-white text-slate-800'"
        style="flex: 0 1 clamp(96px, 11vw, 170px); min-width: 96px; max-width: 190px;"
        @contextmenu.prevent="(e) => emit('context', { id: folder.id, x: e.clientX, y: e.clientY, index: openFolders.indexOf(folder) })"
      >
        <button
          class="flex min-w-0 flex-1 items-center gap-2 text-left"
          type="button"
          @click="emit('select', folder.id)"
        >
          <img
            class="h-4 w-4 shrink-0"
            :class="folder.id === activeFolderId ? 'brightness-0 invert-0' : ''"
            :src="folder.icon === 'recycle' ? recycleIcon : folder.icon === 'library' ? libraryIcon : folderIcon"
            alt=""
          />
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
