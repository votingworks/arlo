import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api, poll } from '../utilities'
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

const deleteBallotManifestFile = async (
  electionId: string,
  jurisdictionId: string
): Promise<boolean> => {
  try {
    return await api(
      `/election/${electionId}/jurisdiction/${jurisdictionId}/ballot-manifest`,
      { method: 'DELETE' }
    )
  } catch (err) {
    toast.error(err.message)
    return false
  }
}

const useBallotManifest = (
  electionId: string,
  jurisdictionId: string
): [
  IFileInfo | null,
  (csv: File) => Promise<boolean>,
  () => Promise<boolean>
] => {
  const [ballotManifest, setBallotManifest] = useState<IFileInfo | null>(null)

  useEffect(() => {
    ;(async () => {
      setBallotManifest(await loadBallotManifest(electionId, jurisdictionId))
    })()
  }, [electionId, jurisdictionId])

  const uploadBallotManifest = async (csv: File): Promise<boolean> => {
    if (await putBallotManifestFile(electionId, jurisdictionId, csv)) {
      setBallotManifest(await loadBallotManifest(electionId, jurisdictionId))
      return true
    }
    return false
  }

  const deleteBallotManifest = async (): Promise<boolean> => {
    if (await deleteBallotManifestFile(electionId, jurisdictionId)) {
      setBallotManifest(await loadBallotManifest(electionId, jurisdictionId))
      return true
    }
    return false
  }

  useEffect(() => {
    const isFinishedProcessing = (manifest: IFileInfo) =>
      !!(manifest.processing && manifest.processing.completedAt)

    if (
      !(ballotManifest && ballotManifest.file) ||
      isFinishedProcessing(ballotManifest)
    )
      return

    const isComplete = async () => {
      const manifest = await loadBallotManifest(electionId, jurisdictionId)
      return !!manifest && isFinishedProcessing(manifest)
    }
    const onComplete = async () => {
      setBallotManifest(await loadBallotManifest(electionId, jurisdictionId))
    }
    poll(isComplete, onComplete, err => toast.error(err.message))
  }, [electionId, jurisdictionId, ballotManifest])

  return [ballotManifest, uploadBallotManifest, deleteBallotManifest]
}

export default useBallotManifest
