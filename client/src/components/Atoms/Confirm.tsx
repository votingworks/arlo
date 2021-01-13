import React, {
  createContext,
  useContext,
  useState,
  ReactNode,
  useEffect,
  useCallback,
} from 'react'
import { Dialog, Classes, Button, Intent } from '@blueprintjs/core'
import { useLocation } from 'react-router-dom'

interface IConfirmOptions {
  title: ReactNode
  description: ReactNode
  yesButtonLabel?: string
  noButtonLabel?: string
  onYesClick: () => Promise<void>
}

const ConfirmContext = createContext<(options: IConfirmOptions) => void>(
  async () => {}
)

export const ConfirmProvider = ({
  children,
}: {
  children?: React.ReactNode
}) => {
  // We show the dialog whenever options are set.
  // On close, we set options to null.
  const [options, setOptions] = useState<IConfirmOptions | null>(null)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)

  // Close the dialog whenever the location changes (e.g. user clicks the back
  // button). Note: this means ConfirmProvider must be rendered inside Router.
  const location = useLocation()
  useEffect(() => setOptions(null), [location.key])

  const confirm = useCallback((newOptions: IConfirmOptions) => {
    setIsSubmitting(false)
    setOptions(newOptions)
  }, [])

  const handleYesClick = async () => {
    setIsSubmitting(true)
    try {
      await options!.onYesClick()
      setOptions(null)
    } catch (error) {
      // Do nothing, error handling is the responsibility of the caller
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    setOptions(null)
  }

  return (
    <>
      <ConfirmContext.Provider value={confirm}>
        {children}
      </ConfirmContext.Provider>
      <Dialog
        icon="info-sign"
        onClose={handleClose}
        title={options && options.title}
        isOpen={!!options}
      >
        <div className={Classes.DIALOG_BODY}>
          {options && options.description}
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button disabled={isSubmitting} onClick={handleClose}>
              {(options && options.noButtonLabel) || 'Cancel'}
            </Button>
            <Button
              intent={Intent.PRIMARY}
              onClick={handleYesClick}
              loading={isSubmitting}
            >
              {(options && options.yesButtonLabel) || 'Ok'}
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  )
}

export const useConfirm = () => useContext(ConfirmContext)
