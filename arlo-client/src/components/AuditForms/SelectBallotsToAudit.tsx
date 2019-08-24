/* eslint-disable no-null */

import React from 'react'
import { toast } from 'react-toastify'
import { Formik, FormikProps, Field, getIn } from 'formik'
import * as Yup from 'yup'
import uuidv4 from 'uuidv4'
import { RadioGroup, Radio, HTMLSelect, FileInput } from '@blueprintjs/core'
import FormSection, {
  FormSectionDescription,
  FormSectionLabel,
} from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormButton from '../Form/FormButton'
import FormButtonBar from '../Form/FormButtonBar'
import { Jurisdiction, Audit, SampleSizeOption } from '../../types'
import { api } from '../utilities'
import { generateOptions, ErrorLabel } from '../Form/_helpers'
import FormTitle from '../Form/FormTitle'

interface SampleSizeOptionsByContest {
  [key: string]: SampleSizeOption[]
}

interface Props {
  audit: Audit
  isLoading: boolean
  setIsLoading: (isLoading: boolean) => void
  updateAudit: () => void
  getStatus: () => Promise<Audit>
}

interface SelectBallotsToAuditValues {
  auditBoards: string
  manifest: File | null
  sampleSize: {
    [key: string]: string
  }
}

const schema = Yup.object().shape({
  auditBoards: Yup.number()
    .typeError('Must be a number')
    .min(1, 'Too few Audit Boards')
    .max(15, 'Too many Audit Boards')
    .required('Required'),
  manifest: Yup.mixed()
    .required('You must upload a manifest')
    .test(
      'fileType',
      'You must upload a CSV file',
      value => value && value.type === 'text/csv'
    ),
})

