<script setup lang="ts">
import axios from 'axios'
import AnchorDetail from '@/components/anchors/AnchorDetail.vue'
import AnchorTable from '@/components/anchors/AnchorTable.vue'
import FolderTabs from '@/components/layout/FolderTabs.vue'
import FolderTree from '@/components/layout/FolderTree.vue'
import TagManager from '@/components/layout/TagManager.vue'
import type { AnchorItem, TagItem, VirtualFolder } from '@/types/ui'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { computed, onMounted, onUnmounted, ref, watchEffect } from 'vue'

declare global {
  interface Window {
    pywebview?: {
      api?: {
        open_file_dialog?: (folder_id?: number) => Promise<{ files: string[]; folder_id?: number; error?: string }>
        open_file?: (path: string) => Promise<{ success?: boolean; error?: string }>
      }
    }
  }
}

type ApiFolder = {
  id: number
  name: string
  description?: string | null
  create_time: string
  is_system: boolean
}

type ApiAnchor = {
  id: number
  name: string
  path: string
  description: string | null
  is_valid: boolean
  create_time: string
  update_time: string
  virtual_folder_ids: number[]
  tag_ids: number[]
}

type ApiTag = {
  id: number
  name: string
  use_count: number
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
})

const folders = ref<VirtualFolder[]>([])
const anchors = ref<AnchorItem[]>([])
const tags = ref<TagItem[]>([])
const anchorCache = ref<Map<string, AnchorItem[]>>(new Map())
const anchorRequestAbort = ref<AbortController | null>(null)
const allowAutoSelectAnchor = ref(true)
const recycleFolderId = ref<string | null>(null)
const allFolderId = ref<string | null>(null)
const draggingAnchor = ref<{ id: string; folderIds: string[] } | null>(null)
const hoverFolderId = ref<string | null>(null)
const folderTabMenu = ref<{ visible: boolean; x: number; y: number; targetId: string | null; index: number }>({
  visible: false,
  x: 0,
  y: 0,
  targetId: null,
  index: -1,
})
const dialogState = ref<{
  open: boolean
  title: string
  description: string
  value: string
  placeholder: string
  mode: 'description' | 'tag'
  anchorId: string | null
}>({
  open: false,
  title: '',
  description: '',
  value: '',
  placeholder: '',
  mode: 'description',
  anchorId: null,
})
const confirmState = ref<{
  open: boolean
  title: string
  description: string
  onConfirm: (() => Promise<void>) | null
}>({
  open: false,
  title: '',
  description: '',
  onConfirm: null,
})
function handleGlobalClickForRename(event: MouseEvent) {
  const target = event.target as HTMLElement | null
  if (target && target.closest('.folder-rename-input')) return
  handleFolderRenameCancel()
}

const openFolders = ref<VirtualFolder[]>([])
const selectedFolderId = ref<string | null>(null)
const selectedAnchorId = ref<string | null>(null)
const selectedTagIds = ref<string[]>([])
const editingFolderId = ref<string | null>(null)
const editingAnchorId = ref<string | null>(null)
const anchorMenu = ref<{ visible: boolean; x: number; y: number; targetId: string | null }>({
  visible: false,
  x: 0,
  y: 0,
  targetId: null,
})
const tagMenu = ref<{ visible: boolean; x: number; y: number; targetId: string | null }>({
  visible: false,
  x: 0,
  y: 0,
  targetId: null,
})

const tagIdNameMap = ref(new Map<number, string>())
const tagNameIdMap = ref(new Map<string, number>())

const tagNameMap = computed(() => new Map(tags.value.map((t) => [t.id, t.name])))

const filteredAnchors = computed(() => {
  const base = anchors.value
  if (!selectedTagIds.value.length) return base
  const targetNames = selectedTagIds.value
    .map((id) => tagNameMap.value.get(id) ?? id)
    .filter(Boolean)
  return base.filter((item) => targetNames.every((tag) => item.tags.includes(tag)))
})

const selectedAnchor = computed(() =>
  anchors.value.find((item) => item.id === selectedAnchorId.value) || null,
)

