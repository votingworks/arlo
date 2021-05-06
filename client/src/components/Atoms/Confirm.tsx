import React, { useState, ReactNode } from 'react'
import { Dialog, Classes, Button, Intent } from '@blueprintjs/core'

export interface IConfirmOptions {
  title: ReactNode
  description: ReactNode
  yesButtonLabel?: string
  yesButtonIntent?: Intent
  noButtonLabel?: string
  onYesClick: () => Promise<void>
}

export const useConfirm = () => {
  // We show the dialog whenever options are set.
  // On close, we set options to null.
  const [options, setOptions] = useState<IConfirmOptions | null>(null)

  const confirm = (newOptions: IConfirmOptions | null) => {
    setOptions(newOptions)
  }

  const onYesClick = async () => {
    await options!.onYesClick()
    setOptions(null)
  }

  const onClose = () => {
    setOptions(null)
  }

  const confirmProps = {
    isOpen: !!options,
    title: options ? options.title : '',
    description: options ? options.description : '',
    yesButtonLabel: options ? options.yesButtonLabel : undefined,
    yesButtonIntent: options ? options.yesButtonIntent : undefined,
    noButtonLabel: options ? options.noButtonLabel : undefined,
    onYesClick,
    onClose,
  }

  return { confirm, confirmProps }
}

interface IConfirmProps extends IConfirmOptions {
  isOpen: boolean
  onClose: () => void
}

export const Confirm = ({
  isOpen,
  title,
  description,
  yesButtonLabel,
  yesButtonIntent,
  noButtonLabel,
  onYesClick,
  onClose,
}: IConfirmProps) => {
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)

  const handleYesClick = async () => {
    setIsSubmitting(true)
    try {
      await onYesClick()
    } catch (error) {
      // Do nothing, error handling should happen within onYesClick
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog icon="info-sign" onClose={onClose} title={title} isOpen={isOpen}>
      <div className={Classes.DIALOG_BODY}>{description}</div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <Button disabled={isSubmitting} onClick={onClose}>
            {noButtonLabel || 'Cancel'}
          </Button>
          <Button
            intent={yesButtonIntent || Intent.PRIMARY}
            onClick={handleYesClick}
            loading={isSubmitting}
          >
            {yesButtonLabel || 'Ok'}
          </Button>
        </div>
      </div>
    </Dialog>
  )
}
