import { useState, useEffect } from 'react'
import {
  useMutation,
  UseMutationResult,
  useQuery,
  useQueryClient,
  UseQueryResult,
} from 'react-query'
import { api } from './utilities'
import { IFileInfo, FileProcessingStatus } from './useCSV'
import { fetchApi, ApiError } from '../utils/api'
import { IActivity } from './AuditAdmin/ActivityLog'

export interface IBallotManifestInfo extends IFileInfo {
  numBallots: number | null
  numBatches: number | null
  // Only in batch comparison audits: [contestId]: the manifest's ballots for
  // that contest, using its per-contest counts
  numBallotsByContestId?: Record<string, number>
  // Only in Hybrid audits
  numBallotsCvr?: number | null
  numBallotsNonCvr?: number | null
}

export interface ICvrFileInfo extends IFileInfo {
  numBallots: number | null
}

export interface IBatchTalliesFileInfo extends IFileInfo {
  numBallots: number | null
  numBallotsByContestId?: Record<string, number> | null
}

export enum JurisdictionRoundStatus {
  NOT_STARTED = 'NOT_STARTED',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETE = 'COMPLETE',
}

export enum JurisdictionProgressStatus {
  UPLOADS_NOT_STARTED_NO_LOGIN = 'UPLOADS_NOT_STARTED_NO_LOGIN',
  UPLOADS_NOT_STARTED_LOGGED_IN = 'UPLOADS_NOT_STARTED_LOGGED_IN',
  UPLOADS_IN_PROGRESS = 'UPLOADS_IN_PROGRESS',
  UPLOADS_COMPLETE = 'UPLOADS_COMPLETE',
  UPLOADS_FAILED = 'UPLOADS_FAILED',
  AUDIT_NOT_STARTED_NO_LOGIN = 'AUDIT_NOT_STARTED_NO_LOGIN',
  AUDIT_NOT_STARTED_LOGGED_IN = 'AUDIT_NOT_STARTED_LOGGED_IN',
  AUDIT_IN_PROGRESS = 'AUDIT_IN_PROGRESS',
  AUDIT_COMPLETE = 'AUDIT_COMPLETE',
}

export interface IJurisdiction {
  id: string
  name: string
  adminEmails: string[]
  ballotManifest: IBallotManifestInfo
  expectedBallotManifestNumBallots: number | null
  batchTallies?: IBatchTalliesFileInfo
  cvrs?: ICvrFileInfo
  currentRoundStatus: {
    status: JurisdictionRoundStatus
    numSamples: number
    numSamplesAudited: number
    numUnique: number
    numUniqueAudited: number
    numBatchesAudited?: number
    extras?: IRoundStatusCounts // Only in batch comparison audits
    lastTalliedAt?: string | null // Only in batch comparison audits
  } | null
  currentRoundStatusByContestId?: Record<string, IBatchRoundStatusCounts> | null
}

export interface IRoundStatusCounts {
  numSamples: number
  numSamplesAudited: number
  numUnique: number
  numUniqueAudited: number
}

// Batch comparison audits also report the extra batches' share of the counts:
// batches sampled on top of what the audit math drew
export interface IBatchRoundStatusCounts extends IRoundStatusCounts {
  extras: IRoundStatusCounts
}

export const getJurisdictionStatus = (
  jurisdiction: IJurisdiction,
  lastLogin?: IActivity
): JurisdictionProgressStatus => {
  const { currentRoundStatus, ballotManifest, batchTallies, cvrs } =
    jurisdiction

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
    if (numComplete > 0) {
      return JurisdictionProgressStatus.UPLOADS_IN_PROGRESS
    }

    if (lastLogin) {
      return JurisdictionProgressStatus.UPLOADS_NOT_STARTED_LOGGED_IN
    }

    return JurisdictionProgressStatus.UPLOADS_NOT_STARTED_NO_LOGIN
  }

  if (currentRoundStatus.status === JurisdictionRoundStatus.COMPLETE) {
    return JurisdictionProgressStatus.AUDIT_COMPLETE
  }
  if (currentRoundStatus.status === JurisdictionRoundStatus.IN_PROGRESS) {
    return JurisdictionProgressStatus.AUDIT_IN_PROGRESS
  }

  if (lastLogin) {
    return JurisdictionProgressStatus.AUDIT_NOT_STARTED_LOGGED_IN
  }

  return JurisdictionProgressStatus.AUDIT_NOT_STARTED_NO_LOGIN
}

