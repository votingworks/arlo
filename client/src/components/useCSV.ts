import axios, { AxiosRequestConfig } from 'axios'
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
  files: File[]
  progress: number
}

export const isFileProcessed = (file: IFileInfo): boolean =>
  !!file.processing && file.processing.status === FileProcessingStatus.PROCESSED

const loadCSVFile = async (url: string): Promise<IFileInfo | null> =>
  api<IFileInfo>(url)

const putCSVFiles = async (
  url: string,
  files: File[],
  formKey: string,
  trackProgress: (progress: number) => void,
  cvrFileType?: CvrFileType
): Promise<boolean> => {
  const formData: FormData = new FormData()
  for (const f of files) formData.append(formKey, f, f.name)
  if (cvrFileType) formData.append('cvrFileType', cvrFileType)
  try {
    await axios(
      `/api${url}`,
      addCSRFToken({
        method: 'PUT',
        data: formData,
        onUploadProgress: progress =>
          trackProgress(progress.loaded / progress.total),
      }) as AxiosRequestConfig
    )
    return true
  } catch (error) {
    const { errors } = error.response.data
    const message =
      errors && errors.length ? errors[0].message : error.response.statusText
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
  (csv: File[]) => Promise<boolean>,
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

  const uploadCSVs = async (
    files: File[],
    cvrFileType?: CvrFileType
  ): Promise<boolean> => {
    if (!shouldFetch) return false
    setUpload({ files, progress: 0 })
    if (
      await putCSVFiles(
        url,
        files,
        formKey,
        progress => setUpload({ files, progress }),
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

  return [csv && { ...csv, upload }, uploadCSVs, deleteCSV]
}

export const useJurisdictionsFile = (
  electionId: string
): [IFileInfo | null, (csv: File[]) => Promise<boolean>] => {
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
): [IFileInfo | null, (csv: File[]) => Promise<boolean>] => {
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
  (csv: File[]) => Promise<boolean>,
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
  (csv: File[]) => Promise<boolean>,
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
  (csv: File[]) => Promise<boolean>,
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
