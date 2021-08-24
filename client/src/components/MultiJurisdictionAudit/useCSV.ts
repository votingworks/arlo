import axios, { AxiosRequestConfig } from 'axios'
import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api, useInterval, addCSRFToken } from '../utilities'
import { IAuditSettings } from './useAuditSettings'

export enum FileProcessingStatus {
  READY_TO_PROCESS = 'READY_TO_PROCESS',
  PROCESSING = 'PROCESSING',
  PROCESSED = 'PROCESSED',
  ERRORED = 'ERRORED',
}

interface IServerFile {
  file: {
    name: string
    uploadedAt: string
  } | null
  processing: {
    status: FileProcessingStatus
    startedAt: string | null
    completedAt: string | null
    error: string | null
    workProgress?: number
    workTotal?: number
  } | null
}
export type IFileInfo = IServerFile

export type IFileUpload =
  | {
      status: 'NO_FILE'
    }
  | {
      status: 'SELECTED'
      clientFile: File
    }
  | {
      status: 'UPLOADING'
      clientFile: File
      uploadProgress: number
    }
  | {
      status: 'READY_TO_PROCESS' | 'PROCESSING' | 'PROCESSED' | 'ERRORED'
      serverFile: IServerFile
    }

export interface IFileUploadActions {
  selectFile: (file: File | null) => void
  uploadFile: (file: File) => Promise<boolean>
  deleteFile: () => Promise<boolean>
}

const loadFile = async (
  url: string,
  shouldFetch: boolean
): Promise<IServerFile | null> =>
  shouldFetch ? api<IServerFile>(url) : { file: null, processing: null }

const putFile = async (
  url: string,
  file: File,
  formKey: string,
  setUploadProgress: (progress: number) => void
): Promise<boolean> => {
  const formData: FormData = new FormData()
  formData.append(formKey, file, file.name)
  try {
    await axios(addCSRFToken({
      method: 'PUT',
      url: `/api/${url}`,
      data: formData,
      onUploadProgress: progress =>
        setUploadProgress(progress.loaded / progress.total),
    }) as AxiosRequestConfig)
    return true
  } catch (error) {
    toast.error(error.message)
    return false
  }
}

const deleteServerFile = async (url: string): Promise<boolean> => {
  const response = await api(url, { method: 'DELETE' })
  return !!response
}

const useFileUpload = (
  url: string,
  formKey: string,
  shouldFetch: boolean = true
): [IFileUpload | null, IFileUploadActions] => {
  const [state, setState] = useState<IFileUpload | null>(null)

  const serverFileToState = (
    serverFile: IServerFile | null
  ): IFileUpload | null =>
    serverFile && serverFile.processing
      ? { status: serverFile.processing.status, serverFile }
      : { status: 'NO_FILE' }

  useEffect(() => {
    ;(async () => {
      const serverFile = await loadFile(url, shouldFetch)
      setState(serverFileToState(serverFile))
    })()
  }, [url, shouldFetch])

  const selectFile = (clientFile: File | null) =>
    clientFile
      ? setState({ status: 'SELECTED', clientFile })
      : setState({ status: 'NO_FILE' })

  const uploadFile = async (clientFile: File) => {
    if (!shouldFetch) return false
    setState({
      status: 'UPLOADING',
      clientFile,
      uploadProgress: 0,
    })
    if (
      await putFile(url, clientFile, formKey, uploadProgress =>
        setState({ status: 'UPLOADING', clientFile, uploadProgress })
      )
    ) {
      const serverFile = await loadFile(url, shouldFetch)
      setState(serverFileToState(serverFile))
      return true
    }
    setState(state)
    return false
  }

  const deleteFile = async () => {
    if (!shouldFetch) return false
    if (await deleteServerFile(url)) {
      setState({ status: 'NO_FILE' })
      return true
    }
    return false
  }

  const shouldPoll =
    shouldFetch &&
    state &&
    (state.status === 'READY_TO_PROCESS' || state.status === 'PROCESSING')
  useInterval(
    async () => {
      const serverFile = await loadFile(url, shouldFetch)
      setState(serverFileToState(serverFile))
    },
    shouldPoll ? 1000 : null
  )

  return [state, { selectFile, uploadFile, deleteFile }]
}

// export const isFileProcessed = (file: IFileInfo): boolean =>
//   !!file.processing && file.processing.status === FileProcessingStatus.PROCESSED

