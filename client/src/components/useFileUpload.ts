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
import { jurisdictionsQueryKey } from './useJurisdictions'
import { contestChoiceNameStandardizationsQueryKey } from './useContestChoiceNameStandardizations'
import { contestsQueryKey } from './useContests'

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

/**
 * useUploadedFile loads the current uploaded file state from the server. If the
 * file is processing, it will refetch the file status every second. It takes an
 * optional argument options.onFileChange, which will be called whenever the
 * uploaded file on the server changes (i.e. when a new file finishes processing
 * or when a file is deleted). It is not called when the file state is first
 * loaded from the server, nor when a file is processing.
 */
// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const useUploadedFile = (
  key: string[],
  url: string,
  options: { onFileChange?: () => void; enabled?: boolean } = {}
) => {
  const isFirstFetch = useRef(true)
  const isProcessing = (fileInfo?: IFileInfo) =>
    fileInfo && fileInfo.processing && !fileInfo.processing.completedAt
  return useQuery<IFileInfo, ApiError>(key, () => fetchApi(url), {
    refetchInterval: fileInfo => (isProcessing(fileInfo) ? 1000 : false),
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

type CompleteFileUploadArgs = {
  file: File
  cvrFileType?: CvrFileType
}

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const useUploadFiles = (key: string[], url: string) => {
  const [progress, setProgress] = useState<number>()

  const completeFileUpload = async ({
    file,
    cvrFileType,
  }: CompleteFileUploadArgs): Promise<void> => {
    try {
      // Get the signed s3 URL for the file upload
      const params = cvrFileType
        ? {
            fileType: file.type,
            cvrFileType,
          }
        : {
            fileType: file.type,
          }
      const getUploadResponse = await axios(
        `${url}/upload-url`,
        addCSRFToken({
          method: 'GET',
          params,
        }) as AxiosRequestConfig
      )

      // Upload the file to s3
      const uploadFileFormData = new FormData()
      Object.entries(getUploadResponse.data.fields).forEach(([k, v]) => {
        uploadFileFormData.append(k, v as string)
      })
      uploadFileFormData.append('Content-Type', file.type)
      uploadFileFormData.append('file', file, file.name)

      await axios(
        getUploadResponse.data.url,
        addCSRFToken({
          method: 'POST',
          data: uploadFileFormData,
          onUploadProgress: p => setProgress(p.loaded / p.total),
        }) as AxiosRequestConfig
      )

      const jsonData = {
        fileName: file.name,
        fileType: file.type,
        ...(cvrFileType && { cvrFileType }),
        storagePathKey: getUploadResponse.data.fields.key,
      }
      await axios(
        `${url}/upload-complete`,
        addCSRFToken({
          method: 'POST',
          data: jsonData,
          headers: {
            'Content-Type': 'application/json',
          },
        }) as AxiosRequestConfig
      )
      return
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
    ...useMutation<void, ApiError, CompleteFileUploadArgs>(completeFileUpload, {
      onSuccess: () => queryClient.invalidateQueries(key),
    }),
    progress,
  }
}

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const useDeleteFile = (key: string[], url: string) => {
  const deleteFile = () => fetchApi(url, { method: 'DELETE' })
  const queryClient = useQueryClient()
  return useMutation<void, ApiError, void>(deleteFile, {
    onSuccess: () => queryClient.invalidateQueries(key),
  })
}

export const useJurisdictionsFile = (electionId: string): IFileUpload => {
  const url = `/api/election/${electionId}/jurisdiction/file`
  const key = ['elections', electionId, 'jurisdictions-file']
  const uploadFiles = useUploadFiles(key, url)
  const deleteFile = useDeleteFile(key, url)
  const queryClient = useQueryClient()
  return {
    uploadedFile: useUploadedFile(key, url, {
      onFileChange: () => {
        // When the jurisdictions file changes, the standardized contest file is reprocessed
        queryClient.invalidateQueries([
          'elections',
          electionId,
          'standardized-contests-file',
        ])
        // We need to reload the jurisdictions list
        queryClient.invalidateQueries(jurisdictionsQueryKey(electionId))
      },
    }),
    uploadFiles: async (files: File[]) => {
      await uploadFiles.mutateAsync({ file: files[0] })
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/csv`,
  }
}

export const useStandardizedContestsFile = (
  electionId: string,
  options: { enabled: boolean } = { enabled: true }
): IFileUpload => {
  const queryClient = useQueryClient()
  const url = `/api/election/${electionId}/standardized-contests/file`
  const key = ['elections', electionId, 'standardized-contests-file']
  const uploadFiles = useUploadFiles(key, url)
  const deleteFile = useDeleteFile(key, url)
  return {
    uploadedFile: useUploadedFile(key, url, {
      ...options,
      onFileChange: () => {
        queryClient.invalidateQueries(
          contestChoiceNameStandardizationsQueryKey(electionId)
        )
        queryClient.invalidateQueries(contestsQueryKey(electionId))
      },
    }),
    uploadFiles: async (files: File[]) => {
      await uploadFiles.mutateAsync({ file: files[0] })
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/csv`,
  }
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
      return uploadFiles.mutateAsync({ file: files[0] })
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
      return uploadFiles.mutateAsync({ file: files[0] })
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/csv`,
  }
}

export interface ICvrsFileUpload extends Omit<IFileUpload, 'uploadFiles'> {
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
      return uploadFiles.mutateAsync({ file: files[0], cvrFileType })
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/csv`,
  }
}
