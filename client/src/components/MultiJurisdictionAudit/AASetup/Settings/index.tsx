import React from 'react'
import { useParams } from 'react-router-dom'
import { Formik, FormikProps, Field, ErrorMessage } from 'formik'
import { RadioGroup, Radio, Spinner } from '@blueprintjs/core'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import { IValues } from './types'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormSection from '../../../Atoms/Form/FormSection'
import { Select } from '../../../SingleJurisdictionAudit/EstimateSampleSize'
import { generateOptions, ErrorLabel } from '../../../Atoms/Form/_helpers'
import { parse as parseNumber } from '../../../../utils/number-schema'
import FormField from '../../../Atoms/Form/FormField'
import schema from './schema'
import useAuditSettings from '../../useAuditSettings'

interface IProps {
  locked: boolean
  nextStage: ISidebarMenuItem
  prevStage: ISidebarMenuItem
}

const Settings: React.FC<IProps> = ({
  nextStage,
  prevStage,
  locked,
}: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [auditSettings, updateState] = useAuditSettings(electionId!)
  if (!auditSettings) return null // still loading
  const {
    electionName,
    randomSeed,
    riskLimit,
    online,
    auditType,
  } = auditSettings
  const submit = async (values: IValues) => {
    const response = await updateState({
      ...values,
      riskLimit: parseNumber(values.riskLimit), // Formik stringifies internally
    })
    if (!response) return
    /* istanbul ignore else */
    if (nextStage.activate) nextStage.activate()
    else throw new Error('Wrong menuItems passed in: activate() is missing')
  }
  const initialValues = {
    electionName: electionName === null ? '' : electionName,
    randomSeed: randomSeed === null ? '' : randomSeed,
    riskLimit: riskLimit === null ? 10 : riskLimit,
    online:
      auditType === 'BATCH_COMPARISON' // batch comparison audits are always offline
        ? false
        : online === null
        ? true
        : online,
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
            <FormSection>
              {/* eslint-disable jsx-a11y/label-has-associated-control */}
              <label htmlFor="election-name" id="election-name-label">
                Election Name
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
              <FormSection>
                <label htmlFor="online">
                  Audit boards will enter data about each audited ballot:
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
                {`Set the risk for the audit as a percentage (e.g. "5" = 5%)`}
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
                  {generateOptions(20)}
                </Field>
                <ErrorMessage name="riskLimit" component={ErrorLabel} />
              </label>
            </FormSection>
            <FormSection label="Random Seed">
              {/* eslint-disable jsx-a11y/label-has-associated-control */}
              <label htmlFor="random-seed" id="random-seed-label">
                Enter the random characters to seed the pseudo-random number
                generator.
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
                type="submit"
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
