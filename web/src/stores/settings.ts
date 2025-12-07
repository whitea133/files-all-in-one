import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useSettingsStore = defineStore('settings', () => {
  const backupPath = ref('')

  function setBackupPath(path: string) {
    backupPath.value = path
  }

  return {
    backupPath,
    setBackupPath,
  }
})
