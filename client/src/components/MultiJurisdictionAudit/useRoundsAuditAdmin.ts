import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { api, poll } from '../utilities'
import { FileProcessingStatus } from './useCSV'
import { ISampleSizeOption } from './AASetup/Review/useSampleSizes'

export interface IRound {
  id: string
  roundNum: number
  startedAt: string
  endedAt: string | null
  isAuditComplete: boolean
  sampledAllBallots: boolean
  drawSampleTask: {
    status: FileProcessingStatus
    startedAt: string | null
    completedAt: string | null
    error: string | null
  }
}

export interface ISampleSizes {
  [contestId: string]: ISampleSizeOption
}

const getRounds = async (electionId: string): Promise<IRound[] | null> => {
  const response = await api<{ rounds: IRound[] }>(
    `/election/${electionId}/round`
  )
  return response && response.rounds
}

const postRound = async (
  electionId: string,
  roundNum: number,
  sampleSizes?: ISampleSizes
) => {
  const response = await api(`/election/${electionId}/round`, {
    method: 'POST',
    body: JSON.stringify({
      roundNum,
      sampleSizes,
    }),
    headers: {
      'Content-Type': 'application/json',
    },
  })
  return response !== null
}

const deleteRound = async (electionId: string, roundId: string) => {
  const response = await api(`/election/${electionId}/round/${roundId}`, {
    method: 'DELETE',
  })
  return response !== null
}

export const isDrawSampleComplete = (rounds: IRound[]) =>
  rounds[rounds.length - 1].drawSampleTask.completedAt !== null

export const drawSampleError = (rounds: IRound[]) =>
  rounds.length > 0 && rounds[rounds.length - 1].drawSampleTask.error

export const isAuditStarted = (rounds: IRound[]) =>
  rounds.length > 0 && isDrawSampleComplete(rounds) && !drawSampleError(rounds)

const useRoundsAuditAdmin = (
  electionId: string,
  refreshId?: string
): [
  IRound[] | null,
  (sampleSizes?: ISampleSizes) => Promise<boolean>,
  () => Promise<boolean>
] => {
  const [rounds, setRounds] = useState<IRound[] | null>(null)

  const startNextRound = async (sampleSizes?: ISampleSizes) => {
    if (rounds === null)
      throw new Error('Cannot start next round until rounds are loaded')
    const nextRoundNum =
      rounds.length === 0 ? 1 : rounds[rounds.length - 1].roundNum + 1
    if (await postRound(electionId, nextRoundNum, sampleSizes)) {
      setRounds(await getRounds(electionId))
      return true
    }
    return false
  }

  const undoRoundStart = async () => {
    if (rounds === null || rounds.length === 0)
      throw new Error('Cannot undo round start')
    if (await deleteRound(electionId, rounds[rounds.length - 1].id)) {
      setRounds(await getRounds(electionId))
      return true
    }
    return false
  }

  useEffect(() => {
    ;(async () => {
      const isComplete = async () => {
        const rounds = await getRounds(electionId) // eslint-disable-line no-shadow
        setRounds(rounds)
        return (
          rounds === null || rounds.length === 0 || isDrawSampleComplete(rounds)
        )
      }
      poll(
        isComplete,
        () => null,
        err => toast.error(err.message),
        10 * 60 * 1000 // Time out sampling after 10 minutes
      )
    })()
  }, [electionId, refreshId])

  return [rounds, startNextRound, undoRoundStart]
}

export default useRoundsAuditAdmin
