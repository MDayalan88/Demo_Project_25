import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Dashboard APIs
export const fetchDashboardStats = async () => {
  const { data } = await api.get('/dashboard/stats')
  return data
}

export const fetchRecentTransfers = async () => {
  const { data } = await api.get('/dashboard/recent-transfers')
  return data
}

// S3 Bucket APIs
export const listBuckets = async () => {
  const { data } = await api.post('/s3/list-buckets', {
    user_id: 'slack_user_123',
    region: 'us-east-1',
  })
  return data
}

export const listBucketContents = async (bucketName) => {
  const { data } = await api.post('/s3/list-contents', {
    user_id: 'slack_user_123',
    bucket_name: bucketName,
  })
  return data
}

// Transfer APIs
export const createTransferRequest = async (transferData) => {
  const { data } = await api.post('/transfer/create', {
    ...transferData,
    user_id: 'slack_user_123',
  })
  return data
}

export const fetchTransferHistory = async () => {
  const { data } = await api.get('/transfer/history', {
    params: { user_id: 'slack_user_123' },
  })
  return data
}

export const initiateTransfer = async (files, destination) => {
  const { data } = await api.post('/transfer/initiate', {
    user_id: 'slack_user_123',
    files,
    destination,
  })
  return data
}

// AI Chat API
export const sendChatMessage = async ({ message, user_id }) => {
  const { data } = await api.post('/chat/message', {
    user_id,
    message,
  })
  return data
}

export default api
