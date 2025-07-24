const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface ApiResponse<T> {
  data: T
  message?: string
  error?: string
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }
    
    try {
      const response = await fetch(url, config)
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || 'API request failed')
      }
      
      return data
    } catch (error) {
      console.error('API Error:', error)
      throw error
    }
  }
  
  async getTopics() {
    return this.request<any[]>('/api/topics')
  }
  
  async getTopic(id: string) {
    return this.request<any>(`/api/topics/${id}`)
  }
  
  async createTopic(data: {
    title: string
    description: string
    content_file?: File
    content_url?: string
  }) {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('description', data.description)
    
    if (data.content_file) {
      formData.append('content_file', data.content_file)
    }
    
    if (data.content_url) {
      formData.append('content_url', data.content_url)
    }
    
    return this.request<any>('/api/topics', {
      method: 'POST',
      headers: {},
      body: formData,
    })
  }
  
  async updateTopic(id: string, data: Partial<any>) {
    return this.request<any>(`/api/topics/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }
  
  async deleteTopic(id: string) {
    return this.request<void>(`/api/topics/${id}`, {
      method: 'DELETE',
    })
  }
  
  async queryTopic(topicId: string, query: string) {
    return this.request<{ answer: string }>('/api/query', {
      method: 'POST',
      body: JSON.stringify({ topic_id: topicId, query }),
    })
  }
  
  async generateAudioSummary(topicId: string) {
    return this.request<{ audio_url: string }>(`/api/topics/${topicId}/audio`, {
      method: 'POST',
    })
  }
  
  async getGraphData(topicId: string) {
    return this.request<any>(`/api/topics/${topicId}/graph`)
  }
}

export const apiService = new ApiService()
export default apiService