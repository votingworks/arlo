import React, { useState } from 'react'
import { Button } from '@blueprintjs/core'
import { Document, pdf } from '@react-pdf/renderer'
import { toast } from 'react-toastify'
import * as FileSaver from 'file-saver'
import * as Sentry from '@sentry/react'

import BatchTallySheet from './BatchTallySheet'
import useContestsJurisdictionAdmin from '../useContestsJurisdictionAdmin'
import { useBatches } from '../useBatchResults'

const FILE_NAME = 'batch-tally-sheets.pdf'

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
  const [isDownloading, setIsDownloading] = useState(false)

  if (!batchesQuery.isSuccess || !contests) {
    return null
  }

  const { batches } = batchesQuery.data
  // Batch comparison audits only support a single contest
  const contest = contests[0]

  const batchTallySheets = (
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
  )

  const onClick = async () => {
    setIsDownloading(true)

    // Use a setImmediate to prevent PDF rendering from blocking React rendering
    setImmediate(async () => {
      let blob: Blob | null = null
      try {
        blob = await pdf(batchTallySheets).toBlob()
        FileSaver.saveAs(blob, FILE_NAME)
      } catch (err) {
        toast.error('Error preparing batch tally sheets for download')
        Sentry.captureException(err)
      }
      setIsDownloading(false)
    })
  }

  return (
    <Button icon="th" loading={isDownloading} onClick={onClick}>
      Download Batch Tally Sheets
    </Button>
  )
}

export default DownloadBatchTallySheetsButton
