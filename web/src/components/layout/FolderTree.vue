<script setup lang="ts">
import type { VirtualFolder } from '@/types/ui'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import folderIcon from '@/components/icons/floder_icon.svg'
import recycleIcon from '@/components/icons/recycle_icon.svg'
import libraryIcon from '@/components/icons/library.svg'
import addFolderIcon from '@/components/icons/addFolder_icon.svg'

const props = defineProps<{
  folders: VirtualFolder[]
  selectedId: string | null
  editingId?: string | null
  hoverFolderId?: string | null
  draggingAnchor?: { id: string; folderIds?: string[] } | null
  recycleFolderId?: string | null
}>()

const emit = defineEmits<{
  (e: 'select', folderId: string): void
  (e: 'create'): void
  (e: 'rename', folderId: string): void
  (e: 'delete', folderId: string): void
  (e: 'rename-commit', payload: { id: string; name: string }): void
  (e: 'rename-cancel'): void
  (e: 'anchor-drop', folderId: string): void
  (e: 'anchor-drag-over', folderId: string): void
  (e: 'anchor-drag-leave'): void
}>()

const isDropDisabled = (folder: VirtualFolder) => {
  if (!props.draggingAnchor) return false
  if (props.draggingAnchor.folderIds?.includes(folder.id)) return true
  if (folder.isSystem) return true
  if (props.recycleFolderId && folder.id === props.recycleFolderId) return true
  if (folder.name === '全部资料') return true
  return false
}

const keyword = ref('')
const contextMenu = ref<{ visible: boolean; x: number; y: number; targetId: string | null }>({
  visible: false,
  x: 0,
  y: 0,
  targetId: null,
})

const rootEl = ref<HTMLElement | null>(null)

const visibleFolders = computed(() => {
  if (!keyword.value.trim()) return props.folders
  const key = keyword.value.toLowerCase()
  return props.folders.filter((f) => f.name.toLowerCase().includes(key))
})

function openContextMenu(event: MouseEvent, folderId: string) {
  event.preventDefault()
  emit('select', folderId)
  // 使用视口坐标，避免滚动和父容器裁剪带来的偏移
  const offsetX = event.clientX
  const offsetY = event.clientY
  contextMenu.value = {
    visible: true,
    x: offsetX + 6,
    y: offsetY + 10,
    targetId: folderId,
  }
}

function closeContextMenu() {
  contextMenu.value.visible = false
  contextMenu.value.targetId = null
}

function handleRename() {
  if (!contextMenu.value.targetId) return
  emit('rename', contextMenu.value.targetId)
  closeContextMenu()
}

function handleDelete() {
  if (!contextMenu.value.targetId) return
  emit('delete', contextMenu.value.targetId)
  closeContextMenu()
}

function handleGlobalClick() {
  if (contextMenu.value.visible) closeContextMenu()
}

onMounted(() => {
  document.addEventListener('click', handleGlobalClick)
  document.addEventListener('contextmenu', handleGlobalClick, { capture: true })
})

onUnmounted(() => {
  document.removeEventListener('click', handleGlobalClick)
  document.removeEventListener('contextmenu', handleGlobalClick, { capture: true })
})
</script>

<template>
  <div ref="rootEl" class="relative flex h-full flex-col">
    <div class="flex items-center justify-between">
      <div class="text-sm font-semibold text-slate-700">虚拟文件夹</div>
      <div class="flex items-center gap-3 text-xs text-slate-500">
        <button
          class="hover:text-blue-600 cursor-pointer transition"
          type="button"
          title="创建文件夹"
          @click="emit('create')"
        >
          <img
            class="h-5 w-5 transition"
            :class="'hover:[filter:invert(35%)_sepia(93%)_saturate(1820%)_hue-rotate(201deg)_brightness(95%)_contrast(89%)]'"
            :src="addFolderIcon"
            alt="创建文件夹"
          />
        </button>
      </div>
    </div>
    <div class="mt-2 flex items-center gap-2">
      <input
        v-model="keyword"
        type="text"
        placeholder="搜索虚拟文件夹"
        class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
      />
    </div>
    <div class="mt-2 flex-1 overflow-y-auto rounded-md border border-slate-300 p-1 space-y-1">
      <button
        v-for="folder in visibleFolders"
        :key="folder.id"
        class="group flex w-full items-center gap-2 px-2 py-1.5 text-left text-[13px] leading-5 transition rounded-md min-h-[32px] border border-transparent min-w-0"
        :class="[
          props.editingId === folder.id || folder.id === selectedId
            ? 'bg-[#4072E5] text-white border border-[#2f5cd7] shadow-[0_0_0_1px_rgba(47,92,215,0.35)]'
            : 'text-slate-800 hover:bg-slate-50',
          props.editingId !== folder.id && hoverFolderId === folder.id && !isDropDisabled(folder)
            ? 'bg-blue-50 border border-blue-200 shadow-[0_0_0_2px_rgba(59,130,246,0.25)]'
            : '',
          props.editingId !== folder.id && draggingAnchor && !isDropDisabled(folder) ? 'border-blue-200' : '',
          isDropDisabled(folder) && draggingAnchor ? 'cursor-not-allowed opacity-60 grayscale' : '',
        ]"
        type="button"
        @click="emit('select', folder.id)"
        @contextmenu.prevent="openContextMenu($event, folder.id)"
        @dragover.prevent="emit('anchor-drag-over', folder.id)"
        @dragleave="emit('anchor-drag-leave')"
        @drop.prevent="() => !isDropDisabled(folder) && emit('anchor-drop', folder.id)"
      >
        <img
          class="h-4 w-4 shrink-0"
          :class="folder.id === selectedId ? 'brightness-0 invert' : ''"
          :src="folder.icon === 'recycle' ? recycleIcon : folder.icon === 'library' ? libraryIcon : folderIcon"
          alt=""
        />
        <span v-if="props.editingId !== folder.id" class="flex-1 truncate min-w-0">{{ folder.name }}</span>
        <input
          v-else
          class="folder-rename-input w-full truncate rounded border border-white/70 bg-[#4072E5] px-2 py-1 text-sm outline-none text-white placeholder-white/80"
          :value="folder.name"
          autofocus
          @keydown.enter.stop.prevent="emit('rename-commit', { id: folder.id, name: ($event.target as HTMLInputElement).value })"
          @blur="emit('rename-commit', { id: folder.id, name: ($event.target as HTMLInputElement).value })"
          @keydown.esc.stop.prevent="emit('rename-cancel')"
        />
      </button>
    </div>

    <div
      v-if="contextMenu.visible"
      class="fixed z-50 w-40 rounded-md border border-slate-200 bg-white shadow-lg shadow-slate-200/80"
      :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }"
      @click.stop
    >
      <button
        class="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
        type="button"
        @click="handleRename"
      >
        重命名文件夹
      </button>
      <button
        class="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
        type="button"
        @click="handleDelete"
      >
        删除文件夹
      </button>
    </div>
  </div>
</template>
