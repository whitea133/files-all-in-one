import { ref } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
})

export const useSettingsStore = defineStore('settings', () => {
  const backupPath = ref('')

  function setBackupPath(path: string) {
    backupPath.value = path
  }

  async function loadBackupPath() {
    const res = await api.get<{ backup_path: string }>('/settings/backup/path')
    backupPath.value = res.data.backup_path || ''
    return backupPath.value
  }

  async function selectBackupPath() {
    const res = await api.post<{ backup_path: string }>('/settings/backup/path/select')
    backupPath.value = res.data.backup_path || ''
    return backupPath.value
  }

  return {
    backupPath,
    setBackupPath,
    loadBackupPath,
    selectBackupPath,
  }
})
