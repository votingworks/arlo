import { useEffect, useState } from 'react'
import { api } from '../../../utilities'
import { IFileInfo } from '../../useJurisdictions'

const loadContestFile = async (
  electionId: string
): Promise<IFileInfo | null> => {
  const response = await api<IFileInfo>(
    `/election/${electionId}/standardized-contests/file`
  )
  if (!response) return null
  return response
}

const putContestFileFile = async (
  electionId: string,
  csv: File
): Promise<boolean> => {
  const formData: FormData = new FormData()
  formData.append('standardize-contests', csv, csv.name)
  const response = await api(
    `/election/${electionId}/standardized-contests/file`,
    {
      method: 'PUT',
      body: formData,
    }
  )
  return !!response
}

const useContestFile = (
  electionId: string
): [IFileInfo | null, (csv: File) => Promise<boolean>] => {
  const [jurisdictionFile, setContestFile] = useState<IFileInfo | null>(null)

  const uploadContestFile = async (csv: File): Promise<boolean> => {
    // TODO poll for result of upload
    if (await putContestFileFile(electionId, csv)) {
      setContestFile(await loadContestFile(electionId))
      return true
    }
    return false
  }

  useEffect(() => {
    ;(async () => {
      setContestFile(await loadContestFile(electionId))
    })()
  }, [electionId])

  return [jurisdictionFile, uploadContestFile]
}

export default useContestFile
