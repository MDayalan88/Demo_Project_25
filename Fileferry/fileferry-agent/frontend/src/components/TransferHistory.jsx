import { useQuery } from '@tanstack/react-query'
import { Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { fetchTransferHistory } from '../services/api'

export default function TransferHistory() {
  const { data: transfers, isLoading } = useQuery({
    queryKey: ['transfer-history'],
    queryFn: fetchTransferHistory,
  })

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Transfer History</h2>

      <div className="card">
        {isLoading ? (
          <div className="text-center py-12 text-gray-500">Loading history...</div>
        ) : !transfers || transfers.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No transfer history found</div>
        ) : (
          <div className="space-y-4">
            {transfers.map((transfer) => (
              <TransferHistoryCard key={transfer.id} transfer={transfer} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function TransferHistoryCard({ transfer }) {
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

  const config = statusConfig[transfer.status] || statusConfig.in_progress
  const Icon = config.icon

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <div className={`w-10 h-10 ${config.bg} rounded-lg flex items-center justify-center`}>
              <Icon size={20} className={config.color} />
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">{transfer.file_name}</h4>
              <p className="text-sm text-gray-600">
                {transfer.source_bucket} → {transfer.destination}
              </p>
            </div>
          </div>

          <div className="ml-13 space-y-1 text-sm text-gray-600">
            <p>Transfer ID: {transfer.id}</p>
            <p>Started: {new Date(transfer.started_at).toLocaleString()}</p>
            {transfer.completed_at && (
              <p>Completed: {new Date(transfer.completed_at).toLocaleString()}</p>
            )}
          </div>
        </div>

        <span className={config.badge}>{transfer.status.replace('_', ' ')}</span>
      </div>
    </div>
  )
}
