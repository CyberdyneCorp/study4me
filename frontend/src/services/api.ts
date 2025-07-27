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

interface QueryResponse {
  result: string
  processing_method: string
  processing_time_seconds: number
  total_time_seconds: number
  study_topic_id: string
  study_topic_name: string
  use_knowledge_graph: boolean
}

interface ContentItem {
  content_id: string
  content_type: string
  title: string
  content: string
  source_url?: string
  file_path?: string
  metadata?: any
  created_at: string
  content_length: number
  number_tokens: number
}

interface StudyTopicContentResponse {
  topic_id: string
  topic_name: string
  topic_description: string
  use_knowledge_graph: boolean
  content_items_count: number
  total_content_length: number
  number_tokens: number
  content_items: ContentItem[]
}

interface StudyTopicSummaryResponse {
  topic_id: string
  topic_name: string
  topic_description: string
  summary: string
  content_items_processed: number
  total_content_length: number
  total_content_tokens: number
  summary_length: number
  processing_time_seconds: number
  total_time_seconds: number
  generated_at: number
}

interface StudyTopicMindmapResponse {
  topic_id: string
  topic_name: string
  topic_description: string
  mindmap: string
  content_items_processed: number
  total_content_length: number
  total_content_tokens: number
  mindmap_length: number
  processing_time_seconds: number
  total_time_seconds: number
  generated_at: number
  cached: boolean
}

interface LectureRequest {
  language: string
  focus_topic?: string
  force?: boolean
}

interface StudyTopicLectureResponse {
  topic_id: string
  topic_name: string
  topic_description: string
  lecture: string
  lecture_speech: string
  language: string
  focus_topic?: string
  content_items_processed: number
  total_content_length: number
  total_content_tokens: number
  lecture_length: number
  lecture_speech_length: number
  processing_time_seconds: number
  total_time_seconds: number
  generated_at: number
  cached: boolean
}

interface LectureStatusResponse {
  topic_id: string
  topic_name: string
  has_lecture: boolean
  lecture_count: number
  latest_lecture?: {
    language: string
    focus_topic?: string
    cached: boolean
    lecture_length: number
    generated_at: number
  }
  generated_at?: number
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

  async getStudyTopicContent(topicId: string): Promise<StudyTopicContentResponse> {
    const response = await this.request<StudyTopicContentResponse>(`/study-topics/${topicId}/content`)
    return response as unknown as StudyTopicContentResponse
  }

  async summarizeStudyTopicContent(topicId: string): Promise<StudyTopicSummaryResponse> {
    const response = await this.request<StudyTopicSummaryResponse>(`/study-topics/${topicId}/summarize`)
    return response as unknown as StudyTopicSummaryResponse
  }

  async generateStudyTopicMindmap(topicId: string): Promise<StudyTopicMindmapResponse> {
    const response = await this.request<StudyTopicMindmapResponse>(`/study-topics/${topicId}/mindmap`)
    return response as unknown as StudyTopicMindmapResponse
  }

  async checkLectureStatus(topicId: string): Promise<LectureStatusResponse> {
    const response = await this.request<LectureStatusResponse>(`/study-topics/${topicId}/lecture/status`)
    return response as unknown as LectureStatusResponse
  }
  
  async generateStudyTopicLecture(topicId: string, lectureRequest: LectureRequest): Promise<StudyTopicLectureResponse> {
    const response = await this.request<StudyTopicLectureResponse>(`/study-topics/${topicId}/lecture`, {
      method: 'POST',
      body: JSON.stringify(lectureRequest),
    })
    return response as unknown as StudyTopicLectureResponse
  }

  // === Knowledge Upload Methods ===

  async uploadDocuments(files: File[], studyTopicId: string): Promise<UploadDocumentsResponse> {
    const formData = new FormData()
    
    // Add each file to the form data
    files.forEach(file => {
      formData.append('files', file)
    })
    
    // Add study topic ID
    formData.append('study_topic_id', studyTopicId)
    
    const response = await this.request<UploadDocumentsResponse>('/documents/upload', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it with boundary for FormData
      body: formData,
    })
    
