import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api } from '../utilities'
import { IFileInfo } from './useJurisdictions'

const loadBallotManifest = async (
  electionId: string,
  jurisdictionId: string
): Promise<IFileInfo | null> => {
  try {
    return await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/ballot-manifest`
    )
  } catch (err) {
    toast.error(err.message)
    return null
  }
}

const putBallotManifestFile = async (
  electionId: string,
  jurisdictionId: string,
  csv: File
): Promise<boolean> => {
  const formData: FormData = new FormData()
  formData.append('manifest', csv, csv.name)
  try {
    await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/ballot-manifest`,
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

const useBallotManifest = (
  electionId: string,
  jurisdictionId: string
): [IFileInfo | null, (csv: File) => Promise<boolean>] => {
  const [ballotManifest, setBallotManifest] = useState<IFileInfo | null>(null)

  const uploadBallotManifest = async (csv: File): Promise<boolean> => {
    // TODO poll for result of upload
    if (await putBallotManifestFile(electionId, jurisdictionId, csv)) {
      setBallotManifest(await loadBallotManifest(electionId, jurisdictionId))
      return true
    }
    return false
  }

  useEffect(() => {
    ;(async () => {
      setBallotManifest(await loadBallotManifest(electionId, jurisdictionId))
    })()
  }, [electionId, jurisdictionId])

  return [ballotManifest, uploadBallotManifest]
}

export default useBallotManifest
