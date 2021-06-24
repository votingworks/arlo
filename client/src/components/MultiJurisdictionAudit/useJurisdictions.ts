import { useState, useEffect } from 'react'
import { api } from '../utilities'
import { IFileInfo, FileProcessingStatus } from './useCSV'

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
  FAILED = 'FAILED',
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

export const getJurisdictionStatus = (jurisdiction: IJurisdiction) => {
  const {
    currentRoundStatus,
    ballotManifest,
    batchTallies,
    cvrs,
  } = jurisdiction

  if (!currentRoundStatus) {
    const files: IFileInfo['processing'][] = [ballotManifest.processing]
    if (batchTallies) files.push(batchTallies.processing)
    if (cvrs) files.push(cvrs.processing)

    const numComplete = files.filter(
      f => f && f.status === FileProcessingStatus.PROCESSED
    ).length
    const anyFailed = files.some(
      f => f && f.status === FileProcessingStatus.ERRORED
    )

    // Special case when we just have a ballotManifest
    if (files.length === 1) {
      if (anyFailed) {
        return JurisdictionRoundStatus.FAILED
      }
      if (numComplete === 1) {
        return JurisdictionRoundStatus.COMPLETE
      }
    }

    // When we have multiple files
    if (anyFailed) {
      return JurisdictionRoundStatus.FAILED
    }
    if (numComplete === files.length) {
      return JurisdictionRoundStatus.COMPLETE
    }
    return JurisdictionRoundStatus.NOT_STARTED
  }
  if (currentRoundStatus.status === JurisdictionRoundStatus.COMPLETE) {
    return JurisdictionRoundStatus.COMPLETE
  }
  if (currentRoundStatus.status === JurisdictionRoundStatus.IN_PROGRESS) {
    return JurisdictionRoundStatus.IN_PROGRESS
  }

  return JurisdictionRoundStatus.NOT_STARTED
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
