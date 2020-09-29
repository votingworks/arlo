import React from 'react'
import { Classes, Dialog, Intent } from '@blueprintjs/core'
import FormButton from '../../../Atoms/Form/FormButton'

const ConfirmLaunch = ({
  isOpen,
  handleClose,
  onLaunch,
  numJurisdictions,
  completedBallotUploads,
}: {
  isOpen: boolean
  handleClose: () => void
  onLaunch: () => void
  numJurisdictions: number
  completedBallotUploads: number
}) => {
  return (
    <Dialog
      icon="info-sign"
      onClose={handleClose}
      title="Are you sure you want to launch the audit?"
      isOpen={isOpen}
    >
      <div className={Classes.DIALOG_BODY}>
        <p>This action cannot be undone</p>
        <p>
          {completedBallotUploads} of {numJurisdictions} jurisdictions have
          uploaded ballot manifests.
        </p>
      </div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <FormButton onClick={handleClose}>Close Without Launching</FormButton>
          <FormButton intent={Intent.PRIMARY} onClick={onLaunch}>
            Launch Audit
          </FormButton>
        </div>
      </div>
    </Dialog>
  )
}

export default ConfirmLaunch
