<script setup lang="ts">
import AnchorDetail from '@/components/anchors/AnchorDetail.vue'
import AnchorTable from '@/components/anchors/AnchorTable.vue'
import FolderTabs from '@/components/layout/FolderTabs.vue'
import FolderTree from '@/components/layout/FolderTree.vue'
import TagManager from '@/components/layout/TagManager.vue'
import type { AnchorItem, TagItem, VirtualFolder } from '@/types/ui'
import { computed, onMounted, onUnmounted, ref, watchEffect } from 'vue'

const folders = ref<VirtualFolder[]>([
  { id: 'all', name: '全部课程资料', color: 'bg-blue-400', icon: 'folder', count: 12 },
  { id: 'ai', name: '人工智能', color: 'bg-emerald-400', icon: 'folder', count: 4 },
  { id: 'security', name: '网络安全', color: 'bg-amber-400', icon: 'folder', count: 3 },
  { id: 'writing', name: '文本文档写作', color: 'bg-indigo-400', icon: 'folder', count: 2 },
  { id: 'mobile', name: '移动端需求安全', color: 'bg-rose-400', icon: 'folder', count: 3 },
  { id: 'archive', name: '归档', color: 'bg-slate-400', icon: 'folder', count: 0 },
  { id: 'recycle', name: '回收站', color: 'bg-slate-500', icon: 'recycle', count: 0 },
])

const anchors = ref<AnchorItem[]>([
  {
    id: 'a1',
    title: 'DiffStega: Training-Free Covert Image Steganography',
    creator: 'Yang 等',
    folderId: 'security',
    addedAt: '2025/09/26 14:20:42',
    updatedAt: '2025/09/26 14:21:25',
    citationCount: 3,
    tags: ['隐写', 'Diffusion', '安全'],
    summary: '介绍一种基于扩散模型的无载体隐写方法，提升安全性与多样性。',
    attachments: 1,
  },
  {
    id: 'a2',
    title: 'Hierarchical Image Steganography for Robust Transmission',
    creator: 'Xu 等',
    folderId: 'security',
    addedAt: '2025/09/26 14:21:32',
    updatedAt: '2025/10/05 22:08:06',
    citationCount: 5,
    tags: ['图像', '加密', '安全'],
    summary: '分层隐写策略，兼顾鲁棒性与隐蔽性，适合复杂网络环境。',
    attachments: 2,
  },
  {
    id: 'a3',
    title: '基于Transformer的课程资料检索与推荐',
    creator: 'Zhu 等',
    folderId: 'ai',
    addedAt: '2025/10/12 10:18:28',
    updatedAt: '2025/11/05 19:21:23',
    citationCount: 8,
    tags: ['NLP', '推荐', '课程资料'],
    summary: '使用多模态 Transformer 聚合课堂资料，支持检索与推荐。',
    attachments: 0,
  },
  {
    id: 'a4',
    title: '课程作业质量评估与反馈闭环',
    creator: 'Ma 等',
    folderId: 'writing',
    addedAt: '2025/10/22 09:12:30',
    updatedAt: '2025/10/24 11:30:11',
    citationCount: 2,
    tags: ['写作', '反馈', '教学'],
    summary: '建立作业评分、批注与改进反馈闭环的流程设计。',
    attachments: 3,
  },
  {
    id: 'a5',
    title: '移动端课件访问的安全策略',
    creator: 'Liu 等',
    folderId: 'mobile',
    addedAt: '2025/09/12 08:18:00',
    updatedAt: '2025/09/14 09:20:10',
    citationCount: 1,
    tags: ['移动端', '权限', '安全'],
    summary: '阐述移动端课件的权限管控、离线缓存与防泄露方案。',
    attachments: 1,
  },
])

const tags = ref<TagItem[]>([
  { id: 't1', name: '安全', color: 'bg-amber-500', usage: 3 },
  { id: 't2', name: 'Diffusion', color: 'bg-blue-500', usage: 1 },
  { id: 't3', name: 'NLP', color: 'bg-indigo-500', usage: 1 },
  { id: 't4', name: '写作', color: 'bg-emerald-500', usage: 1 },
  { id: 't5', name: '移动端', color: 'bg-rose-500', usage: 1 },
  { id: 't6', name: '推荐', color: 'bg-cyan-500', usage: 1 },
])

const openFolders = ref<VirtualFolder[]>(folders.value[0] ? [folders.value[0]] : [])
const selectedFolderId = ref<string | null>(folders.value[0]?.id ?? null)
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

