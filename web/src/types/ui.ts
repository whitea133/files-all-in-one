export type VirtualFolder = {
  id: string
  name: string
  color?: string
  icon?: string
  count?: number
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
  folderId: string
  addedAt: string
  updatedAt: string
  citationCount?: number
  tags: string[]
  summary?: string
  attachments?: number
}
