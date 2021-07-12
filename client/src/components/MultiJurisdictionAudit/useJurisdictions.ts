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
}

export enum JurisdictionProgressStatus {
  UPLOADS_NOT_STARTED = 'UPLOADS_NOT_STARTED',
  UPLOADS_COMPLETE = 'UPLOADS_COMPLETE',
  UPLOADS_FAILED = 'UPLOADS_FAILED',
  AUDIT_NOT_STARTED = 'AUDIT_NOT_STARTED',
  AUDIT_IN_PROGRESS = 'AUDIT_IN_PROGRESS',
  AUDIT_COMPLETE = 'AUDIT_COMPLETE',
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
        return JurisdictionProgressStatus.UPLOADS_FAILED
      }
      if (numComplete === 1) {
        return JurisdictionProgressStatus.UPLOADS_COMPLETE
      }
    }

    // When we have multiple files
    if (anyFailed) {
      return JurisdictionProgressStatus.UPLOADS_FAILED
    }
    if (numComplete === files.length) {
      return JurisdictionProgressStatus.UPLOADS_COMPLETE
    }
    return JurisdictionProgressStatus.UPLOADS_NOT_STARTED
  }
  if (currentRoundStatus.status === JurisdictionRoundStatus.COMPLETE) {
    return JurisdictionProgressStatus.AUDIT_COMPLETE
  }
  if (currentRoundStatus.status === JurisdictionRoundStatus.IN_PROGRESS) {
    return JurisdictionProgressStatus.AUDIT_IN_PROGRESS
  }

  return JurisdictionProgressStatus.AUDIT_NOT_STARTED
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
