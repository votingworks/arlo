import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api, poll } from '../utilities'
import { IFileInfo } from './useJurisdictions'

export type IFilePurpose = 'ballot-manifest' | 'batch-tallies' | 'cvrs'

const filePurposeKeys: { [keys in IFilePurpose]: string } = {
  'ballot-manifest': 'manifest',
  'batch-tallies': 'batchTallies',
  cvrs: 'cvrs',
}

const loadCSV = async (
  electionId: string,
  jurisdictionId: string,
  filePurpose: IFilePurpose
): Promise<IFileInfo | null> => {
  const response = await api<IFileInfo>(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/${filePurpose}`
  )
  if (!response) return null
  return response
}

const putCSVFile = async (
  electionId: string,
  jurisdictionId: string,
  csv: File,
  filePurpose: IFilePurpose
): Promise<boolean> => {
  const formData: FormData = new FormData()
  formData.append(filePurposeKeys[filePurpose], csv, csv.name)
  const response = await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/${filePurpose}`,
    {
      method: 'PUT',
      body: formData,
    }
  )
  return !!response
}

const deleteCSVFile = async (
  electionId: string,
  jurisdictionId: string,
  filePurpose: IFilePurpose
): Promise<boolean> => {
  const response = await api(
    `/election/${electionId}/jurisdiction/${jurisdictionId}/${filePurpose}`,
    { method: 'DELETE' }
  )
  return !!response
}

const useCSV = (
  electionId: string,
  jurisdictionId: string,
  filePurpose: IFilePurpose
): [
  IFileInfo | null,
  (csv: File) => Promise<boolean>,
  () => Promise<boolean>
] => {
  const [csv, setCSV] = useState<IFileInfo | null>(null)

  useEffect(() => {
    ;(async () => {
      setCSV(await loadCSV(electionId, jurisdictionId, filePurpose))
    })()
  }, [electionId, jurisdictionId, filePurpose])

  const uploadCSV = async (csvFile: File): Promise<boolean> => {
    if (await putCSVFile(electionId, jurisdictionId, csvFile, filePurpose)) {
      setCSV(await loadCSV(electionId, jurisdictionId, filePurpose))
      return true
    }
    return false
  }

  const deleteCSV = async (): Promise<boolean> => {
    if (await deleteCSVFile(electionId, jurisdictionId, filePurpose)) {
      setCSV(await loadCSV(electionId, jurisdictionId, filePurpose))
      return true
    }
    return false
  }

  useEffect(() => {
    const isFinishedProcessing = (fileInfo: IFileInfo) =>
      !!(fileInfo.processing && fileInfo.processing.completedAt)

    if (!(csv && csv.file) || isFinishedProcessing(csv)) return

    const isComplete = async () => {
      const fileInfo = await loadCSV(electionId, jurisdictionId, filePurpose)
      return !!fileInfo && isFinishedProcessing(fileInfo)
    }
    const onComplete = async () => {
      setCSV(await loadCSV(electionId, jurisdictionId, filePurpose))
    }
    poll(isComplete, onComplete, err => toast.error(err.message))
  }, [electionId, jurisdictionId, csv, filePurpose])

  return [csv, uploadCSV, deleteCSV]
}

export const useBallotManifest = (
  electionId: string,
  jurisdictionId: string
): [
  IFileInfo | null,
  (csv: File) => Promise<boolean>,
  () => Promise<boolean>
] => useCSV(electionId, jurisdictionId, 'ballot-manifest')

export const useBatchTallies = (
  electionId: string,
  jurisdictionId: string
): [
  IFileInfo | null,
  (csv: File) => Promise<boolean>,
  () => Promise<boolean>
] => useCSV(electionId, jurisdictionId, 'batch-tallies')

export const useCVRS = (
  electionId: string,
  jurisdictionId: string
): [
  IFileInfo | null,
  (csv: File) => Promise<boolean>,
  () => Promise<boolean>
] => useCSV(electionId, jurisdictionId, 'cvrs')

export default useCSV
