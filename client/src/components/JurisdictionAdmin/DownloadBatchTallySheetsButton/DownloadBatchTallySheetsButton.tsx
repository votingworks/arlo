import React, { useEffect } from 'react'
import { AnchorButton } from '@blueprintjs/core'
import { BlobProvider, Document } from '@react-pdf/renderer'
import { toast } from 'react-toastify'

import BatchTallySheet from './BatchTallySheet'
import useContestsJurisdictionAdmin from '../useContestsJurisdictionAdmin'
import { useBatches } from '../useBatchResults'

const FILE_NAME = 'batch-tally-sheets.pdf'

const AnchorButtonErrorState = (): JSX.Element => {
  useEffect(() => {
    toast.error('Error preparing batch tally sheets for download')
  }, [])

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
  const batchesResp = useBatches(electionId, jurisdictionId, roundId)
  const contests = useContestsJurisdictionAdmin(electionId, jurisdictionId)

  if (!batchesResp || !batchesResp.data || !contests || contests.length === 0) {
    return null
  }

  const { batches } = batchesResp.data
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
          return <AnchorButtonErrorState />
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
