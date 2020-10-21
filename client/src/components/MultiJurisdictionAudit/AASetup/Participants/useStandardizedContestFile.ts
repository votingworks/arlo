import { useEffect, useState } from 'react'
import { api } from '../../../utilities'
import { IFileInfo } from '../../useJurisdictions'

const loadStandardizedContestFile = async (
  electionId: string
): Promise<IFileInfo | null> => {
  const response = await api<IFileInfo>(
    `/election/${electionId}/standardized-contests/file`
  )
  if (!response) return null
  return response
}

const putStandardizedContestFile = async (
  electionId: string,
  csv: File
): Promise<boolean> => {
  const formData: FormData = new FormData()
  formData.append('standardized-contests', csv, csv.name)
  const response = await api(
    `/election/${electionId}/standardized-contests/file`,
    {
      method: 'PUT',
      body: formData,
    }
  )
  return !!response
}

const useStandardizedContestFile = (
  electionId: string
): [IFileInfo | null, (csv: File) => Promise<boolean>] => {
  const [
    jurisdictionFile,
    setStandardizedContestFile,
  ] = useState<IFileInfo | null>(null)

  const uploadStandardizedContestFile = async (csv: File): Promise<boolean> => {
    // TODO poll for result of upload
    if (await putStandardizedContestFile(electionId, csv)) {
      setStandardizedContestFile(await loadStandardizedContestFile(electionId))
      return true
    }
    return false
  }

  useEffect(() => {
    ;(async () => {
      setStandardizedContestFile(await loadStandardizedContestFile(electionId))
    })()
  }, [electionId])

  return [jurisdictionFile, uploadStandardizedContestFile]
}

export default useStandardizedContestFile
