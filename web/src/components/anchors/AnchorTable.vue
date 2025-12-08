<script setup lang="ts">
import type { AnchorItem } from '@/types/ui'
import addAnchorIcon from '@/components/icons/addAnchor_icon.svg'
import refreshIcon from '@/components/icons/refresh.svg'
import { computed } from 'vue'

const props = defineProps<{
  anchors: AnchorItem[]
  selectedId: string | null
  /** 行高控制，默认为32px，可传 number(单位px) 或字符串('30px') */
  rowHeight?: number | string
  editingId?: string | null
}>()

const emit = defineEmits<{
  (e: 'select', anchorId: string): void
  (e: 'create'): void
  (e: 'delete'): void
  (e: 'context', payload: { id: string; x: number; y: number }): void
  (e: 'refresh'): void
  (e: 'rename-commit', payload: { id: string; title: string }): void
  (e: 'rename-cancel'): void
  (e: 'drag-start', payload: { id: string }): void
  (e: 'drag-end'): void
  (e: 'update-description', anchorId: string): void
}>()

const rowHeightStyle = computed(() => {
  if (typeof props.rowHeight === 'number') return `${props.rowHeight}px`
  return props.rowHeight || '32px'
})
</script>

<template>
  <div class="flex h-full min-w-0 flex-col border-x border-slate-200 bg-white">
    <div class="flex items-center justify-between border-b border-slate-200 px-4 py-2">
      <div class="text-sm font-semibold text-slate-700">资料锚点</div>
      <div class="flex items-center gap-2 text-xs text-slate-500">
        <button
          class="hover:text-blue-600 cursor-pointer transition"
          type="button"
          title="刷新锚点"
          @click="emit('refresh')"
        >
          <img
            class="h-5 w-5 transition"
            :class="'hover:[filter:invert(35%)_sepia(93%)_saturate(1820%)_hue-rotate(201deg)_brightness(95%)_contrast(89%)]'"
            :src="refreshIcon"
            alt="刷新锚点"
          />
        </button>
        <button
          class="hover:text-blue-600 cursor-pointer transition"
          type="button"
          title="创建锚点"
          @click="emit('create')"
        >
          <img
            class="h-6 w-6 transition"
            :class="'hover:[filter:invert(35%)_sepia(93%)_saturate(1820%)_hue-rotate(201deg)_brightness(95%)_contrast(89%)]'"
            :src="addAnchorIcon"
            alt="创建锚点"
          />
        </button>
      </div>
    </div>
    <div class="flex-1 overflow-hidden px-2">
      <table class="w-full table-fixed text-sm">
        <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500">
          <tr>
            <th class="px-3 py-2 font-semibold w-[32%]">标题</th>
            <th class="px-3 py-2 font-semibold w-[17%]">添加日期</th>
            <th class="px-3 py-2 font-semibold w-[17%]">修改日期</th>
            <th class="px-3 py-2 font-semibold w-[24%]">文件路径</th>
            <th class="px-3 py-2 font-semibold w-[10%]">类型</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr
            v-for="anchor in anchors"
            :key="anchor.id"
            class="cursor-pointer transition leading-tight"
            :class="[
              anchor.id === selectedId ? 'selected-row bg-[#4072E5]' : 'hover:bg-slate-50',
              anchor.isValid === false && anchor.id !== selectedId ? 'bg-red-50/60' : '',
            ]"
            :style="{ height: rowHeightStyle, minHeight: rowHeightStyle }"
            @click="emit('select', anchor.id)"
            @contextmenu.prevent="emit('context', { id: anchor.id, x: $event.clientX, y: $event.clientY })"
            draggable="true"
            @dragstart.stop="emit('drag-start', { id: anchor.id })"
            @dragend.stop="emit('drag-end')"
          >
            <td class="max-w-[320px] px-3 py-0 align-middle">
              <div
                v-if="props.editingId !== anchor.id"
                class="flex items-center gap-2"
              >
                <span
                  :class="[
                    'truncate whitespace-nowrap text-[13px] font-medium',
                    anchor.id === selectedId ? 'text-white' : 'text-slate-900',
                    anchor.isValid === false && anchor.id !== selectedId ? 'text-red-700' : '',
                  ]"
                >
                  {{ anchor.title }}
                </span>
                <span
                  v-if="anchor.isValid === false"
                  class="shrink-0 rounded-full bg-red-100 px-2 py-0.5 text-[11px] font-semibold text-red-700"
                >
                  文件不存在
                </span>
              </div>
              <input
                v-else
                class="anchor-rename-input w-full truncate rounded border border-blue-300 px-2 py-1 text-[13px] outline-none"
                :value="anchor.title"
                autofocus
                @keydown.enter.stop.prevent="emit('rename-commit', { id: anchor.id, title: ($event.target as HTMLInputElement).value })"
                @blur="emit('rename-cancel')"
                @keydown.esc.stop.prevent="emit('rename-cancel')"
              />
            </td>
            <td class="px-3 py-0 text-[13px] text-slate-900 align-middle">
              <div class="truncate" :title="anchor.addedAt">{{ anchor.addedAt }}</div>
            </td>
            <td class="px-3 py-0 text-[13px] text-slate-900 align-middle">
              <div class="truncate" :title="anchor.updatedAt">{{ anchor.updatedAt }}</div>
            </td>
            <td class="px-3 py-0 text-[13px] text-slate-900 align-middle">
              <div class="truncate" :title="anchor.path">{{ anchor.path }}</div>
            </td>
            <td class="px-3 py-0 text-[13px] text-slate-900 align-middle">
              <div class="truncate" :title="anchor.type || '未知'">{{ anchor.type || '未知' }}</div>
            </td>
          </tr>
          <tr v-if="!anchors.length">
            <td colspan="5" class="px-4 py-10 text-center text-slate-400">
              暂无资料锚点，点击右上角添加新资料锚点
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.selected-row td {
  color: #ffffff;
}
.selected-row input {
  color: #0f172a;
}
.selected-row td:first-child {
  border-top-left-radius: 6px;
  border-bottom-left-radius: 6px;
}
.selected-row td:last-child {
  border-top-right-radius: 6px;
  border-bottom-right-radius: 6px;
}
</style>
