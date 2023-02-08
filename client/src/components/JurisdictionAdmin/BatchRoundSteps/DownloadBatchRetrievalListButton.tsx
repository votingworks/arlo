import React from 'react'
import { IButtonProps } from '@blueprintjs/core'
import AsyncButton from '../../Atoms/AsyncButton'
import { apiDownload } from '../../utilities'

interface IDownloadBatchRetrievalListButtonProps extends IButtonProps {
  electionId: string
  jurisdictionId: string
  roundId: string
}

const DownloadBatchRetrievalListButton: React.FC<IDownloadBatchRetrievalListButtonProps> = ({
  electionId,
  jurisdictionId,
  roundId,
  ...buttonProps
}) => (
  <AsyncButton
    {...buttonProps}
    icon="download"
    onClick={() =>
      apiDownload(
        `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/batches/retrieval-list`
      )
    }
  >
    Download Batch Retrieval List
  </AsyncButton>
)

export default DownloadBatchRetrievalListButton
