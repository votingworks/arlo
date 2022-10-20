import React from 'react'
import { toast } from 'react-toastify'
import * as Sentry from '@sentry/react'

import AsyncButton from '../Atoms/AsyncButton'
import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import { downloadBatchTallySheets } from './generateSheets'
import { useBatches } from './useBatchResults'
import { sleep } from '../../utils/sleep'

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
  const contestsQuery = useContestsJurisdictionAdmin(electionId, jurisdictionId)

  const onClick = async () => {
    // Wait for the batches/contests to load in case they haven't yet.
    while (!batchesQuery.isSuccess || !contestsQuery.isSuccess) {
      if (batchesQuery.isError || contestsQuery.isError) return
      // eslint-disable-next-line no-await-in-loop
      await sleep(100)
    }

    const { batches } = batchesQuery.data
    // Batch comparison audits only support a single contest
    const [contest] = contestsQuery.data

    try {
      await downloadBatchTallySheets(batches, contest.choices, jurisdictionName)
    } catch (err) {
      toast.error('Error preparing batch tally sheets for download')
      Sentry.captureException(err)
    }
  }

  return (
    <AsyncButton icon="download" intent="primary" onClick={onClick}>
      Download Batch Tally Sheets
    </AsyncButton>
  )
}

export default DownloadBatchTallySheetsButton
