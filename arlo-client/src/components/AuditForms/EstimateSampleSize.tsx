import React from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import {
  Formik,
  FormikProps,
  Form,
  Field,
  FieldArray,
  ErrorMessage,
} from 'formik'
import * as Yup from 'yup'
import uuidv4 from 'uuidv4'
import { HTMLSelect, Label, Spinner } from '@blueprintjs/core'
import FormSection, { FormSectionDescription } from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormTitle from '../Form/FormTitle'
import FormButton from '../Form/FormButton'
import FormField from '../Form/FormField'
import FormButtonBar from '../Form/FormButtonBar'
import { api, poll } from '../utilities'
import { generateOptions, ErrorLabel } from '../Form/_helpers'
import { Audit } from '../../types'
import number, { parse as parseNumber } from '../../utils/number-schema'

export const Select = styled(HTMLSelect)`
  margin-left: 5px;
`

export const TwoColumnSection = styled.div`
  display: flex;
  flex-direction: column;
  margin-top: 25px;
  width: 100%;
`

export const InputLabelRow = styled.div`
  display: flex;
  flex-direction: row;
  margin-bottom: 10px;
  width: 100%;
`
export const InputFieldRow = styled.div`
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  margin-bottom: 25px;
  width: 100%;
`

export const FlexField = styled(FormField)`
  flex-grow: 2;
  width: unset;
  padding-right: 60px;
`

export const InputLabel = styled(Label)`
  display: inline-block;
  flex-grow: 2;
  width: unset;
`

export const Action = styled.p`
  margin: 5px 0 0 0;
  width: 100%;
  color: #000088;
  &:hover {
    cursor: pointer;
  }
`

interface Props {
  audit: Audit
  isLoading?: boolean
  setIsLoading: (isLoading: boolean) => void
  updateAudit: () => void
  getStatus: () => Promise<Audit>
  electionId: string
}

interface ChoiceValues {
  id?: string
  name: string
  numVotes: string | number
}

interface ContestValues {
  name: string
  totalBallotsCast: string
  winners: string
  choices: ChoiceValues[]
}

interface EstimateSampleSizeValues {
  name: string
  randomSeed: string
  riskLimit: string
  contests: ContestValues[]
}

const contestsSchema = Yup.array()
  .required()
  .of(
    Yup.object().shape({
      name: Yup.string().required('Required'),
      winners: number()
        .typeError('Must be a number')
        .integer('Must be an integer')
        .min(0, 'Must be a positive number')
        .required('Required'),
      totalBallotsCast: number()
        .typeError('Must be a number')
        .integer('Must be an integer')
        .min(0, 'Must be a positive number')
        .test(
          'is-sufficient',
          'Must be greater than or equal to the sum of votes for each candidate/choice',
          function(value?: unknown) {
            const { choices } = this.parent
            const totalVoters = choices.reduce(
              (a: number, v: ChoiceValues) =>
                a + (parseNumber(v.numVotes) || 0),
              0
            )
            return parseNumber(value) >= totalVoters || this.createError()
          }
        )
        .required('Required'),
      choices: Yup.array()
        .required()
        .of(
          Yup.object().shape({
            name: Yup.string().required('Required'),
            numVotes: number()
              .typeError('Must be a number')
              .integer('Must be an integer')
              .min(0, 'Must be a positive number')
              .required('Required'),
          })
        ),
    })
  )

const schema = Yup.object().shape({
  name: Yup.string().required('Required'),
  randomSeed: Yup.string()
    .max(100, 'Must be 100 characters or fewer')
    .required('Required'),
  riskLimit: number()
    .typeError('Must be a number')
    .min(1, 'Must be greater than 0')
    .max(20, 'Must be less than 21')
    .required('Required'),
  contests: contestsSchema,
})

