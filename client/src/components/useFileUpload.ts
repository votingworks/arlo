import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryResult,
} from 'react-query'
import axios, { AxiosRequestConfig } from 'axios'
import { useState, useRef } from 'react'
import { IFileInfo, CvrFileType } from './useCSV'
import { fetchApi, ApiError, addCSRFToken } from '../utils/api'

interface IUseFileUploadProps {
  url: string
  formKey: string
}

export interface IFileUpload {
  uploadedFile: UseQueryResult<IFileInfo, ApiError>
  uploadFiles: (files: File[]) => Promise<void>
  uploadProgress?: number
  deleteFile: () => Promise<void>
  downloadFileUrl?: string
}

export const useUploadedFile = (
  key: string[],
  url: string,
  options: { onFileChange?: () => void; enabled?: boolean } = {}
) => {
  const isFirstFetch = useRef(true)
  const isProcessing = (fileInfo?: IFileInfo) =>
    fileInfo && fileInfo.processing && !fileInfo.processing.completedAt
  return useQuery<IFileInfo, ApiError>(key, () => fetchApi(url), {
    // When a file input dialog closes, it triggers a window focus event,
    // which causes a refetch by default, so we turn that off.
    // https://github.com/tannerlinsley/react-query/issues/2960
    refetchOnWindowFocus: false,
    refetchInterval: fileInfo => (isProcessing(fileInfo) ? 1000 : false),
    // Once a file is finished processing or is deleted, call onFileChange
    // (but don't call it the very first time we load the file)
    onSuccess: fileInfo => {
      if (isFirstFetch.current) {
        isFirstFetch.current = false
        return
      }
      if (!isProcessing(fileInfo) && options.onFileChange) {
        options.onFileChange()
      }
    },
    enabled: options.enabled,
  })
}

export const useUploadFiles = (key: string[], url: string) => {
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
    } finally {
      setProgress(undefined)
    }
  }

  const queryClient = useQueryClient()

  return {
    ...useMutation<void, ApiError, FormData>(putFiles, {
      onSuccess: () => queryClient.invalidateQueries(key),
    }),
    progress,
  }
}

export const useDeleteFile = (key: string[], url: string) => {
  const deleteFile = () => fetchApi(url, { method: 'DELETE' })
  const queryClient = useQueryClient()
  return useMutation<void, ApiError, void>(deleteFile, {
    onSuccess: () => queryClient.invalidateQueries(key),
  })
}

export const useBallotManifest = (
  electionId: string,
  jurisdictionId: string
): IFileUpload => {
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/ballot-manifest`
  const key = ['jurisdictions', jurisdictionId, 'ballot-manifest']
  const uploadFiles = useUploadFiles(key, url)
  const deleteFile = useDeleteFile(key, url)
  const queryClient = useQueryClient()
  return {
    uploadedFile: useUploadedFile(key, url, {
      onFileChange: () => {
        // When the manifest changes, batch tallies and cvrs are reprocessed
        queryClient.invalidateQueries([
          'jurisdictions',
          jurisdictionId,
          'batch-tallies',
        ])
        queryClient.invalidateQueries(['jurisdictions', jurisdictionId, 'cvrs'])
        // We need to reload the jurisdictions list with new file upload status
        queryClient.invalidateQueries([
          'elections',
          electionId,
          'jurisdictions',
        ])
      },
    }),
    uploadFiles: files => {
      const formData = new FormData()
      formData.append('manifest', files[0], files[0].name)
      return uploadFiles.mutateAsync(formData)
    },
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
  const key = ['jurisdictions', jurisdictionId, 'batch-tallies']
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-tallies`
  const uploadFiles = useUploadFiles(key, url)
  const deleteFile = useDeleteFile(key, url)
  const queryClient = useQueryClient()
  return {
    uploadedFile: useUploadedFile(key, url, {
      ...options,
      onFileChange: () => {
        // We need to reload the jurisdictions list with new file upload status
        queryClient.invalidateQueries([
          'elections',
          electionId,
          'jurisdictions',
        ])
      },
    }),
    uploadFiles: files => {
      const formData = new FormData()
      formData.append('batchTallies', files[0], files[0].name)
      return uploadFiles.mutateAsync(formData)
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/csv`,
  }
}

interface ICvrsFileUpload extends Omit<IFileUpload, 'uploadFiles'> {
  uploadFiles: (cvrs: File[], cvrFileType: CvrFileType) => Promise<void>
}

export const useCVRs = (
  electionId: string,
  jurisdictionId: string,
  options: { enabled: boolean } = { enabled: true }
): ICvrsFileUpload => {
  const key = ['jurisdictions', jurisdictionId, 'cvrs']
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/cvrs`
  const uploadFiles = useUploadFiles(key, url)
  const deleteFile = useDeleteFile(key, url)
  const queryClient = useQueryClient()
  return {
    uploadedFile: useUploadedFile(key, url, {
      ...options,
      onFileChange: () => {
        // We need to reload the jurisdictions list with new file upload status
        queryClient.invalidateQueries([
          'elections',
          electionId,
          'jurisdictions',
        ])
      },
    }),
    uploadFiles: (files, cvrFileType) => {
      const formData = new FormData()
      for (const file of files) {
        formData.append('cvrs', file, file.name)
      }
      formData.append('cvrFileType', cvrFileType)
      return uploadFiles.mutateAsync(formData)
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/csv`,
  }
}