export const useJurisdictionsDeprecated = (
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

export const jurisdictionsQueryKey = (electionId: string): string[] => [
  'elections',
  electionId,
  'jurisdictions',
]

export const useJurisdictions = (
  electionId: string
): UseQueryResult<IJurisdiction[], ApiError> => {
  return useQuery(jurisdictionsQueryKey(electionId), async () => {
    const response: { jurisdictions: IJurisdiction[] } = await fetchApi(
      `/api/election/${electionId}/jurisdiction`
    )
    return response.jurisdictions
  })
}

const jurisdictionsWithLastLoginQueryKey = (electionId: string): string[] =>
  jurisdictionsQueryKey(electionId).concat('lastLoginByJurisdiction')

// { jurisidictionId: ActivityLogRecord }
export type LastLoginByJurisdiction = Record<string, IActivity>

export const useLastLoginByJurisdiction = (
  electionId: string
): UseQueryResult<LastLoginByJurisdiction, ApiError> => {
  return useQuery(jurisdictionsWithLastLoginQueryKey(electionId), async () => {
    const response: {
      lastLoginByJurisdiction: LastLoginByJurisdiction
    } = await fetchApi(`/api/election/${electionId}/jurisdictions/last-login`)
    return response.lastLoginByJurisdiction
  })
}

export type IBallotContestDiscrepancies = {
  reportedVotes: Record<string, number | string> // `Record` keys are choiceId
  auditedVotes: Record<string, number | string> // `Record` values are counts, "o" (overvote), "u" (undervote)
  discrepancies: Record<string, number | string>
}

// Ballot comparison audits: [jurisdictionId][ballotName][contestId]
export type BallotDiscrepanciesByJurisdiction = Record<
  string,
  Record<string, Record<string, IBallotContestDiscrepancies>>
>

export interface IBatchContestDiscrepancies {
  reportedVotes: Record<string, number> // [choiceId]
  auditedVotes: Record<string, number> // [choiceId]
  changeInMargin: number // In votes
  numBallots: number
}

export interface IBatchDiscrepancies {
  name: string
  isExtra: boolean // Sampled only as an extra batch, not by the audit math
  discrepancies: Record<string, IBatchContestDiscrepancies> // [contestId]
}

export interface IDiscrepancyNote {
  createdAt: string
  text: string
}

export interface IJurisdictionDiscrepancies {
  notes: IDiscrepancyNote[]
  batches: Record<string, IBatchDiscrepancies> // [batchId]
}

// [contestId]: contestDiscrepancies, for one batch or ballot
export type DiscrepanciesByContest = Record<
  string,
  IBatchContestDiscrepancies | IBallotContestDiscrepancies
>

// Batch comparison audits: [jurisdictionId]
export type BatchDiscrepanciesByJurisdiction = Record<
  string,
  IJurisdictionDiscrepancies
>

const discrepanciesByJurisdictionQueryKey = (electionId: string): string[] =>
  jurisdictionsQueryKey(electionId).concat('discrepanciesByJurisdiction')

export const useDiscrepanciesByJurisdiction = (
  electionId: string,
  options: { enabled?: boolean }
): UseQueryResult<
  BallotDiscrepanciesByJurisdiction | BatchDiscrepanciesByJurisdiction,
  ApiError
> => {
  return useQuery(
    discrepanciesByJurisdictionQueryKey(electionId),
    () => fetchApi(`/api/election/${electionId}/discrepancy`),
    options
  )
}

export const useUnfinalizeBatchTallies = (
  electionId: string
): UseMutationResult<
  unknown,
  ApiError,
  { jurisdictionId: string; roundId: string }
> => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ jurisdictionId, roundId }) =>
      fetchApi(
        `/api/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches/finalize`,
        { method: 'DELETE' }
      ),
    {
      onSuccess: () =>
        queryClient.invalidateQueries(jurisdictionsQueryKey(electionId)),
    }
  )
}

export const useAddJurisdictionDiscrepancyNote = (
  electionId: string
): UseMutationResult<
  unknown,
  ApiError,
  { jurisdictionId: string; text: string }
> => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ jurisdictionId, text }) =>
      fetchApi(
        `/api/election/${electionId}/jurisdiction/${jurisdictionId}/discrepancy-notes`,
        {
          method: 'POST',
          body: JSON.stringify({ text }),
          headers: { 'Content-Type': 'application/json' },
        }
      ),
    {
      onSuccess: () =>
        queryClient.invalidateQueries(
          discrepanciesByJurisdictionQueryKey(electionId)
        ),
    }
  )
}
