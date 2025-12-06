<script setup lang="ts">
import axios from 'axios'
import settingIcon from '@/components/icons/functionMenu/setting_icon.svg'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
})

const handleOpenSettings = async () => {
  try {
    await api.get('/windows/setting')
  } catch (err) {
    console.error('打开设置窗口失败', err)
    window.alert('打开设置窗口失败，请检查后端服务状态')
  }
}
</script>

<template>
  <nav class="flex h-full w-9 shrink-0 flex-col items-center gap-2 border-l border-slate-200 bg-white py-2">
    <button
      class="flex w-full flex-col items-center px-1 py-1 transition hover:bg-slate-50 cursor-pointer"
      type="button"
      title="设置"
      aria-label="设置"
      @click="handleOpenSettings"
    >
      <img :src="settingIcon" alt="" class="h-5 w-5" />
    </button>
  </nav>
</template>