function typeFromPath(path: string | null | undefined): string {
  if (!path) return '未知'
  const parts = path.split('.')
  return parts.length > 1 ? (parts.pop() || '文件').toLowerCase() : '文件'
}

function formatDateTime(value: string | Date | null | undefined): string {
  if (!value) return ''
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  const y = date.getFullYear()
  const m = pad(date.getMonth() + 1)
  const d = pad(date.getDate())
  const hh = pad(date.getHours())
  const mm = pad(date.getMinutes())
  const ss = pad(date.getSeconds())
  return `${y}/${m}/${d} ${hh}:${mm}:${ss}`
}

function mapAnchor(apiAnchor: ApiAnchor, folderId: string): AnchorItem {
  const tagNames = apiAnchor.tag_ids
    .map((id) => tagIdNameMap.value.get(id) || `标签#${id}`)
    .filter(Boolean)
  return {
    id: String(apiAnchor.id),
    title: apiAnchor.name,
    creator: '',
    type: typeFromPath(apiAnchor.path),
    folderId,
    folderIds: apiAnchor.virtual_folder_ids.map((id) => String(id)),
    path: apiAnchor.path,
    addedAt: formatDateTime(apiAnchor.create_time),
    updatedAt: formatDateTime(apiAnchor.update_time),
    tags: tagNames,
    summary: apiAnchor.description ?? undefined,
    attachments: undefined,
  }
}

async function refreshTags() {
  const res = await api.get<ApiTag[]>('/tags/popular')
  tagIdNameMap.value = new Map(res.data.map((t) => [t.id, t.name]))
  tagNameIdMap.value = new Map(res.data.map((t) => [t.name, t.id]))
  tags.value = res.data.map((t) => ({ id: String(t.id), name: t.name, usage: t.use_count }))
}

async function loadFolders() {
  const res = await api.get<ApiFolder[]>('/folders')
  const mapped = res.data.map((f) => ({
    id: String(f.id),
    name: f.name,
    description: f.description ?? undefined,
    isSystem: f.is_system,
    icon: f.name === '回收站' ? 'recycle' : f.name === '全部资料' ? 'library' : 'folder',
  })) as VirtualFolder[]
  folders.value = mapped
  recycleFolderId.value = mapped.find((f) => f.name === '回收站')?.id ?? null
  allFolderId.value = mapped.find((f) => f.name === '全部资料')?.id ?? null
  if (!mapped.length) {
    selectedFolderId.value = null
    openFolders.value = []
    return
  }

  const firstFolder = mapped[0]!

  if (!selectedFolderId.value) {
    selectedFolderId.value = firstFolder.id
  } else {
    const current = mapped.find((f) => f.id === selectedFolderId.value)
    if (!current) {
      selectedFolderId.value = firstFolder.id
    }
  }

  const current = mapped.find((f) => f.id === selectedFolderId.value) ?? firstFolder
  if (current && !openFolders.value.find((f) => f.id === current.id)) {
    openFolders.value.push(current)
  }
}

async function loadAnchors(folderId: string, options: { force?: boolean; autoSelect?: boolean } = {}) {
  if (!folderId) return
  const { force = false, autoSelect = true } = options

  const cached = anchorCache.value.get(folderId)
  if (cached && !force) {
    anchors.value = cached
    if (autoSelect) {
      if (!anchors.value.find((a) => a.id === selectedAnchorId.value)) {
        selectedAnchorId.value = anchors.value[0]?.id ?? null
      }
    } else {
      selectedAnchorId.value = null
    }
  }

  if (anchorRequestAbort.value) {
    anchorRequestAbort.value.abort()
  }
  const controller = new AbortController()
  anchorRequestAbort.value = controller

  try {
    const res = await api.get<ApiAnchor[]>(`/folders/${folderId}/anchors`, { signal: controller.signal })
    const mapped = res.data.map((a) => mapAnchor(a, folderId))
    anchors.value = mapped
    anchorCache.value.set(folderId, mapped)
    allowAutoSelectAnchor.value = autoSelect
    if (autoSelect) {
      if (!anchors.value.find((a) => a.id === selectedAnchorId.value)) {
        selectedAnchorId.value = anchors.value[0]?.id ?? null
      }
    } else {
      selectedAnchorId.value = null
    }
  } catch (err: any) {
    if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') return
    console.error('加载锚点失败', err)
  } finally {
    closeAnchorMenu()
  }
}

