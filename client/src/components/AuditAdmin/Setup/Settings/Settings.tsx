import React from 'react'
import { Formik, FormikProps, Field, ErrorMessage } from 'formik'
import {
  RadioGroup,
  Radio,
  HTMLSelect,
  Button,
  Dialog,
  InputGroup,
  Classes,
} from '@blueprintjs/core'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormSection from '../../../Atoms/Form/FormSection'
import { ErrorLabel } from '../../../Atoms/Form/_helpers'
import { parse as parseNumber } from '../../../../utils/number-schema'
import FormField from '../../../Atoms/Form/FormField'
import schema from './schema'
import {
  IAuditSettings,
  useUpdateAuditSettings,
  useAuditSettings,
} from '../../../useAuditSettings'
import { stateOptions } from './states'
import { range } from '../../../../utils/array'
import AsyncButton from '../../../Atoms/AsyncButton'

const RANDOM_SEED_INSTRUCTIONS =
  'Enter a series of random numbers to be used when drawing the random sample of ballots to audit.'

const RandomSeedModal = ({
  initialValue,
  onClose,
  onSave,
}: {
  initialValue: string | null
  onClose: () => void
  onSave: (seed: string) => Promise<void>
}): JSX.Element => {
  const [value, setValue] = React.useState(initialValue || '')
  return (
    <Dialog
      isOpen
      onClose={onClose}
      title="Enter Random Seed"
      // Zoom in the whole modal
      style={{ transform: 'scale(2)' }}
      // Darken the usual backdrop
      backdropProps={{ style: { backgroundColor: 'rgba(16, 22, 26, 0.9)' } }}
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
            style={{
              fontSize: '1.5em',
              letterSpacing: '0.2em',
            }}
          />
        </label>
      </div>
      <div className={Classes.DIALOG_FOOTER}>
        <div className={Classes.DIALOG_FOOTER_ACTIONS}>
          <Button onClick={onClose}>Cancel</Button>
          <AsyncButton
            intent="success"
            icon="tick"
            disabled={!value}
            onClick={async () => {
              await onSave(value)
              onClose()
            }}
          >
            Set Random Seed
          </AsyncButton>
        </div>
      </div>
    </Dialog>
  )
}

interface IProps {
  electionId: string
  goToPrevStage: () => void
  goToNextStage: () => void
}

type IValues = Pick<
  IAuditSettings,
  'state' | 'electionName' | 'online' | 'randomSeed' | 'riskLimit'
>

const Settings: React.FC<IProps> = ({
  electionId,
  goToPrevStage,
  goToNextStage,
}: IProps) => {
  const auditSettingsQuery = useAuditSettings(electionId)
  const updateAuditSettingsMutation = useUpdateAuditSettings(electionId)
  const [isSeedModalOpen, setIsSeedModalOpen] = React.useState(false)

  if (!auditSettingsQuery.isSuccess) return null
  const auditSettings = auditSettingsQuery.data

  const {
    state,
    electionName,
    randomSeed,
    riskLimit,
    online,
    auditType,
  } = auditSettings

  const saveSettings = async (values: IValues) => {
    await updateAuditSettingsMutation.mutateAsync({
      ...values,
      riskLimit: parseNumber(values.riskLimit), // Formik stringifies internally
    })
  }

  const initialValues = {
    state: state === null ? '' : state,
    electionName: electionName === null ? '' : electionName,
    randomSeed: randomSeed === null ? '' : randomSeed,
    riskLimit: riskLimit === null ? 10 : riskLimit,
    online,
  }

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={schema}
      onSubmit={async values => {
        await saveSettings(values)
        goToNextStage()
      }}
      enableReinitialize
    >
      {({
        handleSubmit,
        setFieldValue,
        values,
        isSubmitting,
      }: FormikProps<IValues>) => (
        <form
          data-testid="form-one"
          style={{ width: '100%' }}
          onSubmit={handleSubmit}
        >
          <FormWrapper title="Audit Settings">
            <FormSection label="State">
              {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
              <label htmlFor="state">
                <p>Choose your state from the options below.</p>
                <div>
                  <Field
                    component={HTMLSelect}
                    id="state"
                    name="state"
                    onChange={(e: React.FormEvent<HTMLSelectElement>) =>
                      setFieldValue('state', e.currentTarget.value)
                    }
                    value={values.state}
                    options={[{ value: '' }, ...stateOptions]}
                  />
                  <ErrorMessage name="state" component={ErrorLabel} />
                </div>
              </label>
            </FormSection>
            <FormSection label="Election Name">
              {/* eslint-disable jsx-a11y/label-has-associated-control */}
              <label htmlFor="election-name" id="election-name-label">
                <p>Enter the name of the election you are auditing.</p>
                <Field
                  id="election-name"
                  aria-labelledby="election-name-label"
                  name="electionName"
                  component={FormField}
                />
              </label>
            </FormSection>
            {auditType === 'BALLOT_POLLING' && (
              <FormSection label="Audit Board Data Entry">
                <label>
                  <p>Audit boards will enter data about each audited ballot:</p>
                  <RadioGroup
                    name="online"
                    data-testid="online-toggle"
                    onChange={e =>
                      setFieldValue(
                        'online',
                        e.currentTarget.value === 'online'
                      )
                    }
                    selectedValue={values.online ? 'online' : 'offline'}
                  >
                    <Radio value="online">Online</Radio>
                    <Radio value="offline">Offline</Radio>
                  </RadioGroup>
                </label>
              </FormSection>
            )}
            <FormSection label="Desired Risk Limit">
              <label htmlFor="risk-limit">
                <p>Set the risk limit for the audit.</p>
                <div>
                  <Field
                    id="risk-limit"
                    data-testid="risk-limit"
                    name="riskLimit"
                    component={HTMLSelect}
                    value={values.riskLimit}
                    onChange={(e: React.FormEvent<HTMLSelectElement>) =>
                      setFieldValue('riskLimit', e.currentTarget.value)
                    }
                  >
                    {range(1, 20).map(n => (
                      <option value={n} key={n}>
                        {n}%
                      </option>
                    ))}
                  </Field>
                  <ErrorMessage name="riskLimit" component={ErrorLabel} />
                </div>
              </label>
            </FormSection>
            <FormSection label="Random Seed">
              <label htmlFor="random-seed" id="random-seed-label">
                <p>{RANDOM_SEED_INSTRUCTIONS}</p>
                <div
                  style={{
                    display: 'flex',
                    gap: '0.5rem',
                    alignItems: 'start',
                  }}
                >
                  <Field
                    id="random-seed"
                    aria-labelledby="random-seed-label"
                    type="text"
                    name="randomSeed"
                    component={FormField}
                  />
                  <Button
                    minimal
                    intent="primary"
                    onClick={() => setIsSeedModalOpen(true)}
                    style={{ marginTop: '5px' }}
                  >
                    Presentation Mode
                  </Button>
                </div>
              </label>
            </FormSection>
          </FormWrapper>
          <FormButtonBar>
            <Button onClick={goToPrevStage} icon="arrow-left">
              Back
            </Button>
            <Button
              type="submit"
              intent="primary"
              rightIcon="arrow-right"
              loading={isSubmitting}
            >
              Save &amp; Next
            </Button>
          </FormButtonBar>
          {isSeedModalOpen && (
            <RandomSeedModal
              initialValue={values.randomSeed}
              onClose={() => setIsSeedModalOpen(false)}
              onSave={value => saveSettings({ ...values, randomSeed: value })}
            />
          )}
        </form>
      )}
    </Formik>
  )
}

export default Settings
