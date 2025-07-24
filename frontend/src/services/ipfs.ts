class IPFSService {
  private readonly IPFS_GATEWAY = 'https://ipfs.io/ipfs/'
  private readonly PINATA_API_URL = 'https://api.pinata.cloud'
  
  async uploadFile(file: File): Promise<string> {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch(`${this.PINATA_API_URL}/pinning/pinFileToIPFS`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${import.meta.env.VITE_PINATA_JWT}`,
        },
        body: formData,
      })
      
      if (!response.ok) {
        throw new Error('Failed to upload to IPFS')
      }
      
      const data = await response.json()
      return data.IpfsHash
    } catch (error) {
      console.error('IPFS upload error:', error)
      throw error
    }
  }
  
  async uploadJSON(data: any): Promise<string> {
    try {
      const response = await fetch(`${this.PINATA_API_URL}/pinning/pinJSONToIPFS`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${import.meta.env.VITE_PINATA_JWT}`,
        },
        body: JSON.stringify({
          pinataContent: data,
          pinataMetadata: {
            name: `study4me-${Date.now()}`,
          },
        }),
      })
      
      if (!response.ok) {
        throw new Error('Failed to upload JSON to IPFS')
      }
      
      const result = await response.json()
      return result.IpfsHash
    } catch (error) {
      console.error('IPFS JSON upload error:', error)
      throw error
    }
  }
  
  async fetchFromIPFS(hash: string): Promise<any> {
    try {
      const response = await fetch(`${this.IPFS_GATEWAY}${hash}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch from IPFS')
      }
      
      const contentType = response.headers.get('content-type')
      
      if (contentType?.includes('application/json')) {
        return await response.json()
      } else {
        return await response.text()
      }
    } catch (error) {
      console.error('IPFS fetch error:', error)
      throw error
    }
  }
  
  getIPFSUrl(hash: string): string {
    return `${this.IPFS_GATEWAY}${hash}`
  }
  
  extractHashFromUrl(url: string): string | null {
    const match = url.match(/\/ipfs\/([a-zA-Z0-9]+)/)
    return match ? match[1] : null
  }
}

export const ipfsService = new IPFSService()
export default ipfsService