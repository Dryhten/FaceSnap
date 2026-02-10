/**
 * API 服务层
 */
import axios from 'axios'
import type {
  DetectResponse,
  Personnel,
  PersonnelCreate,
  PersonnelUpdate,
  PersonnelCategory,
  PaginatedResponse,
} from '@/types'

// 开发环境使用代理（vite.config.ts 中配置），生产环境使用环境变量
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? '' : 'http://localhost:8000')

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 500) {
        error.message = data?.detail || '服务器内部错误'
      } else if (status === 400) {
        error.message = data?.detail || '请求参数错误'
      } else if (status === 404) {
        error.message = '资源不存在'
      } else {
        error.message = data?.message || data?.detail || '请求失败'
      }
    } else if (error.request) {
      error.message = '网络错误，请检查网络连接'
    } else {
      error.message = error.message || '请求失败'
    }
    return Promise.reject(error)
  }
)

/**
 * 人脸检测 API
 */
export const detectApi = {
  /**
   * 上传图片进行人脸检测和识别
   */
  detect: async (file: File): Promise<DetectResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post<DetectResponse>('/api/v1/detect', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

/**
 * 人员管理 API
 */
export const personnelApi = {
  /**
   * 获取人员列表
   */
  getList: async (params?: {
    page?: number
    page_size?: number
    name?: string
    status?: 'active' | 'inactive'
  }): Promise<PaginatedResponse<Personnel>> => {
    const response = await api.get<PaginatedResponse<Personnel>>(
      '/api/v1/personnel',
      { params }
    )
    return response.data
  },

  /**
   * 获取人员详情
   */
  getById: async (id: number): Promise<Personnel> => {
    const response = await api.get<Personnel>(`/api/v1/personnel/${id}`)
    return response.data
  },

  /**
   * 创建人员
   */
  create: async (data: PersonnelCreate): Promise<Personnel> => {
    const formData = new FormData()
    formData.append('name', data.name)
    if (data.id_number) {
      formData.append('id_number', data.id_number)
    }
    if (data.phone) {
      formData.append('phone', data.phone)
    }
    if (data.address) {
      formData.append('address', data.address)
    }
    if (data.gender) {
      formData.append('gender', data.gender)
    }
    if (data.category_id !== undefined && data.category_id !== null) {
      formData.append('category_id', String(data.category_id))
    }
    formData.append('photo', data.photo)

    const response = await api.post<Personnel>('/api/v1/personnel', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * 更新人员信息
   */
  update: async (id: number, data: PersonnelUpdate): Promise<Personnel> => {
    const formData = new FormData()
    if (data.name) {
      formData.append('name', data.name)
    }
    if (data.id_number !== undefined) {
      formData.append('id_number', data.id_number || '')
    }
    if (data.phone !== undefined) {
      formData.append('phone', data.phone || '')
    }
    if (data.address !== undefined) {
      formData.append('address', data.address || '')
    }
    if (data.gender !== undefined) {
      formData.append('gender', data.gender || '')
    }
    if (data.category_id !== undefined) {
      formData.append('category_id', data.category_id === null ? '' : String(data.category_id))
    }
    if (data.photo) {
      formData.append('photo', data.photo)
    }

    const response = await api.put<Personnel>(
      `/api/v1/personnel/${id}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  /**
   * 删除人员
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/personnel/${id}`)
  },
}

/**
 * 人员类别 API（无删除）
 */
export const personnelCategoriesApi = {
  getList: async (): Promise<PersonnelCategory[]> => {
    const response = await api.get<PersonnelCategory[]>('/api/v1/personnel-categories')
    return response.data
  },
  create: async (data: { name: string; sort_order?: number }): Promise<PersonnelCategory> => {
    const formData = new FormData()
    formData.append('name', data.name)
    if (data.sort_order !== undefined) {
      formData.append('sort_order', String(data.sort_order))
    }
    const response = await api.post<PersonnelCategory>(
      '/api/v1/personnel-categories',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },
  update: async (
    id: number,
    data: { name?: string; sort_order?: number }
  ): Promise<PersonnelCategory> => {
    const formData = new FormData()
    if (data.name !== undefined) {
      formData.append('name', data.name)
    }
    if (data.sort_order !== undefined) {
      formData.append('sort_order', String(data.sort_order))
    }
    const response = await api.put<PersonnelCategory>(
      `/api/v1/personnel-categories/${id}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },
}

export default api

