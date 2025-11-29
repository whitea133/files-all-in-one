# AmberDay 项目快照（交接用）

## 1. 项目背景

- 课程资料管理工具前端，仿 Zotero 三栏；前端界面与交互完成约 85%，待接入后端与替换原生弹窗。

## 2. 负责的板块

- 前端（Vue 3 + TS + Tailwind + Pinia），含布局、右键菜单、行内编辑、标签逻辑。

## 3. 技术选型

- 语言/框架：TypeScript · Vue 3
- 构建：Vite 7
- 状态：Pinia 3
- 样式：Tailwind CSS 4，shadcn-vue 基础组件
- Icons：lucide-vue-next
- 包管理：npm（Node ^20.19 或 >=22.12）
- 安装：`cd web && npm install`

## 4. 仓库结构

```
tree -L 2 -d
.
├─app/                       (桌面端相关，未改动)
├─tests/                     (测试目录)
├─web/                       (前端工程)
│  ├─public/                 (静态资源)
│  ├─src/
│  │  ├─components/          (UI 组件)
│  │  │  ├─anchors/          (锚点表格/详情)
│  │  │  └─layout/           (顶部 tabs、左侧树、标签栏)
│  │  ├─stores/              (Pinia 示例)
│  │  ├─types/               (ui.ts 类型)
│  │  └─views/               (HomeView 主界面)
│  └─vite.config.ts          (Vite 配置)
└─webdist/                   (构建输出)
```

重要单文件：`web/src/main.ts`、`web/src/App.vue`、`web/src/views/HomeView.vue`、`web/package.json`。

## 5. 已实现功能（最小片段）

<details>
<summary>Pinia 示例 store <!-- file:web/src/stores/counter.ts --></summary>

```ts
export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubleCount = computed(() => count.value * 2)
  function increment() { count.value++ }
  return { count, doubleCount, increment }
})
```

</details>

<details>
<summary>标签计数重算 & 删除标签确认 <!-- file:web/src/views/HomeView.vue --></summary>

```ts
function recomputeTagUsage() {
  const m = new Map<string, number>()
  anchors.value.forEach((a) => a.tags.forEach((t) => m.set(t, (m.get(t) ?? 0) + 1)))
  tags.value = tags.value.map((t) => ({ ...t, usage: m.get(t.name) ?? 0 }))
}

function handleDeleteTag(id: string) {
  const name = tags.value.find((t) => t.id === id)?.name ?? ''
  if (!window.confirm(`您确定删除此标签${name ? `「${name}」` : ''}吗？\n此标签将从所有条目中移除。`)) return
  tags.value = tags.value.filter((t) => t.id !== id)
  selectedTagIds.value = selectedTagIds.value.filter((t) => t !== id)
  anchors.value = anchors.value.map((a) => ({ ...a, tags: a.tags.filter((t) => t !== name && t !== id) }))
  recomputeTagUsage()
}
```

</details>

<details>
<summary>行内重命名 + 右键菜单（锚点表格） <!-- file:web/src/components/anchors/AnchorTable.vue --></summary>

```vue
<tr v-for="anchor in anchors" @contextmenu.prevent="emit('context',{ id:anchor.id,x:$event.clientX,y:$event.clientY })">
  <td>
    <div v-if="props.editingId !== anchor.id">{{ anchor.title }}</div>
    <input v-else :value="anchor.title"
      @keydown.enter.prevent="emit('rename-commit',{ id:anchor.id,title:($event.target as HTMLInputElement).value })"
      @keydown.esc.prevent="emit('rename-cancel')"/>
  </td>
</tr>
```

</details>

<details>
<summary>虚拟文件夹行内编辑 <!-- file:web/src/components/layout/FolderTree.vue --></summary>

```vue
<button @contextmenu.prevent="openContextMenu($event, folder.id)">
  <span v-if="editingId !== folder.id">{{ folder.name }}</span>
  <input v-else :value="folder.name"
    @keydown.enter.prevent="emit('rename-commit',{ id:folder.id, name:($event.target as HTMLInputElement).value })"
    @keydown.esc.prevent="emit('rename-cancel')" />
</button>
```

</details>

<details>
<summary>信息栏标签解绑 <!-- file:web/src/components/anchors/AnchorDetail.vue --></summary>

```vue
<span v-for="tag in anchor.tags">
  <span class="truncate">{{ tag }}</span>
  <button @click.stop="emit('untag', tag)">×</button>
</span>
```

</details>

<details>
<summary>标签栏右键删除触发菜单 <!-- file:web/src/components/layout/TagManager.vue --></summary>

```vue
<button v-for="tag in tags" @contextmenu.prevent="emit('context',{ id:tag.id, x:$event.clientX, y:$event.clientY })">
  {{ tag.name }} <span v-if="tag.usage !== undefined">({{ tag.usage }})</span>
</button>
```

</details>

## 6. 待办清单

| 任务                       | 目标文件                          | 验收标准                        |
| ------------------------ | ----------------------------- | --------------------------- |
| 自定义弹层替换原生 prompt/confirm | HomeView.vue 及相关组件            | 右键菜单操作、添加/删除标签均用自定义模态，UI 一致 |
| 标签选择面板（添加标签）             | HomeView.vue / TagManager.vue | 弹窗可选择已有标签或新建，计数实时更新         |
| 国际化/文案统一                 | 全局                            | 无乱码，文案统一或接入 i18n            |
| 后端接口接入                   | HomeView.vue 等                | 数据持久化，加载/错误状态有提示            |

## 7. 注意事项

- Node ^20.19 或 >=22.12；安装 `cd web && npm install`。
- 构建：`cd web && npm run build`（outDir 提示如需清空用 `--emptyOutDir`）。
- 右键菜单定位：`position: fixed` 视口坐标，偏移在组件内硬编码（可调）。
- 顶部标签栏：单行隐藏滚动条，宽度 clamp(100px, 12vw, 180px)。
- 编码统一 UTF-8。

## 8. 关键对话摘要（倒序）

- 2025-xx-xx：标签删除确认并同步清理锚点；信息栏标签可解绑。
- 2025-xx-xx：行内重命名文件夹/锚点；右键菜单固定定位；标签计数重算。
- 2025-xx-xx：顶部标签栏单行自适应；左侧栏滚动修复；右键遮挡修复。
- 2025-xx-xx：完成三栏布局与虚拟文件夹/锚点/标签基础交互。