const tagNameMap = computed(() => new Map(tags.value.map((t) => [t.id, t.name])))

const filteredAnchors = computed(() => {
  const base =
    selectedFolderId.value === 'all' || !selectedFolderId.value
      ? anchors.value
      : anchors.value.filter((item) => item.folderId === selectedFolderId.value)
  if (!selectedTagIds.value.length) return base
  const targetNames = selectedTagIds.value
    .map((id) => tagNameMap.value.get(id) ?? id)
    .filter(Boolean)
  return base.filter((item) => targetNames.every((tag) => item.tags.includes(tag)))
})

const selectedAnchor = computed(() =>
  anchors.value.find((item) => item.id === selectedAnchorId.value) || null,
)

function handleFolderSelect(folderId: string) {
  selectedFolderId.value = folderId
  const folder = folders.value.find((f) => f.id === folderId)
  if (folder && !openFolders.value.find((f) => f.id === folder.id)) {
    openFolders.value.push(folder)
  }
}

function handleCloseTab(folderId: string) {
  openFolders.value = openFolders.value.filter((f) => f.id !== folderId)
  if (selectedFolderId.value === folderId) {
    const fallback = openFolders.value[0] ?? folders.value[0] ?? null
    selectedFolderId.value = fallback?.id ?? null
  }
}

function handleTagToggle(tagId: string) {
  if (selectedTagIds.value.includes(tagId)) {
    selectedTagIds.value = selectedTagIds.value.filter((id) => id !== tagId)
  } else {
    selectedTagIds.value = [...selectedTagIds.value, tagId]
  }
}

function handleCreateFolder() {
  const name = `新建文件夹 ${folders.value.length + 1}`
  const id = `folder-${Date.now()}`
  const newFolder: VirtualFolder = { id, name, color: 'bg-blue-400', icon: 'folder', count: 0 }
  folders.value.push(newFolder)
  handleFolderSelect(id)
}

function handleFolderRenameCommit(payload: { id: string; name: string }) {
  const target = folders.value.find((f) => f.id === payload.id)
  if (!target || ['all', 'recycle'].includes(target.id)) {
    editingFolderId.value = null
    return
  }
  const name = payload.name.trim()
  if (name) target.name = name
  editingFolderId.value = null
}

function handleFolderRenameCancel() {
  editingFolderId.value = null
}

function handleRenameFolder(folderId: string) {
  if (['all', 'recycle'].includes(folderId)) return
  editingFolderId.value = folderId
}

function handleDeleteFolder(folderId?: string) {
  const target = folderId ?? selectedFolderId.value
  if (!target || ['all', 'recycle'].includes(target)) return
  anchors.value = anchors.value.filter((a) => a.folderId !== target)
  recomputeTagUsage()
  folders.value = folders.value.filter((f) => f.id !== target)
  openFolders.value = openFolders.value.filter((f) => f.id !== target)
  const fallback = folders.value[0] ?? null
  selectedFolderId.value = fallback?.id ?? null
}

function handleCreateAnchor() {
  if (!selectedFolderId.value) return
  const id = `anchor-${Date.now()}`
  const anchor: AnchorItem = {
    id,
    title: '新建资料锚点',
    creator: '未命名',
    folderId: selectedFolderId.value,
    addedAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    citationCount: 0,
    tags: [],
    attachments: 0,
    summary: '这是一个示例摘要，可替换为真实数据。',
  }
  anchors.value = [anchor, ...anchors.value]
  selectedAnchorId.value = id
}

