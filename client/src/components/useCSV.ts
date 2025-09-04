import axios from 'axios'
import { toast } from 'react-toastify'
import { useEffect, useState } from 'react'
import { api, useInterval } from './utilities'
import { IAuditSettings } from './useAuditSettings'
import { addCSRFToken } from '../utils/api'

export enum FileProcessingStatus {
  READY_TO_PROCESS = 'READY_TO_PROCESS',
  PROCESSING = 'PROCESSING',
  PROCESSED = 'PROCESSED',
  ERRORED = 'ERRORED',
}

export enum CvrFileType {
  DOMINION = 'DOMINION',
  CLEARBALLOT = 'CLEARBALLOT',
  ESS = 'ESS',
  ESS_MD = 'ESS_MD',
  HART = 'HART',
}

export interface IFileInfo {
  file: {
    name: string
    uploadedAt: string
    cvrFileType?: CvrFileType
  } | null
  processing: {
    status: FileProcessingStatus
    startedAt: string | null
    completedAt: string | null
    error: string | null
    workProgress?: number
    workTotal?: number
  } | null
  upload?: IUpload | null
}

interface IUpload {
  file: File
  progress: number
}

type UploadUrlResponseData = {
  url: string
  fields: Record<string, string>
  errors: { message: string }[]
}

export const isFileProcessed = (file: IFileInfo): boolean =>
  !!file.processing && file.processing.status === FileProcessingStatus.PROCESSED

const loadCSVFile = async (url: string): Promise<IFileInfo | null> =>
  api<IFileInfo>(url)

const putCSVFile = async (
  url: string,
  file: File,
  formKey: string,
  trackProgress: (progress: number) => void,
  cvrFileType?: CvrFileType
): Promise<boolean> => {
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
    const getUploadResponse = (await axios<UploadUrlResponseData>(
      `/api${url}/upload-url`,
      addCSRFToken({
        method: 'GET',
        params,
      })
    )) as any

    // Upload the file to s3
    const uploadFileFormData = new FormData()
    Object.entries(getUploadResponse.data.fields).forEach(([key, value]) => {
      uploadFileFormData.append(key, value as string)
    })
    uploadFileFormData.append('Content-Type', file.type)
    uploadFileFormData.append('file', file, file.name)

    await axios(
      getUploadResponse.data.url,
      addCSRFToken({
        method: 'POST',
        data: uploadFileFormData,
        onUploadProgress: progress =>
          trackProgress(progress.loaded / progress.total),
      })
    )

    // Tell the server that the upload has finished to save the file path reference and kick off processing
    const jsonData = {
      fileName: file.name,
      fileType: file.type,
      ...(cvrFileType && { cvrFileType }),
      storagePathKey: getUploadResponse.data.fields.key,
    }

    await axios(
      `/api${url}/upload-complete`,
      addCSRFToken({
        method: 'POST',
        data: jsonData,
        headers: {
          'Content-Type': 'application/json',
        },
      })
    )
    return true
  } catch (e) {
    const error = e as any
    const errors = error.response?.data.errors
    const message =
      errors && errors.length ? errors[0].message : error.response?.statusText
    toast.error(message)
    return false
  }
}

const deleteCSVFile = async (url: string): Promise<boolean> => {
  const response = await api(url, { method: 'DELETE' })
  return !!response
}

const useCSV = (
  url: string,
  formKey: string,
  shouldFetch = true,
  dependencyFile?: IFileInfo | null
): [
  IFileInfo | null,
  (csv: File) => Promise<boolean>,
  () => Promise<boolean>
] => {
  const [csv, setCSV] = useState<IFileInfo | null>(null)
  const [upload, setUpload] = useState<IUpload | null>(null)

  // Load (or reload) this file whenever a file it depends on changes. This is
  // useful when one file gets reprocessed on the backend after its dependency
  // processes (e.g. CVR depends on ballot manifest).
  const hasDependency = dependencyFile !== undefined
  const dependencyNotUploaded = dependencyFile && dependencyFile.file === null
  const dependencyNotProcessing =
    dependencyFile &&
    dependencyFile.processing &&
    dependencyFile.processing.completedAt !== null
  useEffect(() => {
    ;(async () => {
      if (!shouldFetch) return
      if (!hasDependency || dependencyNotUploaded || dependencyNotProcessing) {
        setCSV(await loadCSVFile(url))
      }
    })()
  }, [
    url,
    shouldFetch,
    hasDependency,
    dependencyNotUploaded,
    dependencyNotProcessing,
  ])

  const uploadCSV = async (
    file: File,
    cvrFileType?: CvrFileType
  ): Promise<boolean> => {
    if (!shouldFetch) return false
    setUpload({ file, progress: 0 })
    if (
      await putCSVFile(
        url,
        file,
        formKey,
        progress => setUpload({ file, progress }),
        cvrFileType
      )
    ) {
      setCSV(await loadCSVFile(url))
      setUpload(null)
      return true
    }
    setUpload(null)
    return false
  }

  const deleteCSV = async (): Promise<boolean> => {
    if (!shouldFetch) return false
    if (await deleteCSVFile(url)) {
      setCSV(await loadCSVFile(url))
      return true
    }
    return false
  }

  const shouldPoll =
    shouldFetch && csv && csv.processing && !csv.processing.completedAt
  useInterval(
    async () => {
      setCSV(await loadCSVFile(url))
    },
    shouldPoll ? 1000 : null
  )

  return [csv && { ...csv, upload }, uploadCSV, deleteCSV]
}

export const useJurisdictionsFile = (
  electionId: string
): [IFileInfo | null, (csv: File) => Promise<boolean>] => {
  const [csv, uploadCSV] = useCSV(
    `/election/${electionId}/jurisdiction/file`,
    'jurisdictions'
  )
  // Delete not supported
  return [csv, uploadCSV]
}

export const useStandardizedContestsFile = (
  electionId: string,
  auditType: IAuditSettings['auditType'],
  jurisdictionsFile?: IFileInfo | null
): [IFileInfo | null, (csv: File) => Promise<boolean>] => {
  const [csv, uploadCSV] = useCSV(
    `/election/${electionId}/standardized-contests/file`,
    'standardized-contests',
    auditType === 'BALLOT_COMPARISON' || auditType === 'HYBRID',
    jurisdictionsFile
  )
  // Delete not supported
  return [csv, uploadCSV]
}

export const useBallotManifest = (
  electionId: string,
  jurisdictionId: string
): [
  IFileInfo | null,
  (csv: File) => Promise<boolean>,
  () => Promise<boolean>
] =>
  useCSV(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/ballot-manifest`,
    'manifest'
  )

export const useBatchTallies = (
  electionId: string,
  jurisdictionId: string,
  auditSettings: IAuditSettings | null,
  ballotManifest: IFileInfo | null
): [
  IFileInfo | null,
  (csv: File) => Promise<boolean>,
  () => Promise<boolean>
] =>
  useCSV(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/batch-tallies`,
    'batchTallies',
    !!auditSettings && auditSettings.auditType === 'BATCH_COMPARISON',
    ballotManifest
  )

export const useCVRs = (
  electionId: string,
  jurisdictionId: string,
  auditSettings: IAuditSettings | null,
  ballotManifest: IFileInfo | null
): [
  IFileInfo | null,
  (csv: File) => Promise<boolean>,
  () => Promise<boolean>
] =>
  useCSV(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/cvrs`,
    'cvrs',
    !!auditSettings &&
      (auditSettings.auditType === 'BALLOT_COMPARISON' ||
        auditSettings.auditType === 'HYBRID'),
    ballotManifest
  )

export default useCSV
