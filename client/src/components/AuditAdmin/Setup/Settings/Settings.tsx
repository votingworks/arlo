import React from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Formik, FormikProps, Field, ErrorMessage } from 'formik'
import { RadioGroup, Radio, HTMLSelect } from '@blueprintjs/core'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
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

const Select = styled(HTMLSelect)`
  margin-left: 5px;
`

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

  const submit = async (values: IValues) => {
    await updateAuditSettingsMutation.mutateAsync({
      ...values,
      riskLimit: parseNumber(values.riskLimit), // Formik stringifies internally
    })
    goToNextStage()
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
      onSubmit={submit}
      enableReinitialize
    >
      {({
        handleSubmit,
        setFieldValue,
        values,
        isSubmitting,
      }: FormikProps<IValues>) => (
        <form data-testid="form-one">
          <FormWrapper title="Audit Settings">
            <FormSection label="State">
              {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
              <label htmlFor="state">
                <p>Choose your state from the options below.</p>
                <div>
                  <Field
                    component={Select}
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
                <label htmlFor="online">
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
                    component={Select}
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
              {}
              <label htmlFor="random-seed" id="random-seed-label">
                <p>
                  Enter the random characters to seed the pseudo-random number
                  generator.
                </p>
                <Field
                  id="random-seed"
                  aria-labelledby="random-seed-label"
                  type="text"
                  name="randomSeed"
                  component={FormField}
                />
              </label>
            </FormSection>
          </FormWrapper>
          <FormButtonBar>
            <FormButton onClick={goToPrevStage}>Back</FormButton>
            <FormButton
              intent="primary"
              loading={isSubmitting}
              onClick={handleSubmit}
            >
              Save &amp; Next
            </FormButton>
          </FormButtonBar>
        </form>
      )}
    </Formik>
  )
}

export default Settings
