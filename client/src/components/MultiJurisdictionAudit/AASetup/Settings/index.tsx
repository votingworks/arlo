import React from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import { Formik, FormikProps, Field, ErrorMessage } from 'formik'
import { RadioGroup, Radio, Spinner, HTMLSelect } from '@blueprintjs/core'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormSection from '../../../Atoms/Form/FormSection'
import { ErrorLabel } from '../../../Atoms/Form/_helpers'
import { parse as parseNumber } from '../../../../utils/number-schema'
import FormField from '../../../Atoms/Form/FormField'
import schema from './schema'
import useAuditSettings, { IAuditSettings } from '../../useAuditSettings'
import labelValueStates from './states'
import { range } from '../../../../utils/array'

const Select = styled(HTMLSelect)`
  margin-left: 5px;
`

interface IProps {
  locked: boolean
  nextStage: ISidebarMenuItem
  prevStage: ISidebarMenuItem
}

type IValues = Pick<
  IAuditSettings,
  'state' | 'electionName' | 'online' | 'randomSeed' | 'riskLimit'
>

const Settings: React.FC<IProps> = ({
  nextStage,
  prevStage,
  locked,
}: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [auditSettings, updateSettings] = useAuditSettings(electionId!)
  if (!auditSettings) return null // still loading
  const {
    state,
    electionName,
    randomSeed,
    riskLimit,
    online,
    auditType,
  } = auditSettings

  const submit = async (values: IValues) => {
    const response = await updateSettings({
      ...values,
      riskLimit: parseNumber(values.riskLimit), // Formik stringifies internally
    })
    if (!response) return
    /* istanbul ignore else */
    if (nextStage.activate) nextStage.activate()
    else throw new Error('Wrong menuItems passed in: activate() is missing')
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
      {({ handleSubmit, setFieldValue, values }: FormikProps<IValues>) => (
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
                    disabled={locked}
                    value={values.state}
                    options={[{ value: '' }, ...labelValueStates]}
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
                  disabled={locked}
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
                    disabled={locked}
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
                    disabled={locked}
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
                  disabled={locked}
                  component={FormField}
                />
              </label>
            </FormSection>
          </FormWrapper>
          {nextStage.state === 'processing' ? (
            <Spinner />
          ) : (
            <FormButtonBar>
              <FormButton onClick={prevStage.activate}>Back</FormButton>
              <FormButton
                intent="primary"
                disabled={nextStage.state === 'locked'}
                onClick={handleSubmit}
              >
                Save &amp; Next
              </FormButton>
            </FormButtonBar>
          )}
        </form>
      )}
    </Formik>
  )
}

export default Settings