    return response as unknown as UploadDocumentsResponse
  }

  async processWebpage(url: string, studyTopicId: string): Promise<ProcessWebpageResponse> {
    const response = await this.request<ProcessWebpageResponse>('/webpage/process', {
      method: 'POST',
      body: JSON.stringify({
        url,
        study_topic_id: studyTopicId
      }),
    })
    
    return response as unknown as ProcessWebpageResponse
  }

  async processYouTubeVideo(url: string, studyTopicId: string): Promise<ProcessYouTubeResponse> {
    const formData = new FormData()
    formData.append('url', url)
    formData.append('study_topic_id', studyTopicId)
    
    const response = await this.request<ProcessYouTubeResponse>('/youtube/process', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it with boundary for FormData
      body: formData,
    })
    
    return response as unknown as ProcessYouTubeResponse
  }

  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const response = await this.request<TaskStatusResponse>(`/task-status/${taskId}`)
    return response as unknown as TaskStatusResponse
  }

  // === Query System ===

  async queryStudyTopic(studyTopicId: string, query: string, mode: string = 'hybrid'): Promise<QueryResponse> {
    const encodedQuery = encodeURIComponent(query)
    const response = await this.request<QueryResponse>(`/query?query=${encodedQuery}&study_topic_id=${studyTopicId}&mode=${mode}`)
    return response as unknown as QueryResponse
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

  // === MCP Status ===

  async getMcpStatus(): Promise<McpStatusResponse> {
    const response = await this.request<McpStatusResponse>('/mcp/status')
    return response as unknown as McpStatusResponse
  }

  // === API Status ===

  async getApiStatus(): Promise<ApiStatusResponse> {
    const response = await this.request<ApiStatusResponse>('/api-status')
    return response as unknown as ApiStatusResponse
  }

  // === Content Management ===

  async deleteContent(contentId: string): Promise<DeleteContentResponse> {
    const response = await this.request<DeleteContentResponse>(`/content/${contentId}`, {
      method: 'DELETE',
    })
    return response as unknown as DeleteContentResponse
  }

  // === Text-to-Speech Methods ===

  async listVoices(): Promise<VoicesResponse> {
    const response = await this.request<VoicesResponse>('/tts/voices')
    return response as unknown as VoicesResponse
  }

  async textToSpeech(ttsRequest: TTSRequest): Promise<Blob> {
    const url = `${API_BASE_URL}/tts/text-to-speech`
    
    const config: RequestInit = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(ttsRequest),
    }
    
    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'TTS generation failed')
      }
      
      // Return the audio blob directly
      return await response.blob()
    } catch (error) {
      console.error('TTS Error:', error)
      throw error
    }
  }

  async getVoiceSettings(voiceType: string = 'default'): Promise<VoiceSettingsResponse> {
    const response = await this.request<VoiceSettingsResponse>(`/tts/voice-settings/${voiceType}`)
    return response as unknown as VoiceSettingsResponse
  }
}

export const apiService = new ApiService()
export default apiService

// Export types for use in components
// === Knowledge Upload Types ===

interface UploadDocumentsResponse {
  status: string
  files: string[]
  task_id: string
  study_topic_id: string
  study_topic_name: string
}

interface ProcessWebpageResponse {
  status: string
  url: string
  task_id: string
  study_topic_id: string
  study_topic_name: string
  content_id: string
}

interface ProcessYouTubeResponse {
  status: string
  task_id: string
  url: string
  study_topic_id: string
  study_topic_name: string
  content_id: string
  message: string
}

interface TaskStatusResponse {
  task_id: string
  status: 'processing' | 'done' | 'failed'
  result?: any
  processing_time_seconds?: number
}

interface McpStatusResponse {
  status: 'running' | 'installed_not_running' | 'not_configured' | 'not_installed' | 'unknown' | 'error'
  server_file_exists: boolean
  config_file_exists: boolean
  server_running: boolean
  server_url: string
  server_url_source: string
  server_error?: string
  environment: {
    openai_api_key_set: boolean
    db_path_set: boolean
    rag_dir_set: boolean
  }
  config?: any
  error?: string
  timestamp: number
}

interface DeleteContentResponse {
  message: string
  content_id: string
  title: string
  content_type: string
  study_topic_id: string
  file_deleted: boolean
}

interface ApiStatusResponse {
  openai_configured: boolean
  elevenlabs_configured: boolean
  elevenlabs_key_length: number
  tts_available: boolean
}

// === Text-to-Speech Types ===
interface TTSRequest {
  text: string
  voice_id: string
  model_id?: string
  voice_settings?: {
    stability?: number
    similarity_boost?: number
    style?: number
    use_speaker_boost?: boolean
  }
  output_format?: string
  language_code?: string
  enable_logging?: boolean
}

interface VoiceInfo {
  voice_id: string
  name: string
  category: string
  description: string
  preview_url?: string
  settings: any
  labels: any
  available_for_tiers: string[]
  high_quality_base_model_ids: string[]
}

interface VoicesResponse {
  status: string
  total_voices: number
  voices: VoiceInfo[]
  processing_time_seconds: number
}

interface VoiceSettingsResponse {
  voice_type: string
  settings: {
    stability: number
    similarity_boost: number
    style: number
    use_speaker_boost: boolean
  }
  description: string
}

export type {
  StudyTopic,
  CreateStudyTopicRequest,
  CreateStudyTopicResponse,
  StudyTopicsListResponse,
  QueryResponse,
  ContentItem,
  StudyTopicContentResponse,
  StudyTopicSummaryResponse,
  StudyTopicMindmapResponse,
  LectureRequest,
  LectureStatusResponse,
  StudyTopicLectureResponse,
  UploadDocumentsResponse,
  ProcessWebpageResponse,
  ProcessYouTubeResponse,
  TaskStatusResponse,
  McpStatusResponse,
  DeleteContentResponse,
  ApiStatusResponse,
  TTSRequest,
  VoiceInfo,
  VoicesResponse,
  VoiceSettingsResponse
}