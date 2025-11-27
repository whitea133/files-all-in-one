<script setup lang="ts">
import AnchorDetail from '@/components/anchors/AnchorDetail.vue'
import AnchorTable from '@/components/anchors/AnchorTable.vue'
import FolderTabs from '@/components/layout/FolderTabs.vue'
import FolderTree from '@/components/layout/FolderTree.vue'
import TagManager from '@/components/layout/TagManager.vue'
import type { AnchorItem, TagItem, VirtualFolder } from '@/types/ui'
import { computed, ref, watchEffect } from 'vue'

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
    const fallback = openFolders.value[0] ?? folders.value[0]
    if (fallback) {
      if (!openFolders.value.find((f) => f.id === fallback.id)) {
        openFolders.value.unshift(fallback)
      }
      selectedFolderId.value = fallback.id
    } else {
      selectedFolderId.value = null
    }
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
  const name = `新建文件夹 ${folders.value.length}`
  const id = `folder-${Date.now()}`
  const newFolder: VirtualFolder = { id, name, color: 'bg-blue-400', icon: 'folder', count: 0 }
  folders.value.push(newFolder)
  handleFolderSelect(id)
}

function handleDeleteFolder(folderId?: string) {
  const target = folderId ?? selectedFolderId.value
  if (!target || ['all', 'recycle'].includes(target)) return
  anchors.value = anchors.value.filter((a) => a.folderId !== target)
  folders.value = folders.value.filter((f) => f.id !== target)
  openFolders.value = openFolders.value.filter((f) => f.id !== target)
  const fallback = folders.value[0] ?? null
  selectedFolderId.value = fallback?.id ?? null
}

function handleRenameFolder(folderId: string) {
  if (['all', 'recycle'].includes(folderId)) return
  const target = folders.value.find((f) => f.id === folderId)
  if (!target) return
  const newName = window.prompt('重命名虚拟文件夹', target.name)
  if (!newName) return
  target.name = newName
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
  selectedAnchorId.value = null
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
              @create="handleCreateFolder"
              @rename="handleRenameFolder"
              @delete="(id) => handleDeleteFolder(id)"
              @select="handleFolderSelect"
            />
          </div>
          <div class="mt-4 shrink-0">
            <TagManager
              :tags="tags"
              :selected-tag-ids="selectedTagIds"
              @toggle="handleTagToggle"
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
            @create="handleCreateAnchor"
            @delete="handleDeleteAnchor"
            @select="(id) => (selectedAnchorId = id)"
          />
        </div>
      </main>

      <!-- 右侧：信息栏 -->
      <aside class="w-[340px] min-w-[320px] max-w-[360px] border-l border-slate-200 bg-white">
        <AnchorDetail :anchor="selectedAnchor" />
      </aside>
    </div>
  </div>
</template>