async function initData() {
  try {
    await refreshTags()
    await loadFolders()
    if (selectedFolderId.value) {
      await loadAnchors(selectedFolderId.value, { force: true, autoSelect: false })
    }
  } catch (err) {
    console.error('初始化数据失败，请检查后端服务是否已启动或接口是否可用', err)
  }
}

function handleFolderSelect(folderId: string) {
  selectedFolderId.value = folderId
  selectedAnchorId.value = null
  allowAutoSelectAnchor.value = false
  const folder = folders.value.find((f) => f.id === folderId)
  if (folder && !openFolders.value.find((f) => f.id === folder.id)) {
    openFolders.value.push(folder)
  }
  loadAnchors(folderId, { autoSelect: false })
}

function handleCloseTab(folderId: string) {
  openFolders.value = openFolders.value.filter((f) => f.id !== folderId)
  if (selectedFolderId.value === folderId) {
    const fallback = openFolders.value[0] ?? folders.value[0] ?? null
    selectedFolderId.value = fallback?.id ?? null
    if (selectedFolderId.value) loadAnchors(selectedFolderId.value, { autoSelect: false })
  }
}

function openFolderTabMenu(payload: { id: string; x: number; y: number; index: number }) {
  folderTabMenu.value = { visible: true, x: payload.x, y: payload.y, targetId: payload.id, index: payload.index }
}

function closeFolderTabMenu() {
  folderTabMenu.value.visible = false
  folderTabMenu.value.targetId = null
  folderTabMenu.value.index = -1
}

function closeOtherFolders() {
  if (!folderTabMenu.value.targetId) return
  openFolders.value = openFolders.value.filter((f) => f.id === folderTabMenu.value.targetId)
  if (selectedFolderId.value !== folderTabMenu.value.targetId) {
    selectedFolderId.value = folderTabMenu.value.targetId
    loadAnchors(selectedFolderId.value, { autoSelect: false })
  }
  closeFolderTabMenu()
}

function closeRightFolders() {
  if (folderTabMenu.value.index < 0) return
  const keep = openFolders.value.slice(0, folderTabMenu.value.index + 1)
  const target = keep[keep.length - 1] ?? null
  openFolders.value = keep
  if (target && selectedFolderId.value !== target.id) {
    selectedFolderId.value = target.id
    loadAnchors(target.id, { autoSelect: false })
  }
  closeFolderTabMenu()
}

function closeAllFolders() {
  openFolders.value = []
  selectedFolderId.value = null
  anchors.value = []
  closeFolderTabMenu()
}

function handleAnchorDragStart(payload: { id: string }) {
  const anchor = anchors.value.find((a) => a.id === payload.id)
  draggingAnchor.value = {
    id: payload.id,
    folderIds: anchor?.folderIds ?? (anchor?.folderId ? [anchor.folderId] : []),
  }
}

function handleAnchorDragEnd() {
  draggingAnchor.value = null
  hoverFolderId.value = null
}

function handleFolderDragOver(folderId: string) {
  hoverFolderId.value = folderId
}

