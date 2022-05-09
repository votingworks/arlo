import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryResult,
  UseMutationResult,
} from 'react-query'
import axios, { AxiosRequestConfig } from 'axios'
import { useState } from 'react'
import { IFileInfo } from './useCSV'
import { fetchApi, ApiError } from './SupportTools/support-api'
import { addCSRFToken } from './utilities'

interface IUseFileUploadProps {
  url: string
  formKey: string
}

export interface IFileUpload {
  uploadedFile: UseQueryResult<IFileInfo, ApiError>
  uploadFiles: UseMutationResult<void, ApiError, FormData> & {
    progress?: number
  }
  deleteFile?: UseMutationResult<void, ApiError, void>
  downloadFileUrl?: string
}

const useUploadedFile = (
  url: string,
  options: { onFileChange?: () => void; enabled?: boolean } = {}
) => {
  const isProcessing = (fileInfo?: IFileInfo) =>
    fileInfo && fileInfo.processing && !fileInfo.processing.completedAt
  return useQuery<IFileInfo, ApiError>(url, () => fetchApi(url), {
    refetchInterval: fileInfo => (isProcessing(fileInfo) ? 1000 : false),
    onSuccess: fileInfo => {
      if (!isProcessing(fileInfo) && options.onFileChange)
        options.onFileChange()
    },
    enabled: options.enabled,
  })
}

const useUploadFiles = (url: string) => {
  const [progress, setProgress] = useState<number>()

  const putFiles = async (formData: FormData) => {
    try {
      await axios(url, addCSRFToken({
        method: 'PUT',
        data: formData,
        onUploadProgress: progressEvent =>
          setProgress(progressEvent.loaded / progressEvent.total),
      }) as AxiosRequestConfig)
    } catch (error) {
      const { errors } = error.response.data
      const message =
        errors && errors.length ? errors[0].message : error.response.statusText
      throw new ApiError(message, error.response.status)
    }
  }

  const queryClient = useQueryClient()

  return {
    ...useMutation<void, ApiError, FormData>(putFiles, {
      onSuccess: () => queryClient.invalidateQueries(url),
    }),
    progress,
  }
}

const useDeleteFile = (url: string) => {
  const deleteFile = () => fetchApi(url, { method: 'DELETE' })
  const queryClient = useQueryClient()
  return useMutation<void, ApiError, void>(deleteFile, {
    onSuccess: () => queryClient.invalidateQueries(url),
  })
}

export const useBallotManifest = (
  electionId: string,
  jurisdictionId: string
): IFileUpload => {
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/ballot-manifest`
  const cvrUrl = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/cvr`
  const batchTalliesUrl = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-tallies`
  const jurisdictionsUrl = `/api/election/${electionId}/jurisdiction`
  const queryClient = useQueryClient()
  const invalidateQueries = () => {
    queryClient.invalidateQueries([cvrUrl])
    queryClient.invalidateQueries([batchTalliesUrl])
    queryClient.invalidateQueries([jurisdictionsUrl])
  }

  return {
    uploadedFile: useUploadedFile(url, { onFileChange: invalidateQueries }),
    uploadFiles: useUploadFiles(url),
    deleteFile: useDeleteFile(url),
    downloadFileUrl: `${url}/csv`,
  }
}

export const useBatchTallies = (
  electionId: string,
  jurisdictionId: string,
  options: { enabled: boolean } = { enabled: true }
): IFileUpload => {
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-tallies`
  return {
    uploadedFile: useUploadedFile(url, options),
    uploadFiles: useUploadFiles(url),
    deleteFile: useDeleteFile(url),
    downloadFileUrl: `${url}/csv`,
  }
}

export const useCVRs = (
  electionId: string,
  jurisdictionId: string,
  options: { enabled: boolean } = { enabled: true }
): IFileUpload => {
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/cvrs`
  return {
    uploadedFile: useUploadedFile(url, options),
    uploadFiles: useUploadFiles(url),
    deleteFile: useDeleteFile(url),
    downloadFileUrl: `${url}/csv`,
  }
}
