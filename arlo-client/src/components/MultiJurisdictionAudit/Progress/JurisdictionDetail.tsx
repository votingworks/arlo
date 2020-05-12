import React from 'react'
import { Classes, Dialog } from '@blueprintjs/core'
import FormButton from '../../Atoms/Form/FormButton'
import { IJurisdiction, prettifyStatus } from '../useJurisdictions'

export interface IDialogExampleState {
  autoFocus: boolean
  canEscapeKeyClose: boolean
  canOutsideClickClose: boolean
  enforceFocus: boolean
  isOpen: boolean
  usePortal: boolean
}

const JurisdictionDetail = ({
  handleClose,
  jurisdiction,
  electionId,
}: {
  handleClose: () => void
  jurisdiction: IJurisdiction | null
  electionId: string
}) => {
  if (!jurisdiction) return null
  return (
    <Dialog
      icon="info-sign"
      onClose={handleClose}
      title={`${jurisdiction.name} Audit Information`}
      isOpen
    >
      <div className={Classes.DIALOG_BODY}>
        <p>
          <strong>Ballot Manifest Upload Status: </strong>
          {prettifyStatus(jurisdiction.ballotManifest.processing)}
        </p>
        <p>
          <strong>Current Ballot Manifest File: </strong>
          <a
            href={`/election/${electionId}/jurisdiction/${jurisdiction.id}/ballot-manifest/csv`}
            target="_blank"
            rel="noopener noreferrer"
          >
            {jurisdiction.ballotManifest.file
              ? jurisdiction.ballotManifest.file.name
              : 'N/A'}
          </a>
        </p>
      </div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <FormButton onClick={handleClose}>Close</FormButton>
        </div>
      </div>
    </Dialog>
  )
}

export default JurisdictionDetail
