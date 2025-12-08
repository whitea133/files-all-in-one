<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { useSettingsStore } from '@/stores/settings'

type SectionKey = 'basic' | 'backup' | 'other1' | 'logs'

type OperatorLog = {
  id: number
  operator_type_id: number
  operator_type_name: string
  operator_type_description?: string | null
  result: string
  time: string
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
})

const sections: Array<{ key: SectionKey; title: string; desc: string }> = [
  { key: 'basic', title: '基础设置', desc: '外观与语言等通用选项' },
  { key: 'backup', title: '备份设置', desc: '备份路径与方式' },
  { key: 'other1', title: '其他设置 1', desc: '预留的其他配置项' },
  { key: 'logs', title: '日志记录', desc: '查看所有操作日志' },
]

const activeKey = ref<SectionKey>('basic')
const themeChoice = ref<'light' | 'dark' | 'auto'>('light')
const showLineNumbers = ref(true)
const autoSave = ref(true)

const settingsStore = useSettingsStore()
const backupPathDisplay = computed(() => settingsStore.backupPath || '未选择路径')

const activeSection = computed(() => sections.find((s) => s.key === activeKey.value) ?? sections[0])

const logs = ref<OperatorLog[]>([])
const logsLoading = ref(false)
const logsError = ref('')
const hasFetchedLogs = ref(false)

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

async function fetchLogs() {
  logsError.value = ''
  logsLoading.value = true
  try {
    const res = await api.get<OperatorLog[]>('/logs/')
    logs.value = res.data
    hasFetchedLogs.value = true
  } catch (err: any) {
    logsError.value = err?.response?.data?.detail || err?.message || '获取日志失败，请稍后重试'
  } finally {
    logsLoading.value = false
  }
}

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
  if (activeKey.value === 'logs') {
    fetchLogs()
  }
})

watch(
  () => activeKey.value,
  (key) => {
    if (key === 'logs' && !hasFetchedLogs.value) {
      fetchLogs()
    }
  },
)
</script>

<template>
  <div class="flex h-screen w-screen bg-slate-100">
    <div class="flex h-full w-full overflow-hidden border-t border-slate-200 bg-white shadow-lg">
      <aside class="w-52 border-r border-slate-200 bg-slate-50">
        <div class="px-4 py-3 text-sm font-semibold text-slate-600">设置</div>
        <nav class="flex flex-col">
          <button
            v-for="item in sections"
            :key="item.key"
            class="flex items-center justify-between px-4 py-3 text-sm transition"
            :class="
              activeKey === item.key
                ? 'bg-blue-50 text-blue-700 font-medium'
                : 'text-slate-700 hover:bg-slate-100'
            "
            type="button"
            @click="activeKey = item.key"
          >
            <span>{{ item.title }}</span>
            <span v-if="activeKey === item.key" aria-hidden="true">></span>
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
                  <label class="flex cursor-pointer items-center gap-2">
                    <input v-model="themeChoice" type="radio" value="light" class="h-4 w-4 text-blue-600" />
                    浅色
                  </label>
                  <label class="flex cursor-pointer items-center gap-2">
                    <input v-model="themeChoice" type="radio" value="dark" class="h-4 w-4 text-blue-600" />
                    深色
                  </label>
                  <label class="flex cursor-pointer items-center gap-2">
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
              <p class="text-sm text-slate-600">预留的配置区域，可按需补充具体选项。</p>
              <ul class="list-disc space-y-1 pl-5 text-sm text-slate-700">
                <li>预留开关或选择器</li>
                <li>示例占位：自定义规则</li>
              </ul>
            </section>
          </template>

          <template v-else-if="activeSection?.key === 'logs'">
            <section class="space-y-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <h3 class="text-base font-semibold text-slate-800">日志记录</h3>
                  <p class="text-sm text-slate-600">来自后端的操作日志，按时间倒序展示。</p>
                </div>
                <Button type="button" size="sm" :disabled="logsLoading" class="px-3" @click="fetchLogs">
                  {{ logsLoading ? '刷新中...' : '刷新' }}
                </Button>
              </div>

              <div
                v-if="logsError"
                class="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              >
                {{ logsError }}
              </div>

              <div class="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
                <div v-if="logsLoading" class="px-4 py-6 text-sm text-slate-600">正在加载日志...</div>
                <div v-else-if="!logs.length" class="px-4 py-6 text-sm text-slate-600">暂无日志记录。</div>
                <table v-else class="w-full table-fixed text-sm text-slate-800">
                  <thead class="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th class="w-44 border-b border-slate-200 px-4 py-3 text-left">时间</th>
                      <th class="w-52 border-b border-slate-200 px-4 py-3 text-left">类型</th>
                      <th class="border-b border-slate-200 px-4 py-3 text-left">结果</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in logs" :key="item.id" class="odd:bg-white even:bg-slate-50">
                      <td class="align-top px-4 py-3 font-mono text-xs text-slate-600">
                        {{ formatDateTime(item.time) }}
                      </td>
                      <td class="align-top px-4 py-3 text-xs">
                        <div class="font-medium text-slate-800">{{ item.operator_type_name || '未分类' }}</div>
                      </td>
                      <td class="align-top px-4 py-3 text-sm text-slate-800">
                        <div class="whitespace-pre-wrap leading-relaxed">
                          {{ item.result }}
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          </template>
        </div>
      </main>
    </div>
  </div>
</template>
