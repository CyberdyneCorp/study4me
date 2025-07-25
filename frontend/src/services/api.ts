const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

interface ApiResponse<T> {
  data: T
  message?: string
  error?: string
}

interface StudyTopic {
  topic_id: string
  name: string
  description: string | null
  use_knowledge_graph: boolean
  created_at: string
  updated_at: string
}

interface CreateStudyTopicRequest {
  name: string
  description?: string
  use_knowledge_graph?: boolean
}

interface CreateStudyTopicResponse {
  message: string
  topic_id: string
  name: string
  description: string | null
  use_knowledge_graph: boolean
}

interface StudyTopicsListResponse {
  total_retrieved: number
  limit: number
  offset: number
  topics: StudyTopic[]
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
  
  // === Study Topics Management ===
  
  async createStudyTopic(data: CreateStudyTopicRequest): Promise<CreateStudyTopicResponse> {
    const response = await this.request<CreateStudyTopicResponse>('/study-topics', {
      method: 'POST',
      body: JSON.stringify({
        name: data.name,
        description: data.description || null,
        use_knowledge_graph: data.use_knowledge_graph ?? true
      }),
    })
    
    // The backend returns the data directly, not wrapped in a 'data' property
    return response as unknown as CreateStudyTopicResponse
  }
  
  async getStudyTopics(limit = 100, offset = 0): Promise<StudyTopicsListResponse> {
    const response = await this.request<StudyTopicsListResponse>(`/study-topics?limit=${limit}&offset=${offset}`)
    return response as unknown as StudyTopicsListResponse
  }
  
  async getStudyTopic(topicId: string): Promise<StudyTopic> {
    const response = await this.request<StudyTopic>(`/study-topics/${topicId}`)
    return response as unknown as StudyTopic
  }
  
  async updateStudyTopic(topicId: string, data: Partial<CreateStudyTopicRequest>): Promise<{ message: string; topic: StudyTopic }> {
    const response = await this.request<{ message: string; topic: StudyTopic }>(`/study-topics/${topicId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    return response as unknown as { message: string; topic: StudyTopic }
  }
  
  async deleteStudyTopic(topicId: string): Promise<{ message: string; topic_id: string; name: string }> {
    const response = await this.request<{ message: string; topic_id: string; name: string }>(`/study-topics/${topicId}`, {
      method: 'DELETE',
    })
    return response as unknown as { message: string; topic_id: string; name: string }
  }

  // === Legacy Topic Methods (keeping for compatibility) ===

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

// Export types for use in components
export type {
  StudyTopic,
  CreateStudyTopicRequest,
  CreateStudyTopicResponse,
  StudyTopicsListResponse
}