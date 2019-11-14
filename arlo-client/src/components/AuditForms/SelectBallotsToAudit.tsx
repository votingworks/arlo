/* eslint-disable no-null */

import React from 'react'
import { toast } from 'react-toastify'
import {
  Formik,
  FormikProps,
  Field,
  getIn,
  FieldArray,
  ArrayHelpers,
} from 'formik'
import * as Yup from 'yup'
import uuidv4 from 'uuidv4'
import QRCode from 'qrcode.react'
import {
  RadioGroup,
  Radio,
  HTMLSelect,
  FileInput,
  Spinner,
} from '@blueprintjs/core'
import styled from 'styled-components'
import { Link } from 'react-router-dom'
import FormSection, {
  FormSectionDescription,
  FormSectionLabel,
} from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormButton from '../Form/FormButton'
import FormButtonBar from '../Form/FormButtonBar'
import {
  IJurisdiction,
  IAudit,
  ISampleSizeOption,
  IAuditBoard,
} from '../../types'
import { api, testNumber, openQR } from '../utilities'
import { generateOptions, ErrorLabel } from '../Form/_helpers'
import FormTitle from '../Form/FormTitle'
import FormField from '../Form/FormField'
import number, { parse as parseNumber } from '../../utils/number-schema'
import { formattedUpTo } from '../../utils/indexes'

export const Select = styled(HTMLSelect)`
  margin-left: 5px;
`
export const AuditBoardsWrapper = styled.div`
  display: flex;
  flex-wrap: wrap;
`

export const AuditBoard = styled.div`
  display: flex;
  flex-direction: column;
  margin: 5px 20px 5px 0;
  width: 100px;
  text-align: center;
`

// override size on QR element to display in grid
export const QR = styled(QRCode)`
  margin: 2px;
  border: 1px solid #000000;
  cursor: pointer;
  /* stylelint-disable */
  width: 90px !important;
  height: 90px !important;
  /* stylelint-enable */
  padding: 3px;
`

interface ISampleSizeOptionsByContest {
  [key: string]: ISampleSizeOption[]
}

interface IProps {
  audit: IAudit
  isLoading: boolean
  setIsLoading: (isLoading: boolean) => void
  updateAudit: () => void
  getStatus: () => Promise<IAudit>
  electionId: string
}

interface ISelectBallotsToAuditValues {
  auditBoards: string
  auditNames: string[]
  manifest: File | null
  sampleSize: {
    [key: string]: string
  }
  customSampleSize: {
    [key: string]: string
  }
}

const schema = Yup.object().shape({
  auditBoards: number()
    .typeError('Must be a number')
    .min(1, 'Too few Audit Boards')
    .max(15, 'Too many Audit Boards')
    .required('Required'),
  manifest: Yup.mixed().required('You must upload a manifest'),
})

