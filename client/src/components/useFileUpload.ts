import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryResult,
} from 'react-query'
import axios, { AxiosRequestConfig } from 'axios'
import { useState } from 'react'
import { IFileInfo, CvrFileType } from './useCSV'
import { fetchApi, ApiError } from './SupportTools/support-api'
import { addCSRFToken } from './utilities'

interface IUseFileUploadProps {
  url: string
  formKey: string
}

export interface IFileUpload {
  uploadedFile: UseQueryResult<IFileInfo, ApiError>
  uploadFiles: (files: FileList) => Promise<void>
  uploadProgress?: number
  deleteFile: () => Promise<void>
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

const useUploadFiles = <FormFields>(url: string) => {
  const [progress, setProgress] = useState<number>()

  const putFiles = async (formFields: FormFields) => {
    const formData = new FormData()
    for (const [key, value] of Object.entries(formFields)) {
      if (value instanceof FileList) {
        for (const file of value) {
          formData.append(key, file)
        }
      } else {
        formData.append(key, value)
      }
    }
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
    ...useMutation<void, ApiError, FormFields>(putFiles, {
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
  const cvrUrl = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/cvrs`
  const batchTalliesUrl = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-tallies`
  const jurisdictionsUrl = `/api/election/${electionId}/jurisdiction`
  const queryClient = useQueryClient()
  const invalidateQueries = () => {
    queryClient.invalidateQueries([cvrUrl])
    queryClient.invalidateQueries([batchTalliesUrl])
    queryClient.invalidateQueries([jurisdictionsUrl])
  }
  const uploadFiles = useUploadFiles(url)
  const deleteFile = useDeleteFile(url)
  return {
    uploadedFile: useUploadedFile(url, { onFileChange: invalidateQueries }),
    uploadFiles: files => uploadFiles.mutateAsync({ manifest: files }),
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/csv`,
  }
}

export const useBatchTallies = (
  electionId: string,
  jurisdictionId: string,
  options: { enabled: boolean } = { enabled: true }
): IFileUpload => {
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-tallies`
  const uploadFiles = useUploadFiles(url)
  const deleteFile = useDeleteFile(url)
  return {
    uploadedFile: useUploadedFile(url, options),
    uploadFiles: files => uploadFiles.mutateAsync({ batchTallies: files }),
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/csv`,
  }
}

interface ICvrsFileUpload extends Omit<IFileUpload, 'uploadFiles'> {
  uploadFiles: (cvrs: FileList, cvrFileType: CvrFileType) => Promise<void>
}

export const useCVRs = (
  electionId: string,
  jurisdictionId: string,
  options: { enabled: boolean } = { enabled: true }
): ICvrsFileUpload => {
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/cvrs`
  const uploadFiles = useUploadFiles(url)
  const deleteFile = useDeleteFile(url)
  return {
    uploadedFile: useUploadedFile(url, options),
    uploadFiles: (cvrs, cvrFileType) =>
      uploadFiles.mutateAsync({ cvrs, cvrFileType }),
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/csv`,
  }
}
