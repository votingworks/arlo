import React from 'react'
import { toast } from 'react-toastify'
import * as Sentry from '@sentry/react'
import { IButtonProps } from '@blueprintjs/core'
import AsyncButton from '../../Atoms/AsyncButton'
import useContestsJurisdictionAdmin from '../useContestsJurisdictionAdmin'
import { downloadStackLabels } from '../generateSheets'
import { sleep } from '../../../utils/sleep'

interface DownloadStackLabelsButtonProps extends IButtonProps {
  auditName: string
  electionId: string
  jurisdictionId: string
  jurisdictionName: string
}

const DownloadStackLabelsButton = ({
  auditName,
  electionId,
  jurisdictionId,
  jurisdictionName,
  ...buttonProps
}: DownloadStackLabelsButtonProps): JSX.Element | null => {
  const contestsQuery = useContestsJurisdictionAdmin(electionId, jurisdictionId)

  const onClick = async () => {
    while (!contestsQuery.isSuccess) {
      if (contestsQuery.isError) return
      // eslint-disable-next-line no-await-in-loop
      await sleep(100)
    }

    const contests = contestsQuery.data

    try {
      await downloadStackLabels(auditName, contests, jurisdictionName)
    } catch (err) {
      toast.error('Error preparing stack labels for download')
      Sentry.captureException(err)
    }
  }

  return (
    <AsyncButton icon="download" {...buttonProps} onClick={onClick}>
      Download Stack Labels
    </AsyncButton>
  )
}

export default DownloadStackLabelsButton
