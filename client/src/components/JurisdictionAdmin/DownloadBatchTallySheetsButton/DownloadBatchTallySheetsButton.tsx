import React, { useEffect } from 'react'
import { AnchorButton } from '@blueprintjs/core'
import { BlobProvider, Document } from '@react-pdf/renderer'
import { toast } from 'react-toastify'
import * as Sentry from '@sentry/react'

import BatchTallySheet from './BatchTallySheet'
import useContestsJurisdictionAdmin from '../useContestsJurisdictionAdmin'
import { useBatches } from '../useBatchResults'

const FILE_NAME = 'batch-tally-sheets.pdf'

interface AnchorButtonErrorStateProps {
  error: Error
}

const AnchorButtonErrorState = ({
  error,
}: AnchorButtonErrorStateProps): JSX.Element => {
  // Render an error toast only once, when the component mounts
  useEffect(() => {
    toast.error('Error preparing batch tally sheets for download')
  }, [])

  useEffect(() => {
    Sentry.captureException(error)
  }, [error])

  return (
    <AnchorButton disabled icon="th">
      Download Batch Tally Sheets
    </AnchorButton>
  )
}

interface IProps {
  electionId: string
  jurisdictionId: string
  jurisdictionName: string
  roundId: string
}

const DownloadBatchTallySheetsButton = ({
  electionId,
  jurisdictionId,
  jurisdictionName,
  roundId,
}: IProps): JSX.Element | null => {
  const batchesQuery = useBatches(electionId, jurisdictionId, roundId)
  const contests = useContestsJurisdictionAdmin(electionId, jurisdictionId)

  if (!batchesQuery.isSuccess || !contests) {
    return null
  }

  const { batches } = batchesQuery.data
  // Batch comparison audits only support a single contest
  const contest = contests[0]

  return (
    <BlobProvider
      document={
        <Document title={FILE_NAME}>
          {batches.map(b => (
            <BatchTallySheet
              auditBoardName={b.auditBoard ? b.auditBoard.name : ''}
              batchName={b.name}
              choices={contest.choices}
              jurisdictionName={jurisdictionName}
              key={b.id}
            />
          ))}
        </Document>
      }
    >
      {({ error, loading, url }) => {
        if (error) {
          return <AnchorButtonErrorState error={error} />
        }
        return (
          <AnchorButton
            href={url || undefined}
            download={FILE_NAME}
            icon="th"
            loading={loading}
          >
            Download Batch Tally Sheets
          </AnchorButton>
        )
      }}
    </BlobProvider>
  )
}

export default DownloadBatchTallySheetsButton
