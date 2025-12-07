import { CheckCircle, Clock, XCircle, FileText, FileArchive, FileSpreadsheet, ExternalLink } from 'lucide-react'

export default function TransferCard({ transfer }) {
  const statusConfig = {
    completed: {
      icon: CheckCircle,
      color: 'text-green-600',
      bg: 'bg-green-50',
      badge: 'badge-success',
    },
    failed: {
      icon: XCircle,
      color: 'text-red-600',
      bg: 'bg-red-50',
      badge: 'badge-error',
    },
    in_progress: {
      icon: Clock,
      color: 'text-yellow-600',
      bg: 'bg-yellow-50',
      badge: 'badge-warning',
    },
  }

  const getFileIcon = (fileName) => {
    const ext = fileName?.split('.').pop()?.toLowerCase()
    if (ext === 'csv' || ext === 'xlsx') return <FileSpreadsheet className="w-6 h-6 text-green-600" />
    if (ext === 'zip' || ext === 'tar' || ext === 'gz') return <FileArchive className="w-6 h-6 text-orange-600" />
    return <FileText className="w-6 h-6 text-blue-600" />
  }

  const config = statusConfig[transfer.status] || statusConfig.in_progress
  const Icon = config.icon

  return (
    <div className="card animate-slide-up hover:shadow-xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 flex-1">
          <div className={`w-12 h-12 ${config.bg} rounded-xl flex items-center justify-center shadow-sm`}>
            {getFileIcon(transfer.file_name)}
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h4 className="font-semibold text-gray-900 text-lg">{transfer.file_name}</h4>
              {transfer.servicenow_ticket && (
                <a 
                  href={`https://dev329630.service-now.com/nav_to.do?uri=incident.do?sysparm_query=number=${transfer.servicenow_ticket}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="servicenow-ticket"
                  title="View ServiceNow Ticket"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span className="servicenow-badge">{transfer.servicenow_ticket}</span>
                </a>
              )}
            </div>
            <p className="text-sm text-gray-600 mt-1 flex items-center">
              <span className="font-medium">{transfer.source}</span>
              <span className="mx-2">→</span>
              <span className="font-medium">{transfer.destination}</span>
            </p>
            {transfer.file_size && (
              <p className="text-xs text-gray-500 mt-1">
                Size: {(transfer.file_size / 1024 / 1024).toFixed(2)} MB
              </p>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end space-y-2">
          <div className="flex items-center space-x-2">
            <span className={`status-indicator status-${transfer.status === 'completed' ? 'success' : transfer.status === 'failed' ? 'error' : 'pending'}`}></span>
            <span className={config.badge}>
              <Icon size={14} className="inline mr-1" />
              {transfer.status}
            </span>
          </div>
          <span className="text-sm text-gray-500 font-medium">
            {new Date(transfer.timestamp).toLocaleString()}
          </span>
        </div>
      </div>
      
      {transfer.progress !== undefined && transfer.status === 'in_progress' && (
        <div className="mt-4">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>Progress</span>
            <span className="font-semibold">{transfer.progress}%</span>
          </div>
          <div className="transfer-progress">
            <div 
              className="transfer-progress-bar" 
              style={{ width: `${transfer.progress}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  )
}