async function handleAnchorDrop(folderId: string) {
  hoverFolderId.value = null
  if (!draggingAnchor.value) return
  const targetFolder = folders.value.find((f) => f.id === folderId)
  if (!targetFolder) return
  if ((targetFolder as any).isSystem || folderId === recycleFolderId.value || folderId === allFolderId.value) {
    window.alert('不能绑定到系统文件夹或回收站/全部资料')
    handleAnchorDragEnd()
    return
  }
  if (draggingAnchor.value.folderIds.includes(folderId)) {
    window.alert('该资料锚点已在此文件夹中')
    handleAnchorDragEnd()
    return
  }
  try {
    await api.post(`/anchors/${draggingAnchor.value.id}/bindFolders`, {
      folder_ids: [Number(folderId)],
    })
    anchorCache.value.forEach((list, key) => {
      const idx = list.findIndex((a) => a.id === draggingAnchor.value?.id)
      if (idx >= 0 && draggingAnchor.value) {
        const anchorEntry = list[idx]
        if (!anchorEntry) return
        const baseFolders = anchorEntry.folderIds ?? (anchorEntry.folderId ? [anchorEntry.folderId] : [])
        const updatedFolderIds = Array.from(new Set([...baseFolders, folderId]))
        list[idx] = { ...anchorEntry, folderIds: updatedFolderIds, id: anchorEntry.id }
        anchorCache.value.set(key, [...list])
      }
    })
    await loadAnchors(folderId, { force: true, autoSelect: false })
    window.alert('已加入该文件夹')
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    window.alert(detail ? `绑定失败：${detail}` : '绑定失败，请稍后重试')
  } finally {
    handleAnchorDragEnd()
  }
}

function handleTagToggle(tagId: string) {
  if (selectedTagIds.value.includes(tagId)) {
    selectedTagIds.value = selectedTagIds.value.filter((id) => id !== tagId)
  } else {
    selectedTagIds.value = [...selectedTagIds.value, tagId]
  }
}

async function handleCreateFolder() {
  const name = `新建文件夹 ${folders.value.length + 1}`
  await api.post('/folders', { name })
  await loadFolders()
}

async function handleFolderRenameCommit(payload: { id: string; name: string }) {
  const targetName = payload.name.trim()
  if (!targetName) {
    editingFolderId.value = null
    return
  }
  await api.patch(`/folders/${payload.id}`, { name: targetName })
  editingFolderId.value = null
  await loadFolders()
}

function handleFolderRenameCancel() {
  editingFolderId.value = null
}

function handleRenameFolder(folderId: string) {
  editingFolderId.value = folderId
}

async function handleDeleteFolder(folderId?: string) {
  const target = folderId ?? selectedFolderId.value
  if (!target) return

  const currentFolder = folders.value.find((f) => f.id === target)
  if (currentFolder && (currentFolder as any).isSystem) {
    window.alert('无法删除系统级虚拟文件夹')
    return
  }

  const doDelete = async () => {
    await api.delete(`/folders/${target}`)
    openFolders.value = openFolders.value.filter((f) => f.id !== target)
    anchorCache.value.delete(target)
    selectedFolderId.value = folders.value[0]?.id ?? null
    await loadFolders()
    if (selectedFolderId.value) await loadAnchors(selectedFolderId.value, { force: true })
    window.alert('删除成功')
  }

  confirmState.value = {
    open: true,
    title: '删除文件夹',
    description: '您确定要删除选中的文件夹吗？\n将不会删除此文件夹下的资料锚点。',
    onConfirm: doDelete,
  }
}

async function handleCreateAnchor() {
  if (!selectedFolderId.value) return
  const currentFolder = folders.value.find((f) => f.id === selectedFolderId.value)
  if (currentFolder && (currentFolder as any).isSystem) {
    window.alert('系统文件夹中不能创建资料，请先选择普通文件夹')
    return
  }

  let files: string[] | null = null
  const picker = window.pywebview?.api?.open_file_dialog
  if (picker) {
    try {
      const res = await picker(Number(selectedFolderId.value))
      if (res?.error) {
        window.alert(`打开文件对话框失败：${res.error}`)
        return
      }
      files = res?.files ?? []
      if (!files.length) return
    } catch (err) {
      console.error('打开文件对话框异常', err)
      return
    }
  }

  const targets = files && files.length ? files : ['/tmp/placeholder.txt']
  for (const filePath of targets) {
    const base = filePath.split(/[/\\\\]/).pop() || '新建资料锚点'
    const payload = {
      name: base,
      path: filePath,
      description: '示例描述，可通过接口更新',
      folder_id: Number(selectedFolderId.value),
    }
    await api.post('/anchors', payload)
  }

  await loadAnchors(selectedFolderId.value, { force: true })
  await refreshTags()
}

