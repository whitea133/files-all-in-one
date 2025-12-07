<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { useSettingsStore } from '@/stores/settings'

type SectionKey = 'basic' | 'backup' | 'other1' | 'other2'

const sections: Array<{ key: SectionKey; title: string; desc: string }> = [
  { key: 'basic', title: '基础设置', desc: '外观与语言等通用选项' },
  { key: 'backup', title: '备份设置', desc: '备份路径与方式' },
  { key: 'other1', title: '其他设置 1', desc: '预留的其他配置项' },
  { key: 'other2', title: '其他设置 2', desc: '预留的其他配置项' },
]

const activeKey = ref<SectionKey>('basic')
const themeChoice = ref<'light' | 'dark' | 'auto'>('light')
const showLineNumbers = ref(true)
const autoSave = ref(true)

const settingsStore = useSettingsStore()
const backupPathDisplay = computed(() => settingsStore.backupPath || '未选择路径')

const activeSection = computed(() => sections.find((s) => s.key === activeKey.value) ?? sections[0])

async function handlePickBackupPath() {
  try {
    await settingsStore.selectBackupPath()
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || '选择路径失败，请重试'
    window.alert(msg)
  }
}

onMounted(() => {
  settingsStore.loadBackupPath().catch(() => {
    /* ignore */
  })
})
</script>

<template>
  <div class="flex h-screen w-screen bg-slate-100">
    <div class="flex h-full w-full overflow-hidden border-t border-slate-200 bg-white shadow-lg">
      <aside class="w-48 border-r border-slate-200 bg-slate-50">
        <div class="px-4 py-3 text-sm font-semibold text-slate-600">设置</div>
        <nav class="flex flex-col">
          <button
            v-for="item in sections"
            :key="item.key"
            class="flex items-center justify-between px-4 py-3 text-sm transition"
            :class="activeKey === item.key ? 'bg-blue-50 text-blue-700 font-medium' : 'text-slate-700 hover:bg-slate-100'"
            type="button"
            @click="activeKey = item.key"
          >
            <span>{{ item.title }}</span>
            <span v-if="activeKey === item.key" aria-hidden="true">›</span>
          </button>
        </nav>
      </aside>

      <main class="flex-1 overflow-auto p-8">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold text-slate-800">{{ activeSection?.title }}</h2>
            <p class="text-sm text-slate-500">{{ activeSection?.desc }}</p>
          </div>
        </div>

        <div class="mt-8 space-y-8">
          <template v-if="activeSection?.key === 'basic'">
            <section class="space-y-4">
              <h3 class="text-base font-semibold text-slate-800">外观</h3>
              <div class="space-y-2">
                <div class="text-sm font-medium text-slate-700">背景颜色</div>
                <div class="flex gap-6 text-sm text-slate-700">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input v-model="themeChoice" type="radio" value="light" class="h-4 w-4 text-blue-600" />
                    浅色
                  </label>
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input v-model="themeChoice" type="radio" value="dark" class="h-4 w-4 text-blue-600" />
                    深色
                  </label>
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input v-model="themeChoice" type="radio" value="auto" class="h-4 w-4 text-blue-600" />
                    跟随系统
                  </label>
                </div>
              </div>

              <div class="space-y-2">
                <div class="text-sm font-medium text-slate-700">编辑体验</div>
                <label class="flex items-center gap-2 text-sm text-slate-700">
                  <input v-model="showLineNumbers" type="checkbox" class="h-4 w-4 text-blue-600" />
                  显示行号
                </label>
                <label class="flex items-center gap-2 text-sm text-slate-700">
                  <input v-model="autoSave" type="checkbox" class="h-4 w-4 text-blue-600" />
                  自动保存
                </label>
              </div>
            </section>
          </template>

          <template v-else-if="activeSection?.key === 'backup'">
            <section class="space-y-4">
              <h3 class="text-base font-semibold text-slate-800">备份路径</h3>
              <p class="text-sm text-slate-600">请选择备份目录（当前仅展示，不触发实际操作）。</p>
              <div class="flex items-center gap-3">
                <input
                  :value="backupPathDisplay"
                  type="text"
                  class="w-80 rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  readonly
                />
                <Button type="button" size="sm" class="px-3" @click="handlePickBackupPath">
                  选择路径
                </Button>
              </div>
            </section>
          </template>

          <template v-else-if="activeSection?.key === 'other1'">
            <section class="space-y-3">
              <h3 class="text-base font-semibold text-slate-800">其他设置 1</h3>
              <p class="text-sm text-slate-600">这里是预留的配置区域，可按需补充具体选项。</p>
              <ul class="list-disc space-y-1 pl-5 text-sm text-slate-700">
                <li>预留开关或选择器</li>
                <li>示例占位：自定义规则</li>
              </ul>
            </section>
          </template>

          <template v-else-if="activeSection?.key === 'other2'">
            <section class="space-y-3">
              <h3 class="text-base font-semibold text-slate-800">其他设置 2</h3>
              <p class="text-sm text-slate-600">同样作为占位，可后续扩展为高级配置。</p>
              <div class="rounded-md border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-700">
                在此处添加新的设置面板或说明文字。
              </div>
            </section>
          </template>
        </div>
      </main>
    </div>
  </div>
</template>