const SelectBallotsToAudit: React.FC<Props> = ({
  audit,
  isLoading,
  setIsLoading,
  updateAudit,
  getStatus,
}: Props) => {
  const manifestUploaded =
    audit.jurisdictions.length &&
    audit.jurisdictions[0].ballotManifest &&
    audit.jurisdictions[0].ballotManifest.filename &&
    audit.jurisdictions[0].ballotManifest.numBallots &&
    audit.jurisdictions[0].ballotManifest.numBatches

  const handlePost = async (values: SelectBallotsToAuditValues) => {
    try {
      const auditBoards = Array.from(
        Array(parseInt(values.auditBoards)).keys()
      ).map(i => {
        return {
          id: `audit-board-${i + 1}`,
          name: `Audit Board #${i + 1}`,
          members: [],
        }
      })

      // upload jurisdictions
      const data: Jurisdiction[] = [
        {
          id: uuidv4(),
          name: 'Jurisdiction 1',
          contests: [...audit.contests].map(contest => contest.id),
          auditBoards: auditBoards,
        },
      ]
      setIsLoading(true)
      /* istanbul ignore else */
      if (Object.values(values.sampleSize).some(sampleSize => !!sampleSize)) {
        const body = {
          size: values.sampleSize[audit.contests[0].id], // until multiple contests are supported
        }
        await api('/audit/sample-size', {
          method: 'POST',
          body: JSON.stringify(body),
          headers: {
            'Content-Type': 'application/json',
          },
        })
      }
      await api('/audit/jurisdictions', {
        method: 'POST',
        body: JSON.stringify({ jurisdictions: data }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const newStatus = await getStatus()
      const jurisdictionID: string = newStatus.jurisdictions[0].id

      /* istanbul ignore else */
      if (values.manifest) {
        const formData: FormData = new FormData()
        formData.append('manifest', values.manifest, values.manifest.name)
        await api(`/jurisdiction/${jurisdictionID}/manifest`, {
          method: 'POST',
          body: formData,
        })
      }

      updateAudit()
    } catch (err) {
      toast.error(err.message)
    }
  }

  const initialState: SelectBallotsToAuditValues = {
    auditBoards:
      '' +
      ((audit.jurisdictions.length &&
        audit.jurisdictions[0].auditBoards.length) ||
        1),
    manifest: null,
    sampleSize: [...audit.contests].reduce(
      (a: { [key: string]: string }, c) => {
        a[c.id] =
          c.sampleSizeOptions && c.sampleSizeOptions.length
            ? c.sampleSizeOptions[0].size.toString()
            : ''
        if (audit.rounds[0]) {
          const rc = audit.rounds[0].contests.find(v => v.id === c.id)
          a[c.id] = rc!.sampleSize.toString()
        }
        return a
      },
      {}
    ),
  }

  const sampleSizeOptions = [...audit.contests].reduce<
    SampleSizeOptionsByContest
  >((acc, contest) => {
    acc[contest.id] =
      contest.sampleSizeOptions && contest.sampleSizeOptions.length
        ? contest.sampleSizeOptions.reduce<SampleSizeOption[]>(
            (acc, option) => {
              const duplicateOptionIndex: number = acc.findIndex(
                v => Number(v.size) === option.size
              )
              const duplicateOption =
                duplicateOptionIndex > -1 ? acc[duplicateOptionIndex] : false
              if (duplicateOption) {
                if (
                  option.prob &&
                  duplicateOption.prob &&
                  Number(duplicateOption.prob) < option.prob
                ) {
                  duplicateOption.prob = option.prob
                }
              } else {
                acc.push({
                  ...option,
                  size: option.size.toString(),
                })
              }
              return acc
            },
            []
          )
        : []
    return acc
  }, {})

  return (
    <Formik
      initialValues={initialState}
      validationSchema={schema}
      onSubmit={handlePost}
      enableReinitialize
      render={({
        handleBlur,
        handleChange,
        handleSubmit,
        values,
        errors,
        touched,
        setFieldValue,
      }: FormikProps<SelectBallotsToAuditValues>) => (
        <form onSubmit={handleSubmit} id="formTwo" data-testid="form-two">
          <hr />
          <FormWrapper>
            <FormTitle>Select Ballots to Audit</FormTitle>
            {Object.keys(sampleSizeOptions).length &&
              Object.values(sampleSizeOptions).some(v => !!v.length) && (
                <FormSection>
                  <FormSectionLabel>Estimated Sample Size</FormSectionLabel>
                  <FormSectionDescription>
                    Choose the initial sample size for each contest you would
                    like to use for Round 1 of the audit from the options below.
                  </FormSectionDescription>
                  {Object.keys(sampleSizeOptions).map((key, i) => (
                    <React.Fragment key={key}>
                      {Object.keys(sampleSizeOptions).length > 1 && (
                        /* istanbul ignore next */
                        <FormSectionLabel>
                          Contest {i + 1} sample size
                        </FormSectionLabel>
                      )}
                      <FormSectionDescription>
                        <RadioGroup
                          name={`sampleSize[${key}]`}
                          onChange={e =>
                            setFieldValue(
                              `sampleSize[${key}]`,
                              e.currentTarget.value
                            )
                          }
                          selectedValue={getIn(values, `sampleSize[${key}]`)}
                          disabled={!!audit.rounds.length}
                        >
                          {sampleSizeOptions[key].map((option, j) => {
                            return (
                              <Radio value={option.size} key={option.size}>
                                {option.type
                                  ? 'BRAVO Average Sample Number: '
                                  : ''}
                                {`${option.size} samples`}
                                {option.prob
                                  ? ` (${option.prob *
                                      100}% chance of reaching risk limit and completing the audit in one round)`
                                  : ''}
                              </Radio>
                            )
                          })}
                        </RadioGroup>
                      </FormSectionDescription>
                    </React.Fragment>
                  ))}
                </FormSection>
              )}
            <FormSection
              label="Number of Audit Boards"
              description="Set the number of audit boards you with to use."
            >
              <Field
                component={HTMLSelect}
                id="auditBoards"
                data-testid="audit-boards"
                name="auditBoards"
                onChange={(e: React.FormEvent<HTMLSelectElement>) =>
                  setFieldValue('auditBoards', e.currentTarget.value)
                }
                disabled={!!audit.rounds.length}
              >
                {generateOptions(15)}
              </Field>
            </FormSection>
            <FormSection label="Ballot Manifest">
              {manifestUploaded && audit.jurisdictions[0].ballotManifest ? ( // duplicating effect of manifestUploaded for TS
                <React.Fragment>
                  <FormSectionDescription>
                    <b>Filename:</b>{' '}
                    {audit.jurisdictions[0].ballotManifest.filename}
                  </FormSectionDescription>
                  <FormSectionDescription>
                    <b>Ballots:</b>{' '}
                    {audit.jurisdictions[0].ballotManifest.numBallots}
                  </FormSectionDescription>
                  <FormSectionDescription>
                    <b>Batches:</b>{' '}
                    {audit.jurisdictions[0].ballotManifest.numBatches}
                  </FormSectionDescription>
                </React.Fragment>
              ) : (
                <React.Fragment>
                  <FormSectionDescription>
                    Click &quot;Browse&quot; to choose the appropriate Ballot
                    Manifest file from your computer
                  </FormSectionDescription>
                  <FileInput
                    inputProps={{
                      accept: '.csv',
                      name: 'manifest',
                    }}
                    onInputChange={e => {
                      setFieldValue(
                        'manifest',
                        (e.currentTarget.files && e.currentTarget.files[0]) ||
                          null
                      )
                    }}
                    hasSelection={!!values.manifest}
                    text={
                      values.manifest
                        ? values.manifest.name
                        : 'Select manifest...'
                    }
                    onBlur={handleBlur}
                  />
                  {errors.manifest && touched.manifest && (
                    <ErrorLabel>{errors.manifest}</ErrorLabel>
                  )}
                </React.Fragment>
              )}
            </FormSection>
          </FormWrapper>
          {!audit.rounds.length && isLoading && <p>Loading...</p>}
          {!audit.rounds.length && !isLoading && (
            <FormButtonBar>
              <FormButton intent="primary" type="button" onClick={handleSubmit}>
                Select Ballots To Audit
              </FormButton>
            </FormButtonBar>
          )}
        </form>
      )}
    />
  )
}

export default React.memo(SelectBallotsToAudit)