const EstimateSampleSize: React.FC<Props> = ({
  audit,
  isLoading,
  setIsLoading,
  updateAudit,
  getStatus,
  electionId,
}: Props) => {
  const canEstimateSampleSize = !audit.contests.length

  const handlePost = async (values: EstimateSampleSizeValues) => {
    const data = {
      name: values.name,
      randomSeed: values.randomSeed,
      riskLimit: parseNumber(values.riskLimit),
      contests: values.contests.map(contest => ({
        id: uuidv4(),
        name: contest.name,
        totalBallotsCast: parseNumber(contest.totalBallotsCast),
        winners: parseNumber(contest.winners),
        choices: contest.choices.map(choice => ({
          id: uuidv4(),
          name: choice.name,
          numVotes: parseNumber(choice.numVotes),
        })),
      })),
    }
    try {
      setIsLoading(true)
      await api(`/audit/basic`, {
        electionId,
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const condition = async () => {
        const { rounds } = await getStatus()
        return (
          !!rounds.length &&
          !!rounds[0].contests.length &&
          rounds[0].contests.every(c => !!c.sampleSizeOptions)
        )
      }
      const complete = () => {
        updateAudit()
        setIsLoading(false)
      }
      await poll(condition, complete, (err: Error) => toast.error(err.message))
    } catch (err) {
      toast.error(err.message)
    }
  }

  const contestValues = [
    {
      name: '',
      totalBallotsCast: '',
      winners: '1',
      choices: [
        {
          name: '',
          numVotes: '',
        },
        {
          name: '',
          numVotes: '',
        },
      ],
    },
  ]

  const initialValues = {
    randomSeed: audit.randomSeed || '',
    riskLimit: audit.riskLimit || '10',
    name: audit.name || '',
    contests: audit.contests.length ? audit.contests : contestValues,
  }

  return (
    <>
      <Formik
        initialValues={initialValues}
        validationSchema={schema}
        onSubmit={handlePost}
        enableReinitialize
        validateOnChange={false}
      >
        {({
          values,
          handleSubmit,
          setFieldValue,
        }: FormikProps<EstimateSampleSizeValues>) => (
          <Form data-testid="form-one">
            <FormWrapper title="Administer an Audit">
              <FormSection>
                {/* eslint-disable jsx-a11y/label-has-associated-control */}
                <label htmlFor="audit-name" id="audit-name-label">
                  Election Name
                  <Field
                    id="audit-name"
                    aria-labelledby="audit-name-label"
                    name="name"
                    disabled={audit.contests.length}
                    component={FormField}
                  />
                </label>
              </FormSection>
              <FieldArray
                name="contests"
                render={() => (
                  <>
                    {values.contests.map(
                      (contest: ContestValues, i: number) => (
                        /* eslint-disable react/no-array-index-key */
                        <React.Fragment key={i}>
                          {i > 0 && (
                            /* istanbul ignore next */
                            <FormSection>
                              <hr />
                            </FormSection>
                          )}
                          <FormSection
                            label={`Contest ${
                              /* istanbul ignore next */
                              values.contests.length > 1 ? i + 1 : ''
                            } Info`}
                            description="Enter the name of the contest that will drive the audit."
                          >
                            <label htmlFor={`contests[${i}].name`}>
                              Contest{' '}
                              {/* istanbul ignore next */
                              values.contests.length > 1 ? i + 1 : ''}{' '}
                              Name
                              <Field
                                id={`contests[${i}].name`}
                                name={`contests[${i}].name`}
                                disabled={!canEstimateSampleSize}
                                component={FormField}
                              />
                            </label>
                            <FormSectionDescription>
                              Enter the number of winners for the contest.
                            </FormSectionDescription>
                            <label htmlFor={`contests[${i}].winners`}>
                              Winners
                              <Field
                                id={`contests[${i}].winners`}
                                name={`contests[${i}].winners`}
                                disabled={!canEstimateSampleSize}
                                component={FormField}
                              />
                            </label>
                            {/*values.contests.length > 1 &&
                              !audit.contests.length && (
                                <Action
                                  onClick={() => contestsArrayHelpers.remove(i)}
                                >
                                  Remove Contest {i + 1}
                                </Action>
                              )*/}
                          </FormSection>
                          <FieldArray
                            name={`contests[${i}].choices`}
                            render={choicesArrayHelpers => (
                              <FormSection
                                label="Candidates/Choices & Vote Totals"
                                description="Enter the name of each candidate choice that appears on the ballot for this contest."
                              >
                                <TwoColumnSection>
                                  {contest.choices.map(
                                    (choice: ChoiceValues, j: number) => (
                                      /* eslint-disable react/no-array-index-key */
                                      <React.Fragment key={j}>
                                        <InputFieldRow>
                                          <InputLabel>
                                            Name of Candidate/Choice {j + 1}
                                            <Field
                                              name={`contests[${i}].choices[${j}].name`}
                                              disabled={!canEstimateSampleSize}
                                              component={FlexField}
                                            />
                                          </InputLabel>
                                          <InputLabel>
                                            Votes for Candidate/Choice {j + 1}
                                            <Field
                                              name={`contests[${i}].choices[${j}].numVotes`}
                                              disabled={!canEstimateSampleSize}
                                              component={FlexField}
                                            />
                                          </InputLabel>
                                          {contest.choices.length > 2 &&
                                            !audit.contests.length && (
                                              <Action
                                                onClick={() =>
                                                  choicesArrayHelpers.remove(j)
                                                }
                                              >
                                                Remove choice {j + 1}
                                              </Action>
                                            )}
                                        </InputFieldRow>
                                      </React.Fragment>
                                    )
                                  )}
                                  {!audit.contests.length && (
                                    <Action
                                      onClick={() =>
                                        choicesArrayHelpers.push({
                                          name: '',
                                          numVotes: 0,
                                        })
                                      }
                                    >
                                      Add a new candidate/choice
                                    </Action>
                                  )}
                                </TwoColumnSection>
                              </FormSection>
                            )}
                          />
                          <FormSection
                            label="Total Ballots Cast"
                            description="Enter the overall number of ballot cards cast in jurisdictions containing this contest."
                          >
                            <label htmlFor={`contests[${i}].totalBallotsCast`}>
                              Total Ballots for Contest{' '}
                              {/* istanbul ignore next */
                              values.contests.length > 1 ? i + 1 : ''}
                              <Field
                                id={`contests[${i}].totalBallotsCast`}
                                name={`contests[${i}].totalBallotsCast`}
                                disabled={!canEstimateSampleSize}
                                component={FormField}
                              />
                            </label>
                          </FormSection>
                        </React.Fragment>
                      )
                    )}
                    {/*<FormButtonBar>
                      {!audit.contests.length && (
                        <FormButton
                          type="button"
                          onClick={() =>
                            contestsArrayHelpers.push({ ...contestValues[0] })
                          }
                        >
                          Add another targeted contest
                        </FormButton>
                      )}
                    </FormButtonBar>*/}
                  </>
                )}
              />
              <FormTitle>Audit Settings</FormTitle>
              <FormSection label="Desired Risk Limit">
                <label htmlFor="risk-limit">
                  Set the risk for the audit as a percentage (e.g. &quot;5&quot;
                  = 5%)
                  <Field
                    id="risk-limit"
                    name="riskLimit"
                    disabled={!canEstimateSampleSize}
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
                    disabled={!canEstimateSampleSize}
                    component={FormField}
                  />
                </label>
              </FormSection>
            </FormWrapper>
            {isLoading && <Spinner />}
            {!audit.contests.length && !isLoading && (
              <FormButtonBar>
                <FormButton
                  type="submit"
                  intent="primary"
                  disabled={!canEstimateSampleSize}
                  onClick={handleSubmit}
                >
                  Estimate Sample Size
                </FormButton>
              </FormButtonBar>
            )}
          </Form>
        )}
      </Formik>
    </>
  )
}

export default React.memo(EstimateSampleSize)
