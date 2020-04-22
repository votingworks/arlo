import { toast } from 'react-toastify'
import { api, checkAndToast } from '../../utilities'
import { IRound, IErrorResponse } from '../../../types'

const getRound = async (electionId: string): Promise<number> => {
  try {
    const roundsOrError: { rounds: IRound[] } | IErrorResponse = await api(
      `/election/${electionId}/round`
    )
    if (checkAndToast(roundsOrError) || !roundsOrError.rounds.length) {
      return 0
    }
    return roundsOrError.rounds.length
  } catch (err) {
    toast.error(err.message)
    return 0
  }
}

export default getRound
