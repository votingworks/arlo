import React, { useState } from 'react'
import { Classes, Dialog, Intent } from '@blueprintjs/core'
import FormButton from '../../../Atoms/Form/FormButton'

export interface IDialogExampleState {
  autoFocus: boolean
  canEscapeKeyClose: boolean
  canOutsideClickClose: boolean
  enforceFocus: boolean
  isOpen: boolean
  usePortal: boolean
}

const useConfirmLaunch = (
  launch: () => void
): [() => void, React.ReactElement] => {
  const [isOpen, setIsOpen] = useState(false)
  const handleClose = () => setIsOpen(false)
  const dialog = (
    <Dialog
      icon="info-sign"
      onClose={handleClose}
      title="Are you sure you want to launch the audit?"
      isOpen={isOpen}
    >
      <div className={Classes.DIALOG_BODY}>
        <p>This action cannot be undone</p>
      </div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <FormButton onClick={handleClose}>Close Without Launching</FormButton>
          <FormButton intent={Intent.PRIMARY} onClick={launch}>
            Launch Audit
          </FormButton>
        </div>
      </div>
    </Dialog>
  )
  return [() => setIsOpen(true), dialog]
}

export default useConfirmLaunch
