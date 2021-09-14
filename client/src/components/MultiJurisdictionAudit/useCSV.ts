import axios, { AxiosRequestConfig } from 'axios'
import { toast } from 'react-toastify'
import { useEffect, useState } from 'react'
import { api, useInterval, addCSRFToken } from '../utilities'
import { IAuditSettings } from './useAuditSettings'

export enum FileProcessingStatus {
  READY_TO_PROCESS = 'READY_TO_PROCESS',
  PROCESSING = 'PROCESSING',
  PROCESSED = 'PROCESSED',
  ERRORED = 'ERRORED',
}

export interface IFileInfo {
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
  upload?: IUpload | null
}

interface IUpload {
  file: File
  progress: number
}

export const isFileProcessed = (file: IFileInfo): boolean =>
  !!file.processing && file.processing.status === FileProcessingStatus.PROCESSED

const loadCSVFile = async (
  url: string,
  shouldFetch: boolean
): Promise<IFileInfo | null> =>
  shouldFetch ? api<IFileInfo>(url) : { file: null, processing: null }

const putCSVFile = async (
  url: string,
  csv: File,
  formKey: string,
  trackProgress: (progress: number) => void
): Promise<boolean> => {
  const formData: FormData = new FormData()
  formData.append(formKey, csv, csv.name)
  try {
    await axios(`/api${url}`, addCSRFToken({
      method: 'PUT',
      data: formData,
      onUploadProgress: progress =>
        trackProgress(progress.loaded / progress.total),
    }) as AxiosRequestConfig)
    return true
  } catch (error) {
    toast.error(error.message)
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
  shouldFetch: boolean = true,
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
      if (!hasDependency || dependencyNotUploaded || dependencyNotProcessing) {
        setCSV(await loadCSVFile(url, shouldFetch))
      }
    })()
  }, [
    url,
    shouldFetch,
    hasDependency,
    dependencyNotUploaded,
    dependencyNotProcessing,
  ])

  const uploadCSV = async (file: File): Promise<boolean> => {
    if (!shouldFetch) return false
    setUpload({ file, progress: 0 })
    if (
      await putCSVFile(url, file, formKey, progress =>
        setUpload({ file, progress })
      )
    ) {
      setCSV(await loadCSVFile(url, shouldFetch))
      setUpload(null)
      return true
    }
    setUpload(null)
    return false
  }

  const deleteCSV = async (): Promise<boolean> => {
    if (!shouldFetch) return false
    if (await deleteCSVFile(url)) {
      setCSV(await loadCSVFile(url, shouldFetch))
      return true
    }
    return false
  }

  const shouldPoll =
    shouldFetch && csv && csv.processing && !csv.processing.completedAt
  useInterval(
    async () => {
      setCSV(await loadCSVFile(url, shouldFetch))
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
  auditSettings: IAuditSettings | null,
  jurisdictionsFile?: IFileInfo | null
): [IFileInfo | null, (csv: File) => Promise<boolean>] => {
  const [csv, uploadCSV] = useCSV(
    `/election/${electionId}/standardized-contests/file`,
    'standardized-contests',
    !!auditSettings &&
      (auditSettings.auditType === 'BALLOT_COMPARISON' ||
        auditSettings.auditType === 'HYBRID'),
    jurisdictionsFile
  )
  // Delete not supported
  return [csv, uploadCSV]
}

export const useBallotManifest = (electionId: string, jurisdictionId: string) =>
  useCSV(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/ballot-manifest`,
    'manifest'
  )

export const useBatchTallies = (
  electionId: string,
  jurisdictionId: string,
  auditSettings: IAuditSettings | null,
  ballotManifest: IFileInfo | null
) =>
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
) =>
  useCSV(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/cvrs`,
    'cvrs',
    !!auditSettings &&
      (auditSettings.auditType === 'BALLOT_COMPARISON' ||
        auditSettings.auditType === 'HYBRID'),
    ballotManifest
  )
export default useCSV
