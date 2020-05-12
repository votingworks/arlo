import { toast } from 'react-toastify'
import { api, checkAndToast } from '../../utilities'
import { IRound, IErrorResponse } from '../../../types'

const getRoundStatus = async (electionId: string): Promise<boolean> => {
  try {
    const roundsOrError: { rounds: IRound[] } | IErrorResponse = await api(
      `/election/${electionId}/round`
    )
    if (checkAndToast(roundsOrError) || !roundsOrError.rounds.length) {
      return false
    }
    return true
  } catch (err) {
    toast.error(err.message)
    return false
  }
}

export default getRoundStatus
