import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { api, poll } from '../utilities'
import { FileProcessingStatus } from './useCSV'

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
  [contestId: string]: number
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

export const isDrawSampleComplete = (rounds: IRound[]) =>
  rounds[rounds.length - 1].drawSampleTask.completedAt !== null

const useRoundsAuditAdmin = (
  electionId: string,
  refreshId?: string
): [IRound[] | null, (sampleSizes?: ISampleSizes) => Promise<boolean>] => {
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

  return [rounds, startNextRound]
}

export default useRoundsAuditAdmin
