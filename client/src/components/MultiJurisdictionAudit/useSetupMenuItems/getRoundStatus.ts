import { api } from '../../utilities'
import { IRound } from '../useRoundsAuditAdmin'

const getRoundStatus = async (electionId: string): Promise<boolean> => {
  const response = await api<{ rounds: IRound[] }>(
    `/election/${electionId}/round`
  )
  if (!response || !response.rounds.length) return false
  return true
}

export default getRoundStatus