async function handleDeleteAnchor() {
  if (!selectedAnchorId.value) return
  await api.delete(`/anchors/${selectedAnchorId.value}`)
  await refreshTags()
  if (selectedFolderId.value) await loadAnchors(selectedFolderId.value, { force: true })
  selectedAnchorId.value = null
}

function openAnchorMenu(payload: { id: string; x: number; y: number }) {
  selectedAnchorId.value = payload.id
  anchorMenu.value = { visible: true, x: payload.x + 8, y: payload.y + 10, targetId: payload.id }
}

function closeAnchorMenu() {
  anchorMenu.value.visible = false
  anchorMenu.value.targetId = null
}

function handleRenameAnchor() {
  if (!anchorMenu.value.targetId) return
  editingAnchorId.value = anchorMenu.value.targetId
  closeAnchorMenu()
}

async function handleDeleteAnchorByMenu() {
  if (!anchorMenu.value.targetId) return
  selectedAnchorId.value = anchorMenu.value.targetId
  await handleDeleteAnchor()
  closeAnchorMenu()
}

async function handleAddTagToAnchor() {
  const target = anchors.value.find((a) => a.id === anchorMenu.value.targetId)
  if (!target || !anchorMenu.value.targetId) return
  dialogState.value = {
    open: true,
    title: '添加标签',
    description: '为该锚点添加一个新标签',
    value: '',
    placeholder: '输入标签名称',
    mode: 'tag',
    anchorId: target.id,
  }
  closeAnchorMenu()
}

async function handleRestoreFromRecycle() {
  if (!anchorMenu.value.targetId) return
  const targetId = anchorMenu.value.targetId
  confirmState.value = {
    open: true,
    title: '恢复资料锚点',
    description: '资料锚点将会恢复到全部资料文件夹里面，是否确认？',
    onConfirm: async () => {
      await api.post(`/anchors/${targetId}/restore`)
      await refreshTags()
      if (selectedFolderId.value) {
        await loadAnchors(selectedFolderId.value, { force: true, autoSelect: false })
      }
      closeAnchorMenu()
    },
  }
}

async function handleClearRecycle() {
  if (selectedFolderId.value !== recycleFolderId.value) return
  confirmState.value = {
    open: true,
    title: '清空回收站',
    description: '将清空回收站中的所有资料锚点，是否确认？',
    onConfirm: async () => {
      await api.delete('/folders/recycle/empty')
      if (selectedFolderId.value) {
        anchorCache.value.delete(selectedFolderId.value)
        await loadAnchors(selectedFolderId.value, { force: true, autoSelect: false })
      }
      await refreshTags()
    },
  }
}

async function handleAnchorRenameCommit(payload: { id: string; title: string }) {
  const target = anchors.value.find((a) => a.id === payload.id)
  if (!target) {
    editingAnchorId.value = null
    return
  }
  const title = payload.title.trim()
  if (title) {
    await api.patch(`/anchors/${payload.id}/name`, { name: title })
    if (selectedFolderId.value) await loadAnchors(selectedFolderId.value, { force: true })
  }
  editingAnchorId.value = null
}

async function handleUpdateAnchorDescription(anchorId: string) {
  const target = anchors.value.find((a) => a.id === anchorId)
  if (!target) return
  dialogState.value = {
    open: true,
    title: '更新描述',
    description: '请输入新的描述内容',
    value: target.summary ?? '',
    placeholder: '描述内容',
    mode: 'description',
    anchorId,
  }
  closeAnchorMenu()
}

function resetDialogState() {
  dialogState.value = {
    open: false,
    title: '',
    description: '',
    value: '',
    placeholder: '',
    mode: 'description',
    anchorId: null,
  }
}

function handleDialogCancel() {
  resetDialogState()
}

function handleConfirmCancel() {
  confirmState.value = { open: false, title: '', description: '', onConfirm: null }
}

