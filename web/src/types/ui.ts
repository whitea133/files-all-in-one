export type VirtualFolder = {
  id: string
  name: string
  color?: string
  icon?: string
  count?: number
  isSystem?: boolean
}

export type TagItem = {
  id: string
  name: string
  color?: string
  usage?: number
}

export type AnchorItem = {
  id: string
  title: string
  creator: string
  type: string
  folderId: string
  folderIds?: string[]
  addedAt: string
  updatedAt: string
  tags: string[]
  summary?: string
  attachments?: number
}
