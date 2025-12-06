<script setup lang="ts">
const emit = defineEmits<{
  (e: 'settings'): void
  (e: 'about'): void
}>()
</script>

<template>
  <div class="flex items-center justify-start gap-2 border-b border-slate-200 bg-[#f2f2f2] px-4 py-1.5 h-10">
    <button
      class="rounded-md border border-slate-200 px-3 py-1 text-sm text-slate-700 transition hover:border-blue-400 hover:text-blue-700"
      type="button"
      @click="emit('settings')"
    >
      设置
    </button>
    <button
      class="rounded-md border border-slate-200 px-3 py-1 text-sm text-slate-700 transition hover:border-blue-400 hover:text-blue-700"
      type="button"
      @click="emit('about')"
    >
      关于
    </button>
  </div>
</template>
