<script setup lang="ts">
import settingIcon from '@/components/icons/functionMenu/setting_icon.svg'

const handleOpenSettings = () => {
  // 预留设置入口，后续接入实际功能
  window.alert('设置功能开发中，敬请期待')
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
