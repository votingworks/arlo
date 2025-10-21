import { useState } from 'react'
import { useQuery, useMutation } from 'react-query'
import { fetchApi } from '../utils/api'
import { FileProcessingStatus } from './useCSV'

export interface IBundleStatus {
  bundleId: string
  bundleType: string
  status: {
    status: FileProcessingStatus
    startedAt: string | null
    completedAt: string | null
    error: string | null
  }
  downloadUrl?: string
  error?: string
}

const startBundleGeneration = async (
  electionId: string,
  bundleType: 'manifests' | 'candidate-totals'
): Promise<IBundleStatus> => {
  return fetchApi(
    `/api/election/${electionId}/batch-files/${bundleType}-bundle`,
    {
      method: 'POST',
    }
  )
}

const getBundleStatus = async (
  electionId: string,
  bundleId: string
): Promise<IBundleStatus> => {
  return fetchApi(`/api/election/${electionId}/batch-files/bundle/${bundleId}`)
}

export const useBatchFilesBundle = (
  electionId: string,
  bundleType: 'manifests' | 'candidate-totals'
): {
  startDownload: () => void
  reset: () => void
  isGenerating: boolean
  isComplete: boolean
  hasError: boolean
  error: unknown
  downloadUrl: string | undefined
} => {
  const [bundleId, setBundleId] = useState<string>()

  // Mutation to start bundle generation
  const startGeneration = useMutation(
    () => startBundleGeneration(electionId, bundleType),
    {
      onSuccess: data => {
        setBundleId(data.bundleId)
      },
    }
  )

  // Query to poll bundle status
  const statusQuery = useQuery(
    ['batch-files-bundle', electionId, bundleType, bundleId],
    () => getBundleStatus(electionId, bundleId!),
    {
      enabled: !!bundleId,
      refetchInterval: data => {
        // Poll every 2 seconds while processing
        if (
          data?.status.status === FileProcessingStatus.PROCESSING ||
          data?.status.status === FileProcessingStatus.READY_TO_PROCESS
        ) {
          return 2000
        }
        // Stop polling once complete or errored
        return false
      },
    }
  )

  const startDownload = () => {
    startGeneration.mutate()
  }

  const reset = () => {
    setBundleId(undefined)
    startGeneration.reset()
  }

  const isGenerating =
    startGeneration.isLoading ||
    statusQuery.data?.status.status === FileProcessingStatus.PROCESSING ||
    statusQuery.data?.status.status === FileProcessingStatus.READY_TO_PROCESS

  const isComplete =
    statusQuery.data?.status.status === FileProcessingStatus.PROCESSED

  const hasError =
    startGeneration.isError ||
    statusQuery.data?.status.status === FileProcessingStatus.ERRORED ||
    !!statusQuery.data?.error

  const downloadUrl = statusQuery.data?.downloadUrl

  return {
    startDownload,
    reset,
    isGenerating,
    isComplete,
    hasError,
    error: statusQuery.data?.error || startGeneration.error,
    downloadUrl,
  }
}
