import React from 'react'
import { useParams } from 'react-router-dom'
import { Formik, FormikProps, Form, Field, ErrorMessage } from 'formik'
import { RadioGroup, Radio, Spinner } from '@blueprintjs/core'
import FormButtonBar from '../../../Form/FormButtonBar'
import FormButton from '../../../Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import { IValues } from './types'
import FormWrapper from '../../../Form/FormWrapper'
import FormSection from '../../../Form/FormSection'
import { Select } from '../../EstimateSampleSize'
import { generateOptions, ErrorLabel } from '../../../Form/_helpers'
import { parse as parseNumber } from '../../../../utils/number-schema'
import FormField from '../../../Form/FormField'
import schema from './schema'
import useAuditSettings from '../useAuditSettings'

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
  const { electionId } = useParams()
  const [
    { electionName, randomSeed, riskLimit, online },
    updateState,
  ] = useAuditSettings(electionId!)
  const submit = async (values: IValues) => {
    const response = await updateState({
      ...values,
      riskLimit: parseNumber(values.riskLimit), // Formik stringifies internally
    })
    if (!response) return
    nextStage.activate()
  }
  const initialValues = {
    electionName: electionName === null ? '' : electionName,
    randomSeed: randomSeed === null ? '' : randomSeed,
    riskLimit: riskLimit === null ? 10 : riskLimit,
    online: online === null ? true : online,
  }
  return (
    <Formik
      initialValues={initialValues}
      validationSchema={schema}
      onSubmit={submit}
      enableReinitialize
    >
      {({ handleSubmit, setFieldValue, values }: FormikProps<IValues>) => (
        <Form data-testid="form-one">
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
            <FormSection>
              <label htmlFor="online">
                Audit boards will enter data about each audited ballot:
                <RadioGroup
                  name="online"
                  data-testid="online-toggle"
                  onChange={e =>
                    setFieldValue('online', e.currentTarget.value === 'online')
                  }
                  selectedValue={values.online ? 'online' : 'offline'}
                  disabled={locked}
                >
                  <Radio value="online">Online</Radio>
                  <Radio value="offline">Offline</Radio>
                </RadioGroup>
              </label>
            </FormSection>
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
        </Form>
      )}
    </Formik>
  )
}

export default Settings