function handleDeleteAnchor() {
  if (!selectedAnchorId.value) return
  anchors.value = anchors.value.filter((a) => a.id !== selectedAnchorId.value)
  recomputeTagUsage()
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

function handleDeleteAnchorByMenu() {
  if (!anchorMenu.value.targetId) return
  anchors.value = anchors.value.filter((a) => a.id !== anchorMenu.value.targetId)
  if (selectedAnchorId.value === anchorMenu.value.targetId) selectedAnchorId.value = null
  recomputeTagUsage()
  closeAnchorMenu()
}

function handleAddTagToAnchor() {
  const target = anchors.value.find((a) => a.id === anchorMenu.value.targetId)
  if (!target) return
  const input = window.prompt('输入要添加的标签名')
  if (!input) return
  const name = input.trim()
  if (!name) return
  if (!target.tags.includes(name)) {
    target.tags = [...target.tags, name]
  }
  const existed = tags.value.find((t) => t.name === name)
  if (!existed) {
    tags.value.push({
      id: `tag-${Date.now()}`,
      name,
      color: 'bg-blue-400',
      usage: 1,
    })
  } else if (existed.usage !== undefined) {
    existed.usage += 1
  }
  recomputeTagUsage()
  closeAnchorMenu()
}

function handleAnchorRenameCommit(payload: { id: string; title: string }) {
  const target = anchors.value.find((a) => a.id === payload.id)
  if (!target) {
    editingAnchorId.value = null
    return
  }
  const title = payload.title.trim()
  if (title) target.title = title
  editingAnchorId.value = null
}

function handleAnchorRenameCancel() {
  editingAnchorId.value = null
}

function handleUntag(tag: string) {
  if (!selectedAnchorId.value) return
  const target = anchors.value.find((a) => a.id === selectedAnchorId.value)
  if (!target) return
  target.tags = target.tags.filter((t) => t !== tag)
  recomputeTagUsage()
}

function openTagMenu(payload: { id: string; x: number; y: number }) {
  tagMenu.value = { visible: true, x: payload.x + 6, y: payload.y + 10, targetId: payload.id }
}

function closeTagMenu() {
  tagMenu.value.visible = false
  tagMenu.value.targetId = null
}

function handleDeleteTag(id: string) {
  const target = tags.value.find((t) => t.id === id)
  const name = target?.name ?? ''
  const ok = window.confirm(`您确定删除此标签${name ? `「${name}」` : ''}吗？\n此标签将从所有条目中移除。`)
  if (!ok) {
    closeTagMenu()
    return
  }
  tags.value = tags.value.filter((t) => t.id !== id)
  selectedTagIds.value = selectedTagIds.value.filter((t) => t !== id)
  anchors.value = anchors.value.map((a) => ({
    ...a,
    tags: a.tags.filter((tag) => tag !== name && tag !== id),
  }))
  recomputeTagUsage()
  closeTagMenu()
}

function recomputeTagUsage() {
  const usageMap = new Map<string, number>()
  anchors.value.forEach((a) => {
    a.tags.forEach((tag) => {
      usageMap.set(tag, (usageMap.get(tag) ?? 0) + 1)
    })
  })
  tags.value = tags.value.map((t) => ({
    ...t,
    usage: usageMap.get(t.name) ?? 0,
  }))
}

watchEffect(() => {
  const current = filteredAnchors.value
  if (!current.length) {
    selectedAnchorId.value = null
    return
  }
  if (!current.find((item) => item.id === selectedAnchorId.value)) {
    const first = current[0]
    selectedAnchorId.value = first ? first.id : null
  }
})

onMounted(() => {
  window.addEventListener('click', closeAnchorMenu)
  window.addEventListener('click', closeTagMenu)
})

onUnmounted(() => {
  window.removeEventListener('click', closeAnchorMenu)
  window.removeEventListener('click', closeTagMenu)
})
</script>

<template>
  <div class="flex h-screen flex-col overflow-hidden bg-slate-50">
    <div class="border-b border-slate-200 bg-white">
      <FolderTabs
        :open-folders="openFolders"
        :active-folder-id="selectedFolderId"
        @select="handleFolderSelect"
        @close="handleCloseTab"
      />
    </div>

    <div class="flex flex-1 min-h-0 overflow-hidden">
      <!-- 左侧：虚拟文件夹 + 标签 -->
      <aside class="flex h-full w-72 min-w-[280px] max-w-[280px] flex-col border-r border-slate-200 bg-white min-h-0 overflow-hidden">
        <div class="flex h-full flex-col p-4">
          <div class="text-sm font-semibold text-slate-700">搜索虚拟文件夹</div>
          <div class="mt-2 flex-1 min-h-0">
            <FolderTree
              class="h-full"
              :folders="folders"
              :selected-id="selectedFolderId"
              :editing-id="editingFolderId"
              @create="handleCreateFolder"
              @rename="handleRenameFolder"
              @rename-commit="handleFolderRenameCommit"
              @rename-cancel="handleFolderRenameCancel"
              @delete="(id) => handleDeleteFolder(id)"
              @select="handleFolderSelect"
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
          />
        </div>
      </main>

      <!-- 右侧：信息栏 -->
      <aside class="w-[340px] min-w-[320px] max-w-[360px] border-l border-slate-200 bg-white">
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
  </div>
</template>
