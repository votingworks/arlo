import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { api } from '../utilities'

enum FileProcessingStatus {
  READY_TO_PROCESS = 'READY_TO_PROCESS',
  PROCESSING = 'PROCESSING',
  PROCESSED = 'PROCESSED',
  ERRORED = 'ERRORED',
}

interface IFileInfo {
  file: {
    contents: null | string
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

export enum JurisdictionRoundStatus {
  NOT_STARTED = 'NOT_STARTED',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETE = 'COMPLETE',
}

export interface IJurisdiction {
  id: string
  name: string
  ballotManifest: IFileInfo
  currentRoundStatus: {
    status: JurisdictionRoundStatus
    numBallotsSampled: number
    numBallotsAudited: number
  } | null
}

const useJurisdictions = (electionId: string) => {
  const [jurisdictions, setJurisdictions] = useState<IJurisdiction[]>([])
  useEffect(() => {
    ;(async () => {
      try {
        const response: { jurisdictions: IJurisdiction[] } = await api(
          `/election/${electionId}/jurisdiction`
        )
        setJurisdictions(response.jurisdictions)
      } catch (err) {
        toast.error(err.message)
      }
    })()
  }, [electionId])
  return jurisdictions
}

export default useJurisdictions