async function handleConfirmOk() {
  const action = confirmState.value.onConfirm
  confirmState.value = { open: false, title: '', description: '', onConfirm: null }
  if (action) {
    try {
      await action()
    } catch (err) {
      console.error('确认操作失败', err)
      window.alert('操作失败，请稍后重试')
    }
  }
}

async function handleDialogConfirm() {
  const state = dialogState.value
  if (!state.anchorId) {
    resetDialogState()
    return
  }
  const text = state.value.trim()
  try {
    if (state.mode === 'description') {
      await api.patch(`/anchors/${state.anchorId}/description`, { description: text || null })
      if (selectedFolderId.value) {
        await loadAnchors(selectedFolderId.value, { force: true, autoSelect: false })
      }
    } else if (state.mode === 'tag') {
      if (!text) {
        window.alert('标签名称不能为空')
        return
      }
      await api.post(`/anchors/${state.anchorId}/tags`, { names: [text] })
      await refreshTags()
      if (selectedFolderId.value) {
        await loadAnchors(selectedFolderId.value, { force: true, autoSelect: false })
      }
    }
    resetDialogState()
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    window.alert(detail ? `操作失败：${detail}` : '操作失败，请稍后重试')
  }
}

async function handleOpenFile(anchorId: string) {
  const target = anchors.value.find((a) => a.id === anchorId)
  if (!target?.path) {
    window.alert('未找到可打开的文件路径')
    return
  }
  const opener = window.pywebview?.api?.open_file
  if (!opener) {
    window.alert('当前环境不支持直接打开本地文件')
    return
  }
  try {
    const res = await opener(target.path)
    if (!res?.success) {
      window.alert(`打开失败：${res?.error ?? '未知原因'}`)
    }
  } catch (err) {
    console.error('打开文件失败', err)
    window.alert('打开文件失败，请检查路径或权限')
  } finally {
    closeAnchorMenu()
  }
}

function handleAnchorRenameCancel() {
  editingAnchorId.value = null
}

function handleGlobalClickForAnchorRename(event: MouseEvent) {
  if (!editingAnchorId.value) return
  const target = event.target as HTMLElement | null
  if (target && target.closest('.anchor-rename-input')) return
  handleAnchorRenameCancel()
}

async function handleUntag(tag: string) {
  if (!selectedAnchorId.value) return
  let tagId = tagNameIdMap.value.get(tag)
  if (!tagId) {
    await refreshTags()
    tagId = tagNameIdMap.value.get(tag)
  }
  if (!tagId) return
  await api.delete(`/anchors/${selectedAnchorId.value}/tags/${tagId}`)
  await refreshTags()
  if (selectedFolderId.value) await loadAnchors(selectedFolderId.value, { force: true })
}

function openTagMenu(payload: { id: string; x: number; y: number }) {
  tagMenu.value = { visible: true, x: payload.x + 6, y: payload.y + 10, targetId: payload.id }
}

function closeTagMenu() {
  tagMenu.value.visible = false
  tagMenu.value.targetId = null
}

async function handleDeleteTag(id: string) {
  const target = tags.value.find((t) => t.id === id)
  const name = target?.name ?? ''
  const ok = window.confirm(`您确定删除此标签${name ? `「${name}」` : ''}吗？\n此标签将从所有条目中移除。`)
  if (!ok) {
    closeTagMenu()
    return
  }
  await api.delete(`/tags/${id}`)
  await refreshTags()
  if (selectedFolderId.value) await loadAnchors(selectedFolderId.value)
  selectedTagIds.value = selectedTagIds.value.filter((t) => t !== id)
  closeTagMenu()
}

watchEffect(() => {
  const current = filteredAnchors.value
  if (!current.length) {
    selectedAnchorId.value = null
    return
  }
  if (!current.find((item) => item.id === selectedAnchorId.value)) {
    if (!allowAutoSelectAnchor.value) return
    const first = current[0]
    selectedAnchorId.value = first ? first.id : null
  }
})

