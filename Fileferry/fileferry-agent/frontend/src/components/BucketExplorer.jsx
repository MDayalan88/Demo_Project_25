import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { FolderOpen, FileText, Download, Upload, RefreshCw } from 'lucide-react'
import { listBuckets, listBucketContents, initiateTransfer } from '../services/api'

export default function BucketExplorer() {
  const [buckets, setBuckets] = useState([])
  const [selectedBucket, setSelectedBucket] = useState(null)
  const [files, setFiles] = useState([])
  const [selectedFiles, setSelectedFiles] = useState([])

  const bucketsMutation = useMutation({
    mutationFn: listBuckets,
    onSuccess: (data) => setBuckets(data.buckets || []),
  })

  const filesMutation = useMutation({
    mutationFn: (bucket) => listBucketContents(bucket),
    onSuccess: (data) => setFiles(data.files || []),
  })

  const handleBucketClick = (bucket) => {
    setSelectedBucket(bucket)
    filesMutation.mutate(bucket.name)
  }

  const handleFileSelect = (file) => {
    setSelectedFiles((prev) =>
      prev.includes(file)
        ? prev.filter((f) => f !== file)
        : [...prev, file]
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">S3 Bucket Explorer</h2>
        <button
          onClick={() => bucketsMutation.mutate()}
          className="btn-primary"
          disabled={bucketsMutation.isPending}
        >
          <RefreshCw size={18} className={bucketsMutation.isPending ? 'animate-spin' : ''} />
          <span className="ml-2">Load Buckets</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Buckets List */}
        <div className="card">
          <h3 className="font-semibold mb-4 flex items-center">
            <FolderOpen className="mr-2" size={18} />
            S3 Buckets ({buckets.length})
          </h3>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {bucketsMutation.isPending ? (
              <div className="text-center py-8 text-gray-500">Loading buckets...</div>
            ) : buckets.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                Click "Load Buckets" to view your S3 buckets
              </div>
            ) : (
              buckets.map((bucket) => (
                <button
                  key={bucket.name}
                  onClick={() => handleBucketClick(bucket)}
                  className={`w-full text-left p-3 rounded-md transition-colors ${
                    selectedBucket?.name === bucket.name
                      ? 'bg-slack-purple text-white'
                      : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                >
                  <div className="font-medium">{bucket.name}</div>
                  <div className="text-xs opacity-75">{bucket.region}</div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Files List */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center">
              <FileText className="mr-2" size={18} />
              {selectedBucket ? `${selectedBucket.name} Contents` : 'Select a bucket'}
            </h3>
            {selectedFiles.length > 0 && (
              <span className="badge-info">{selectedFiles.length} selected</span>
            )}
          </div>

          {!selectedBucket ? (
            <div className="text-center py-16 text-gray-500">
              <FolderOpen size={48} className="mx-auto mb-4 opacity-50" />
              <p>Select a bucket to view its contents</p>
            </div>
          ) : filesMutation.isPending ? (
            <div className="text-center py-16 text-gray-500">Loading files...</div>
          ) : files.length === 0 ? (
            <div className="text-center py-16 text-gray-500">
              <FileText size={48} className="mx-auto mb-4 opacity-50" />
              <p>No files found in this bucket</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {files.map((file) => (
                <FileItem
                  key={file.key}
                  file={file}
                  selected={selectedFiles.includes(file)}
                  onSelect={() => handleFileSelect(file)}
                />
              ))}
            </div>
          )}

          {selectedFiles.length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-200 flex space-x-3">
              <button className="btn-primary flex-1">
                <Upload size={18} />
                <span className="ml-2">Transfer to FTP/SFTP</span>
              </button>
              <button className="btn-secondary">
                <Download size={18} />
                <span className="ml-2">Download</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function FileItem({ file, selected, onSelect }) {
  return (
    <div
      className={`flex items-center p-3 rounded-md border transition-colors cursor-pointer ${
        selected
          ? 'bg-slack-purple/10 border-slack-purple'
          : 'bg-white border-gray-200 hover:bg-gray-50'
      }`}
      onClick={onSelect}
    >
      <input
        type="checkbox"
        checked={selected}
        onChange={() => {}}
        className="mr-3"
      />
      <FileText size={16} className="mr-3 text-gray-400" />
      <div className="flex-1">
        <div className="font-medium text-sm">{file.key}</div>
        <div className="text-xs text-gray-500">
          {formatBytes(file.size)} • {new Date(file.last_modified).toLocaleDateString()}
        </div>
      </div>
    </div>
  )
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
