import { api, checkAndToast } from '../../utilities'
import { IErrorResponse } from '../../../types'

export enum FileProcessingStatus {
  Blank = 'NULL', // only returned from getJurisdictionFileStatus, represents the null state from the server
  ReadyToProcess = 'READY_TO_PROCESS', // only received from the server, never returned from getJurisdictionFileStatus; equivalent to 'Processing'
  Processing = 'PROCESSING',
  Processed = 'PROCESSED',
  Errored = 'ERRORED',
}

export interface IJurisdictionsFileResponse {
  file: {
    contents: null | string
    name: string
    uploadedAt: string
  } | null
  processing: {
    status: FileProcessingStatus
    startedAt: string | null
    completedAt: string | null
    error: string | null
  } | null
}

const getJurisdictionFileStatus = async (
  electionId: string
): Promise<FileProcessingStatus> => {
  const jurisdictionsOrError:
    | IJurisdictionsFileResponse
    | IErrorResponse = await api(`/election/${electionId}/jurisdiction/file`)
  if (checkAndToast(jurisdictionsOrError)) {
    return FileProcessingStatus.Errored
  }
  if (jurisdictionsOrError.processing) {
    if (
      jurisdictionsOrError.processing!.status ===
      FileProcessingStatus.ReadyToProcess
    ) {
      return FileProcessingStatus.Processing
    }
    return jurisdictionsOrError.processing!.status
  }
  return FileProcessingStatus.Blank
}

export default getJurisdictionFileStatus