onMounted(async () => {
  window.addEventListener('click', closeAnchorMenu)
  window.addEventListener('click', closeTagMenu)
  window.addEventListener('contextmenu', closeAnchorMenu, true)
  window.addEventListener('contextmenu', closeTagMenu, true)
  window.addEventListener('click', handleGlobalClickForRename, true)
  window.addEventListener('click', closeFolderTabMenu)
  window.addEventListener('click', handleGlobalClickForAnchorRename, true)
  await initData()
})

onUnmounted(() => {
  window.removeEventListener('click', closeAnchorMenu)
  window.removeEventListener('click', closeTagMenu)
  window.removeEventListener('contextmenu', closeAnchorMenu, true)
  window.removeEventListener('contextmenu', closeTagMenu, true)
  if (anchorRequestAbort.value) {
    anchorRequestAbort.value.abort()
  }
  window.removeEventListener('click', handleGlobalClickForRename, true)
  window.removeEventListener('click', closeFolderTabMenu)
  window.removeEventListener('click', handleGlobalClickForAnchorRename, true)
})
</script>

<template>
  <div class="flex h-screen flex-col overflow-hidden bg-[#f2f2f2]">
    <div class="border-b border-slate-200 bg-[#f2f2f2]">
      <FolderTabs
        :open-folders="openFolders"
        :active-folder-id="selectedFolderId"
        @select="handleFolderSelect"
        @close="handleCloseTab"
        @context="openFolderTabMenu"
      />
    </div>

    <div class="flex flex-1 min-h-0 overflow-hidden">
      <!-- 左侧：虚拟文件夹 + 标签 -->
      <aside class="flex h-full w-64 min-w-[240px] max-w-[260px] flex-col border-r border-slate-200 bg-[#f2f2f2] min-h-0 overflow-hidden">
        <div class="flex h-full flex-col p-4">
          <div class="flex-1 min-h-0">
            <FolderTree
              class="h-full"
              :folders="folders"
              :selected-id="selectedFolderId"
              :editing-id="editingFolderId"
              :hover-folder-id="hoverFolderId"
              :dragging-anchor="draggingAnchor"
              :recycle-folder-id="recycleFolderId"
              @create="handleCreateFolder"
              @rename="handleRenameFolder"
              @rename-commit="handleFolderRenameCommit"
              @rename-cancel="handleFolderRenameCancel"
              @delete="(id) => handleDeleteFolder(id)"
              @select="handleFolderSelect"
              @anchor-drop="handleAnchorDrop"
              @anchor-drag-over="handleFolderDragOver"
              @anchor-drag-leave="() => (hoverFolderId = null)"
            />
          </div>
          <div class="mt-4 shrink-0">
            <TagManager
              class="max-h-48 overflow-y-auto"
              :tags="tags"
              :selected-tag-ids="selectedTagIds"
              @toggle="handleTagToggle"
              @context="openTagMenu"
            />
          </div>
        </div>
      </aside>

      <!-- 中间：资料锚点列表 -->
      <main class="flex min-h-0 flex-1 flex-col overflow-hidden">
        <div class="flex-1 overflow-hidden">
          <AnchorTable
            :anchors="filteredAnchors"
            :selected-id="selectedAnchorId"
            :row-height="30"
            :editing-id="editingAnchorId"
            @create="handleCreateAnchor"
            @delete="handleDeleteAnchor"
            @context="openAnchorMenu"
            @rename-commit="handleAnchorRenameCommit"
            @rename-cancel="handleAnchorRenameCancel"
            @select="(id) => (selectedAnchorId = id)"
            @drag-start="handleAnchorDragStart"
            @drag-end="handleAnchorDragEnd"
          />
        </div>
      </main>

      <!-- 右侧：信息栏 -->
      <aside class="w-[340px] min-w-[320px] max-w-[360px] border-l border-slate-200 bg-[#f2f2f2]">
        <AnchorDetail :anchor="selectedAnchor" @untag="handleUntag" />
      </aside>
    </div>

    <!-- 资料锚点右键菜单 -->
    <div
      v-if="anchorMenu.visible"
      class="fixed z-50 w-44 rounded-md border border-slate-200 bg-white shadow-lg shadow-slate-200/80"
      :style="{ top: anchorMenu.y + 'px', left: anchorMenu.x + 'px' }"
      @click.stop
    >
      <template v-if="selectedFolderId === recycleFolderId">
        <button
          class="flex w-full items-center px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
          type="button"
          @click="handleRestoreFromRecycle"
        >
          恢复资料锚点
        </button>
        <button
          class="flex w-full items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50"
          type="button"
          @click="handleClearRecycle"
        >
          清空回收站
        </button>
      </template>
      <template v-else>
        <button
          class="flex w-full items-center px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
          type="button"
          @click="anchorMenu.targetId && handleOpenFile(anchorMenu.targetId)"
        >
          打开文件
        </button>
        <button
          class="flex w-full items-center px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
          type="button"
          @click="handleRenameAnchor"
        >
          重命名锚点
        </button>
        <button
          class="flex w-full items-center px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
          type="button"
          @click="anchorMenu.targetId && handleUpdateAnchorDescription(anchorMenu.targetId)"
        >
          更新描述
        </button>
        <button
          class="flex w-full items-center px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
          type="button"
          @click="handleAddTagToAnchor"
        >
          添加标签
        </button>
        <button
          class="flex w-full items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50"
          type="button"
          @click="handleDeleteAnchorByMenu"
        >
          删除锚点
        </button>
      </template>
    </div>

    <!-- 标签右键菜单 -->
    <div
      v-if="tagMenu.visible"
      class="fixed z-50 w-32 rounded-md border border-slate-200 bg-white shadow-lg shadow-slate-200/80"
      :style="{ top: tagMenu.y + 'px', left: tagMenu.x + 'px' }"
      @click.stop
    >
      <button
        class="flex w-full items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50"
        type="button"
        @click="() => tagMenu.targetId && handleDeleteTag(tagMenu.targetId)"
      >
        删除标签
      </button>
    </div>

    <!-- 打开文件夹标签右键菜单 -->
    <div
      v-if="folderTabMenu.visible"
      class="fixed z-50 w-40 rounded-md border border-slate-200 bg-white shadow-lg shadow-slate-200/80"
      :style="{ top: folderTabMenu.y + 'px', left: folderTabMenu.x + 'px' }"
      @click.stop
    >
      <button
        class="flex w-full items-center px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
        type="button"
        @click="closeOtherFolders"
      >
        关闭其他文件夹
      </button>
      <button
        class="flex w-full items-center px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
        type="button"
        @click="closeRightFolders"
      >
        关闭右边文件夹
      </button>
      <button
        class="flex w-full items-center px-3 py-2 text-sm text-red-600 hover:bg-red-50"
        type="button"
        @click="closeAllFolders"
      >
        关闭全部文件夹
      </button>
    </div>

    <!-- 通用对话框：更新描述 / 添加标签 -->
    <Dialog v-model:open="dialogState.open">
      <DialogContent class="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>{{ dialogState.title }}</DialogTitle>
          <DialogDescription>{{ dialogState.description }}</DialogDescription>
        </DialogHeader>
        <div class="mt-4 space-y-2">
          <template v-if="dialogState.mode === 'description'">
            <textarea
              v-model="dialogState.value"
              class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-400 focus:outline-none"
              rows="4"
              :placeholder="dialogState.placeholder"
            ></textarea>
          </template>
          <template v-else>
            <input
              v-model="dialogState.value"
              type="text"
              class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-400 focus:outline-none"
              :placeholder="dialogState.placeholder"
            />
          </template>
        </div>
        <DialogFooter class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            @click="handleDialogCancel"
          >
            取消
          </button>
          <button
            type="button"
            class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            @click="handleDialogConfirm"
          >
            确认
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 通用确认对话框（恢复、清空回收站等） -->
    <Dialog v-model:open="confirmState.open">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>{{ confirmState.title }}</DialogTitle>
          <DialogDescription>{{ confirmState.description }}</DialogDescription>
        </DialogHeader>
        <DialogFooter class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            @click="handleConfirmCancel"
          >
            取消
          </button>
          <button
            type="button"
            class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            @click="handleConfirmOk"
          >
            确认
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
