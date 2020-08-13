import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api, poll } from '../utilities'
import { IFileInfo } from './useJurisdictions'

const loadCSV = async (
  electionId: string,
  jurisdictionId: string,
  filePurpose: 'ballot-manifest' | 'batch-tallies'
): Promise<IFileInfo | null> => {
  try {
    return await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/${filePurpose}`
    )
  } catch (err) {
    toast.error(err.message)
    return null
  }
}

const putCSVFile = async (
  electionId: string,
  jurisdictionId: string,
  csv: File,
  filePurpose: 'ballot-manifest' | 'batch-tallies'
): Promise<boolean> => {
  const formData: FormData = new FormData()
  formData.append('manifest', csv, csv.name)
  try {
    await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/${filePurpose}`,
      {
        method: 'PUT',
        body: formData,
      }
    )
    return true
  } catch (err) {
    toast.error(err.message)
    return false
  }
}

const deleteCSVFile = async (
  electionId: string,
  jurisdictionId: string,
  filePurpose: 'ballot-manifest' | 'batch-tallies'
): Promise<boolean> => {
  try {
    return await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/${filePurpose}`,
      { method: 'DELETE' }
    )
  } catch (err) {
    toast.error(err.message)
    return false
  }
}

const useCSV = (
  electionId: string,
  jurisdictionId: string,
  filePurpose: 'ballot-manifest' | 'batch-tallies'
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
  }, [electionId, jurisdictionId])

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
  }, [electionId, jurisdictionId, csv])

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

export default useCSV
