import React from 'react'
import { Classes, Dialog, Intent } from '@blueprintjs/core'
import FormButton from '../../../Atoms/Form/FormButton'

const ConfirmLaunch = ({
  isOpen,
  handleClose,
  handleSubmit,
  isSubmitting,
  message,
}: {
  isOpen: boolean
  handleClose: () => void
  handleSubmit: () => void
  isSubmitting: boolean
  message?: string
}) => {
  return (
    <Dialog
      icon="info-sign"
      onClose={handleClose}
      title="Are you sure you want to launch the audit?"
      isOpen={isOpen}
    >
      <div className={Classes.DIALOG_BODY}>{message && <p>{message}</p>}</div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <FormButton disabled={isSubmitting} onClick={handleClose}>
            Cancel
          </FormButton>
          <FormButton
            intent={Intent.PRIMARY}
            onClick={handleSubmit}
            loading={isSubmitting}
          >
            Launch Audit
          </FormButton>
        </div>
      </div>
    </Dialog>
  )
}

export default ConfirmLaunch
