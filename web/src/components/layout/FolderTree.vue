<script setup lang="ts">
import type { VirtualFolder } from '@/types/ui'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import folderIcon from '@/components/icons/floder_icon.svg'
import recycleIcon from '@/components/icons/recycle_icon.svg'

const props = defineProps<{
  folders: VirtualFolder[]
  selectedId: string | null
}>()

const emit = defineEmits<{
  (e: 'select', folderId: string): void
  (e: 'create'): void
  (e: 'rename', folderId: string): void
  (e: 'delete', folderId: string): void
}>()

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
        <button class="hover:text-blue-600" type="button" @click="emit('create')">创建</button>
      </div>
    </div>
    <div class="mt-2 flex items-center gap-2">
      <input
        v-model="keyword"
        type="text"
        placeholder="搜索虚拟文件夹"
        class="w-full rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
      />
    </div>
    <div class="mt-2 flex-1 overflow-y-auto rounded-md border border-slate-200">
      <button
        v-for="folder in visibleFolders"
        :key="folder.id"
        class="group flex w-full items-center gap-3 px-3 py-2 text-left text-sm transition"
        :class="folder.id === selectedId ? 'bg-blue-50 text-blue-700' : 'text-slate-700 hover:bg-slate-50'"
        type="button"
        @click="emit('select', folder.id)"
        @contextmenu.prevent="openContextMenu($event, folder.id)"
      >
        <img
          class="h-4 w-4 shrink-0"
          :src="folder.icon === 'recycle' ? recycleIcon : folderIcon"
          alt=""
        />
        <span class="flex-1 truncate">{{ folder.name }}</span>
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
