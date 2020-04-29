import { toast } from 'react-toastify'
import { api, checkAndToast } from '../../utilities'
import { IRound, IErrorResponse } from '../../../types'

const getRound = async (electionId: string): Promise<IRound[]> => {
  try {
    const roundsOrError: { rounds: IRound[] } | IErrorResponse = await api(
      `/election/${electionId}/round`
    )
    // checkAndToast left here for consistency and reference but not tested since it's vestigial
    /* istanbul ignore next */
    if (checkAndToast(roundsOrError) || !roundsOrError.rounds.length) {
      return []
    }
    return roundsOrError.rounds
  } catch (err) /* istanbul ignore next */ {
    // TEST TODO
    toast.error(err.message)
    return []
  }
}

export default getRound