// const loadCSVFile = async (
//   url: string,
//   shouldFetch: boolean
// ): Promise<IFileInfo | null> =>
//   shouldFetch ? api<IFileInfo>(url) : { file: null, processing: null }

// const putCSVFile = async (
//   url: string,
//   csv: File,
//   formKey: string,
//   setUploadProgress: (progress: number) => void
// ): Promise<boolean> => {
//   const formData: FormData = new FormData()
//   formData.append(formKey, csv, csv.name)
//   try {
//     await axios(addCSRFToken({
//       method: 'PUT',
//       url: `/api/${url}`,
//       data: formData,
//       onUploadProgress: progress =>
//         setUploadProgress(progress.loaded / progress.total),
//     }) as AxiosRequestConfig)
//     return true
//   } catch (error) {
//     toast.error(error.message)
//     return false
//   }
// }

// const deleteCSVFile = async (url: string): Promise<boolean> => {
//   const response = await api(url, { method: 'DELETE' })
//   return !!response
// }

// const useCSV = (
//   url: string,
//   formKey: string,
//   shouldFetch: boolean = true
// ): [
//   IClientFileInfo | null,
//   (csv: File) => Promise<boolean>,
//   () => Promise<boolean>
// ] => {
//   const [csv, setCSV] = useState<IFileInfo | null>(null)
//   const [uploadProgress, setUploadProgress] = useState<number | null>(null)

//   useEffect(() => {
//     ;(async () => {
//       setCSV(await loadCSVFile(url, shouldFetch))
//     })()
//   }, [url, shouldFetch])

//   const uploadCSV = async (csvFile: File): Promise<boolean> => {
//     if (!shouldFetch) return false
//     setCSV({ file: null, processing: null })
//     setUploadProgress(0)
//     if (await putCSVFile(url, csvFile, formKey, setUploadProgress)) {
//       setCSV(await loadCSVFile(url, shouldFetch))
//       setUploadProgress(null)
//       return true
//     }
//     setCSV(csv)
//     setUploadProgress(null)
//     return false
//   }

//   const deleteCSV = async (): Promise<boolean> => {
//     if (!shouldFetch) return false
//     if (await deleteCSVFile(url)) {
//       setCSV(await loadCSVFile(url, shouldFetch))
//       setUploadProgress(null)
//       return true
//     }
//     return false
//   }

//   const shouldPoll =
//     shouldFetch && csv && csv.processing && !csv.processing.completedAt
//   useInterval(
//     async () => {
//       setCSV(await loadCSVFile(url, shouldFetch))
//     },
//     shouldPoll ? 1000 : null
//   )

//   return [
//     csv && ({ ...csv, uploadProgress } as IClientFileInfo),
//     uploadCSV,
//     deleteCSV,
//   ]
// }

export const useJurisdictionsFile = (
  electionId: string
): [IFileUpload | null, Omit<IFileUploadActions, 'deleteFile'>] => {
  const [state, actions] = useFileUpload(
    `/election/${electionId}/jurisdiction/file`,
    'jurisdictions'
  )
  // Delete not supported
  const { selectFile, uploadFile } = actions
  return [state, { selectFile, uploadFile }]
}

export const useStandardizedContestsFile = (
  electionId: string,
  auditSettings: IAuditSettings | null
): [IFileUpload | null, Omit<IFileUploadActions, 'deleteFile'>] => {
  const [state, actions] = useFileUpload(
    `/election/${electionId}/standardized-contests/file`,
    'standardized-contests',
    !!auditSettings &&
      (auditSettings.auditType === 'BALLOT_COMPARISON' ||
        auditSettings.auditType === 'HYBRID')
  )
  // Delete not supported
  const { selectFile, uploadFile } = actions
  return [state, { selectFile, uploadFile }]
}

export const useBallotManifest = (electionId: string, jurisdictionId: string) =>
  useFileUpload(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/ballot-manifest`,
    'manifest'
  )

export const useBatchTallies = (electionId: string, jurisdictionId: string) =>
  useFileUpload(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/batch-tallies`,
    'batchTallies'
  )

export const useCVRs = (electionId: string, jurisdictionId: string) =>
  useFileUpload(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/cvrs`,
    'cvrs'
  )

export default useFileUpload
