import { useState, useEffect } from 'react'
import { api } from '../utilities'
import { IFileInfo } from './useCSV'

export interface IBallotManifestInfo extends IFileInfo {
  numBallots: number | null
  numBatches: number | null
  // Only in Hybrid audits
  numBallotsCvr?: number | null
  numBallotsNonCvr?: number | null
}

export interface ICvrFileInfo extends IFileInfo {
  numBallots: number | null
}

export interface IBatchTalliesFileInfo extends IFileInfo {
  numBallots: number | null
}

export enum JurisdictionRoundStatus {
  NOT_STARTED = 'NOT_STARTED',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETE = 'COMPLETE',
}

export interface IJurisdiction {
  id: string
  name: string
  ballotManifest: IBallotManifestInfo
  batchTallies?: IBatchTalliesFileInfo
  cvrs?: ICvrFileInfo
  currentRoundStatus: {
    status: JurisdictionRoundStatus
    numSamples: number
    numSamplesAudited: number
    numUnique: number
    numUniqueAudited: number
    numBatchesAudited?: number
  } | null
}

const useJurisdictions = (
  electionId: string,
  refreshId?: string
): IJurisdiction[] | null => {
  const [jurisdictions, setJurisdictions] = useState<IJurisdiction[] | null>(
    null
  )
  useEffect(() => {
    ;(async () => {
      const response = await api<{ jurisdictions: IJurisdiction[] }>(
        `/election/${electionId}/jurisdiction`
      )
      if (!response) return
      setJurisdictions(response.jurisdictions)
    })()
  }, [electionId, refreshId])
  return jurisdictions
}

export default useJurisdictions
