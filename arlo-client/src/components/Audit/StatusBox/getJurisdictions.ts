import { toast } from 'react-toastify'
import { api, checkAndToast } from '../../utilities'
import { IErrorResponse } from '../../../types'

export enum FileProcessingStatus {
  Blank = 'NULL', // only returned from getJurisdictionFileStatus, represents the null state from the server
  ReadyToProcess = 'READY_TO_PROCESS', // only received from the server, never returned from getJurisdictionFileStatus; equivalent to 'Processing'
  Processing = 'PROCESSING',
  Processed = 'PROCESSED',
  Errored = 'ERRORED',
}

export interface IJurisdictionsResponse {
  jurisdictions: {
    id: string
    name: string
    ballotManifest: {
      file: string | null
      processing: FileProcessingStatus
      numBallots: number
      numBatches: number
    }
    currentRoundStatus: number
  }[]
}

const getJurisdictions = async (
  electionId: string
): Promise<undefined | IJurisdictionsResponse> => {
  try {
    const jurisdictionsOrError:
      | IJurisdictionsResponse
      | IErrorResponse = await api(`/election/${electionId}/jurisdiction`)
    if (checkAndToast(jurisdictionsOrError)) {
      return undefined
    }
    return jurisdictionsOrError
  } catch (err) {
    toast.error(err.message)
    return undefined
  }
}

export default getJurisdictions
