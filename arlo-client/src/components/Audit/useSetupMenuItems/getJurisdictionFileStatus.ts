import { api } from '../../utilities'

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
): Promise<{ status: FileProcessingStatus; error: string | null } | null> => {
  try {
    const fileStatus: IJurisdictionsFileResponse = await api(
      `/election/${electionId}/jurisdiction/file`
    )
    return fileStatus.processing
  } catch (err) {
    return { status: FileProcessingStatus.Errored, error: err.message }
  }
}

export default getJurisdictionFileStatus
