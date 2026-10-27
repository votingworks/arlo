import React from 'react'
import { Button, Dialog, InputGroup, Classes } from '@blueprintjs/core'
import AsyncButton from '../Atoms/AsyncButton'
import { ErrorLabel } from '../Atoms/Form/_helpers'

export const RANDOM_SEED_INSTRUCTIONS =
  'Enter a series of random numbers to be used when drawing the random sample of ballots to audit.'

export const RANDOM_SEED_MAX_LENGTH = 100
export const RANDOM_SEED_MAX_LENGTH_ERROR = `Must be ${RANDOM_SEED_MAX_LENGTH} characters or fewer`

interface IRandomSeedModalProps {
  title: string
  submitButtonText: string
  initialValue: string | null
  onClose: () => void
  onSave: (seed: string) => Promise<void>
  // If true, the modal is always shown in presentation mode. Otherwise, the
  // user can toggle presentation mode on and off.
  alwaysPresentationMode?: boolean
}

const RandomSeedModal = ({
  title,
  submitButtonText,
  initialValue,
  onClose,
  onSave,
  alwaysPresentationMode = false,
}: IRandomSeedModalProps): JSX.Element => {
  const [value, setValue] = React.useState(initialValue || '')
  const [isPresentationModeToggled, setIsPresentationModeToggled] =
    React.useState(false)
  const isPresentationMode = alwaysPresentationMode || isPresentationModeToggled
  const isTooLong = value.length > RANDOM_SEED_MAX_LENGTH

  return (
    <Dialog
      isOpen
      onClose={onClose}
      title={title}
      {...(isPresentationMode && {
        // Zoom in the whole modal
        style: { transform: 'scale(2)' },
        // Darken the usual backdrop
        backdropProps: { style: { backgroundColor: 'rgba(16, 22, 26, 0.9)' } },
      })}
    >
      <div className={Classes.DIALOG_BODY}>
        <label htmlFor="random-seed-modal" id="random-seed-modal-label">
          <p>{RANDOM_SEED_INSTRUCTIONS}</p>
          <InputGroup
            id="random-seed-modal"
            aria-labelledby="random-seed-modal-label"
            type="text"
            value={value}
            onChange={(e: React.FormEvent<HTMLInputElement>) =>
              setValue(e.currentTarget.value)
            }
            large
            fill
            style={
              isPresentationMode
                ? { fontSize: '1.5em', letterSpacing: '0.2em' }
                : undefined
            }
          />
          {isTooLong && <ErrorLabel>{RANDOM_SEED_MAX_LENGTH_ERROR}</ErrorLabel>}
        </label>
      </div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          {!alwaysPresentationMode && (
            <Button
              minimal
              intent="primary"
              onClick={() => setIsPresentationModeToggled(!isPresentationMode)}
              style={{ marginRight: 'auto' }}
            >
              {isPresentationMode
                ? 'Exit Presentation Mode'
                : 'Presentation Mode'}
            </Button>
          )}
          <Button onClick={onClose}>Cancel</Button>
          <AsyncButton
            intent="success"
            icon="tick"
            disabled={!value || isTooLong}
            onClick={async () => {
              await onSave(value)
              onClose()
            }}
          >
            {submitButtonText}
          </AsyncButton>
        </div>
      </div>
    </Dialog>
  )
}

export default RandomSeedModal
