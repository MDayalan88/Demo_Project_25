import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, CheckCircle } from 'lucide-react'
import { createTransferRequest } from '../services/api'

export default function TransferRequest() {
  const [formData, setFormData] = useState({
    source_bucket: '',
    source_key: '',
    destination_type: 'ftp',
    destination_host: '',
    destination_path: '',
    destination_user: '',
    destination_password: '',
    priority: 'medium',
  })

  const mutation = useMutation({
    mutationFn: createTransferRequest,
    onSuccess: () => {
      alert('Transfer request submitted successfully!')
      setFormData({
        source_bucket: '',
        source_key: '',
        destination_type: 'ftp',
        destination_host: '',
        destination_path: '',
        destination_user: '',
        destination_password: '',
        priority: 'medium',
      })
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="card">
        <h2 className="text-2xl font-bold mb-6">Create Transfer Request</h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Source Section */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mr-2">
                1
              </div>
              Source (S3)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 ml-10">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  S3 Bucket
                </label>
                <input
                  type="text"
                  value={formData.source_bucket}
                  onChange={(e) => setFormData({ ...formData, source_bucket: e.target.value })}
                  className="input"
                  placeholder="my-bucket"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  File Path/Key
                </label>
                <input
                  type="text"
                  value={formData.source_key}
                  onChange={(e) => setFormData({ ...formData, source_key: e.target.value })}
                  className="input"
                  placeholder="path/to/file.txt"
                  required
                />
              </div>
            </div>
          </div>

          {/* Destination Section */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center mr-2">
                2
              </div>
              Destination
            </h3>
            <div className="space-y-4 ml-10">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Transfer Type
                </label>
                <select
                  value={formData.destination_type}
                  onChange={(e) => setFormData({ ...formData, destination_type: e.target.value })}
                  className="input"
                >
                  <option value="ftp">FTP</option>
                  <option value="sftp">SFTP</option>
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Host/Server
                  </label>
                  <input
                    type="text"
                    value={formData.destination_host}
                    onChange={(e) => setFormData({ ...formData, destination_host: e.target.value })}
                    className="input"
                    placeholder="ftp.example.com"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Destination Path
                  </label>
                  <input
                    type="text"
                    value={formData.destination_path}
                    onChange={(e) => setFormData({ ...formData, destination_path: e.target.value })}
                    className="input"
                    placeholder="/upload/"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Username
                  </label>
                  <input
                    type="text"
                    value={formData.destination_user}
                    onChange={(e) => setFormData({ ...formData, destination_user: e.target.value })}
                    className="input"
                    placeholder="username"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    value={formData.destination_password}
                    onChange={(e) => setFormData({ ...formData, destination_password: e.target.value })}
                    className="input"
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Options Section */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <div className="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center mr-2">
                3
              </div>
              Options
            </h3>
            <div className="ml-10">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority
              </label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="input max-w-xs"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>

          {/* Submit */}
          <div className="flex items-center justify-between pt-6 border-t border-gray-200">
            <div className="text-sm text-gray-600">
              <CheckCircle size={16} className="inline mr-1" />
              ServiceNow tickets will be created automatically
            </div>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="btn-primary px-8"
            >
              {mutation.isPending ? (
                'Submitting...'
              ) : (
                <>
                  <Send size={18} />
                  <span className="ml-2">Submit Transfer</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
