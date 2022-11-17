import axios, { AxiosRequestConfig } from 'axios'
import { toast } from 'react-toastify'
import { useEffect, useState } from 'react'
import uuidv4 from 'uuidv4'
import { api, useInterval } from './utilities'
import { IAuditSettings } from './useAuditSettings'
import { addCSRFToken, fetchApi } from '../utils/api'
import { sum } from '../utils/number'

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

const MEGABYTE = 1000 * 1000
const MIN_FILE_SIZE_TO_CHUNK = 100 * MEGABYTE
const CHUNK_SIZE = 5 * MEGABYTE

const uploadFileInChunks = async (chunksUrl: string, file: File) => {
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE)
  for (let chunkNumber = 0; chunkNumber < totalChunks; chunkNumber += 1) {
    const chunk = file.slice(
      chunkNumber * CHUNK_SIZE,
      (chunkNumber + 1) * CHUNK_SIZE
    )
    const formData = new FormData()
    formData.append('fileName', file.name)
    formData.append('chunkNumber', chunkNumber.toString())
    formData.append('chunkContents', chunk)
    // eslint-disable-next-line no-await-in-loop
    await fetchApi(chunksUrl, {
      method: 'PUT',
      body: formData,
    })
  }
}

const uploadFilesInChunks = async (
  url: string,
  files: File[],
  trackProgress: (progress: number) => void,
  cvrFileType: CvrFileType
) => {
  // TODO track progress
  const chunkedUploadId = uuidv4()
  const apiUrl = `/api${url}`
  const chunksUrl = `${apiUrl}/chunks/${chunkedUploadId}`
  for (const file of files) {
    // eslint-disable-next-line no-await-in-loop
    await uploadFileInChunks(chunksUrl, file)
  }
  const formData = new FormData()
  formData.append('chunkedUploadId', chunkedUploadId)
  formData.append('cvrFileType', cvrFileType)
  await fetchApi(apiUrl, {
    method: 'PUT',
    body: formData,
  })
}

const putCSVFiles = async (
  url: string,
  files: File[],
  formKey: string,
  trackProgress: (progress: number) => void,
  cvrFileType?: CvrFileType
): Promise<boolean> => {
  const totalFileSize = sum(files.map(f => f.size))
  if (
    (cvrFileType === CvrFileType.HART || cvrFileType === CvrFileType.ESS) &&
    totalFileSize >= MIN_FILE_SIZE_TO_CHUNK
  ) {
    await uploadFilesInChunks(url, files, trackProgress, cvrFileType)
    return true
  }

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
