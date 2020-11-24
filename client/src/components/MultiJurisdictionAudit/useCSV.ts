import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api, poll } from '../utilities'

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
  } | null
}

const loadCSVFile = async (url: string): Promise<IFileInfo | null> =>
  api<IFileInfo>(url)

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
  formKey: string
): [
  IFileInfo | null,
  (csv: File) => Promise<boolean>,
  () => Promise<boolean>
] => {
  const [csv, setCSV] = useState<IFileInfo | null>(null)

  // useEffect(() => {
  //   ;(async () => {
  //     setCSV(await loadCSVFile(url))
  //   })()
  // }, [url])

  const uploadCSV = async (csvFile: File): Promise<boolean> => {
    if (await putCSVFile(url, csvFile, formKey)) {
      setCSV(await loadCSVFile(url))
      return true
    }
    return false
  }

  const deleteCSV = async (): Promise<boolean> => {
    if (await deleteCSVFile(url)) {
      setCSV(await loadCSVFile(url))
      return true
    }
    return false
  }

  useEffect(() => {
    const isFinishedProcessing = (fileInfo: IFileInfo) =>
      !!(fileInfo.processing && fileInfo.processing.completedAt)

    if (!(csv && csv.file) || isFinishedProcessing(csv)) return

    const isComplete = async () => {
      const fileInfo = await loadCSVFile(url)
      return !!fileInfo && isFinishedProcessing(fileInfo)
    }
    const onComplete = async () => {
      setCSV(await loadCSVFile(url))
    }
    poll(isComplete, onComplete, err => toast.error(err.message))
  }, [url, csv])

  return [csv, uploadCSV, deleteCSV]
}

export const useJurisdictionsFile = (electionId: string) =>
  useCSV(`/election/${electionId}/jurisdiction/file`, 'jurisdictions')

export const useStandardizedContestsFile = (electionId: string) =>
  useCSV(
    `/election/${electionId}/standardized-contests/file`,
    'standardized-contests'
  )

export const useBallotManifest = (electionId: string, jurisdictionId: string) =>
  useCSV(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/ballot-manifest`,
    'ballotManifest'
  )

export const useBatchTallies = (electionId: string, jurisdictionId: string) =>
  useCSV(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/batch-tallies`,
    'batchTallies'
  )

export const useCVRs = (electionId: string, jurisdictionId: string) =>
  useCSV(`/election/${electionId}/jurisdiction/${jurisdictionId}/cvrs`, 'cvrs')

export default useCSV
