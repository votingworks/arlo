import { useEffect, useState } from 'react'
import { api, useInterval } from '../utilities'
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
  formKey: string
): Promise<boolean> => {
  const formData: FormData = new FormData()
  formData.append(formKey, csv, csv.name)
  const response = await api(url, {
    method: 'PUT',
    body: formData,
  })
  return !!response
}

const deleteCSVFile = async (url: string): Promise<boolean> => {
  const response = await api(url, { method: 'DELETE' })
  return !!response
}

const useCSV = (
  url: string,
  formKey: string,
  shouldFetch: boolean = true
): [
  IFileInfo | null,
  (csv: File) => Promise<boolean>,
  () => Promise<boolean>
] => {
  const [csv, setCSV] = useState<IFileInfo | null>(null)

  useEffect(() => {
    ;(async () => {
      setCSV(await loadCSVFile(url, shouldFetch))
    })()
  }, [url, shouldFetch])

  const uploadCSV = async (csvFile: File): Promise<boolean> => {
    if (!shouldFetch) return false
    if (await putCSVFile(url, csvFile, formKey)) {
      setCSV(await loadCSVFile(url, shouldFetch))
      return true
    }
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

  return [csv, uploadCSV, deleteCSV]
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
  auditSettings: IAuditSettings | null
): [IFileInfo | null, (csv: File) => Promise<boolean>] => {
  const [csv, uploadCSV] = useCSV(
    `/election/${electionId}/standardized-contests/file`,
    'standardized-contests',
    !!auditSettings &&
      (auditSettings.auditType === 'BALLOT_COMPARISON' ||
        auditSettings.auditType === 'HYBRID')
  )
  // Delete not supported
  return [csv, uploadCSV]
}

export const useBallotManifest = (electionId: string, jurisdictionId: string) =>
  useCSV(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/ballot-manifest`,
    'manifest'
  )

export const useBatchTallies = (electionId: string, jurisdictionId: string) =>
  useCSV(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/batch-tallies`,
    'batchTallies'
  )

export const useCVRs = (electionId: string, jurisdictionId: string) =>
  useCSV(`/election/${electionId}/jurisdiction/${jurisdictionId}/cvrs`, 'cvrs')

export default useCSV
