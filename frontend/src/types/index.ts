/**
 * API 类型定义
 */

export interface FaceBox {
  x: number
  y: number
  w: number
  h: number
}

export interface PersonInfo {
  name: string
  id_number?: string
  phone?: string
  address?: string
  gender?: string
}

export interface DetectResponse {
  detected: boolean
  face_box?: FaceBox
  person_info?: PersonInfo
}

export interface Personnel {
  id: number
  face_id: string
  name: string
  id_number?: string
  phone?: string
  address?: string
  gender?: string
  status: 'active' | 'inactive'
  photo_path?: string
  created_at: string
  updated_at: string
}

export interface PersonnelCreate {
  name: string
  id_number?: string
  phone?: string
  address?: string
  gender?: string
  photo: File
}

export interface PersonnelUpdate {
  name?: string
  id_number?: string
  phone?: string
  address?: string
  gender?: string
  photo?: File
}

export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}

export interface PaginationParams {
  page: number
  page_size: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