const SelectBallotsToAudit: React.FC<IProps> = ({
  audit,
  isLoading,
  setIsLoading,
  updateAudit,
  getStatus,
  electionId,
}: IProps) => {
  const manifestUploaded =
    audit.jurisdictions.length &&
    audit.jurisdictions[0].ballotManifest &&
    audit.jurisdictions[0].ballotManifest.filename &&
    audit.jurisdictions[0].ballotManifest.numBallots &&
    audit.jurisdictions[0].ballotManifest.numBatches
  const sampleSizeSelected = audit.rounds[0].contests.every(c => !!c.sampleSize)

  const handlePost = async (values: ISelectBallotsToAuditValues) => {
    try {
      const auditBoards = [
        ...formattedUpTo(parseNumber(values.auditBoards)),
      ].map(auditBoardIndex => {
        return {
          id: uuidv4(),
          name: `Audit Board #${auditBoardIndex}`,
          members: [],
        }
      })

      // upload jurisdictions
      const data: IJurisdiction[] = [
        {
          id: uuidv4(),
          name: 'Jurisdiction 1',
          contests: audit.contests.map(contest => contest.id),
          auditBoards,
        },
      ]
      setIsLoading(true)
      /* istanbul ignore else */
      if (Object.values(values.sampleSize).some(sampleSize => !!sampleSize)) {
        const size =
          values.sampleSize[audit.contests[0].id] === 'custom'
            ? values.customSampleSize[audit.contests[0].id]
            : values.sampleSize[audit.contests[0].id]
        const body = {
          size, // until multiple contests are supported
        }
        await api(`/election/${electionId}/audit/sample-size`, {
          method: 'POST',
          body: JSON.stringify(body),
          headers: {
            'Content-Type': 'application/json',
          },
        })
      }
      await api(`/election/${electionId}/audit/jurisdictions`, {
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
        await api(
          `/election/${electionId}/jurisdiction/${jurisdictionID}/manifest`,
          {
            method: 'POST',
            body: formData,
          }
        )
      }

      updateAudit()
    } catch (err) {
      toast.error(err.message)
    }
  }

  const numberOfBoards =
    (audit.jurisdictions.length && audit.jurisdictions[0].auditBoards.length) ||
    1
  const auditNames =
    audit.jurisdictions.length && audit.jurisdictions[0].auditBoards.length
      ? audit.jurisdictions[0].auditBoards.map(
          (board: IAuditBoard) => board.name
        )
      : Array(numberOfBoards).fill('')
  const initialState: ISelectBallotsToAuditValues = {
    auditBoards: '' + numberOfBoards,
    auditNames,
    manifest: null, // eslint-disable-line no-null/no-null
    sampleSize: [...audit.rounds[0].contests].reduce(
      (a: { [key: string]: string }, c) => {
        a[c.id] =
          c.sampleSizeOptions && c.sampleSizeOptions.length
            ? c.sampleSizeOptions[0].size.toString()
            : ''
        if (c.sampleSize) {
          a[c.id] = c.sampleSize.toString()
        }
        return a
      },
      {}
    ),
    customSampleSize: [...audit.rounds[0].contests].reduce(
      (a: { [key: string]: string }, c) => {
        a[c.id] = ''
        if (c.sampleSize) {
          a[c.id] = c.sampleSize.toString()
        }
        return a
      },
      {}
    ),
  }

  const sampleSizeOptions = [...audit.rounds[0].contests].reduce<
    ISampleSizeOptionsByContest
  >((acc, contest) => {
    acc[contest.id] =
      contest.sampleSizeOptions && contest.sampleSizeOptions.length
        ? contest.sampleSizeOptions.reduce<ISampleSizeOption[]>(
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
      validateOnChange={false}
      render={({
        handleBlur,
        handleSubmit,
        values,
        errors,
        touched,
        setFieldValue,
      }: FormikProps<ISelectBallotsToAuditValues>) => (
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
                          disabled={sampleSizeSelected}
                        >
                          {sampleSizeOptions[key].map(option => {
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
                          <Radio value="custom">
                            Enter your own sample size (not recommended)
                          </Radio>
                          {getIn(values, `sampleSize[${key}]`) === 'custom' && (
                            <Field
                              component={FormField}
                              name={`customSampleSize[${key}]`}
                              validate={testNumber(
                                Number(audit.contests[i].totalBallotsCast),
                                'Must be less than or equal to the total number of ballots'
                              )}
                              data-testid={`customSampleSize[${key}]`}
                            />
                          )}
                        </RadioGroup>
                      </FormSectionDescription>
                    </React.Fragment>
                  ))}
                </FormSection>
              )}
            <FieldArray
              name="auditNames"
              render={(utils: ArrayHelpers) => {
                const changeBoards = (n: number) => {
                  const num = values.auditNames.length
                  setFieldValue('auditBoards', n)
                  if (n > num) {
                    Array.from(Array(n - num).keys()).forEach(() =>
                      utils.push('')
                    )
                  }
                  if (n < num) {
                    Array.from(Array(num - n).keys()).forEach(() => utils.pop())
                  }
                }
                return (
                  <FormSection label="Audit Boards">
                    <label htmlFor="auditBoards">
                      Set the number of audit boards you wish to use.
                      <Field
                        component={Select}
                        id="auditBoards"
                        name="auditBoards"
                        onChange={(e: React.FormEvent<HTMLSelectElement>) =>
                          changeBoards(Number(e.currentTarget.value))
                        }
                        disabled={sampleSizeSelected}
                      >
                        {generateOptions(15)}
                      </Field>
                    </label>
                    <AuditBoardsWrapper>
                      {values.auditNames.map((name, i) => (
                        /* eslint-disable react/no-array-index-key */
                        <AuditBoard key={i}>
                          {/* <Field
                            name={`auditNames[${i}]`}
                            data-testid={`audit-name-${i}`}
                            disabled={sampleSizeSelected}
                          /> */}
                          {sampleSizeSelected && (
                            <>
                              <Link
                                to={`/election/${electionId}/board/${audit.jurisdictions[0].auditBoards[i].id}`}
                                className="bp3-text-small"
                              >
                                {name}
                              </Link>
                              {/* eslint-disable jsx-a11y/click-events-have-key-events, jsx-a11y/interactive-supports-focus */}
                              <span
                                id={`qr-${audit.jurisdictions[0].auditBoards[i].id}`}
                                title="Click to print"
                                role="button"
                                onClick={() =>
                                  openQR(
                                    audit.jurisdictions[0].auditBoards[i].id,
                                    name
                                  )
                                }
                              >
                                <QR
                                  value={`http://localhost:3000/election/${electionId}/board/${audit.jurisdictions[0].auditBoards[i].id}`}
                                  size={250} // set size for printing so resolution is right
                                />
                              </span>
                            </>
                          )}
                        </AuditBoard>
                      ))}
                    </AuditBoardsWrapper>
                  </FormSection>
                )
              }}
            />
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
                          undefined
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
          {!sampleSizeSelected && isLoading && <Spinner />}
          {!sampleSizeSelected && !isLoading && (
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
