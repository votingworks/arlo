import React from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import { Formik, FormikProps, Field, FieldArray, ErrorMessage } from 'formik'
import * as Yup from 'yup'
import uuidv4 from 'uuidv4'
import {
  HTMLSelect,
  Label,
  Spinner,
  RadioGroup,
  Radio,
} from '@blueprintjs/core'
import FormSection, { FormSectionDescription } from '../Atoms/Form/FormSection'
import FormWrapper from '../Atoms/Form/FormWrapper'
import H2Title from '../Atoms/H2Title'
import FormButton from '../Atoms/Form/FormButton'
import FormField from '../Atoms/Form/FormField'
import FormButtonBar from '../Atoms/Form/FormButtonBar'
import { api, poll } from '../utilities'
import { generateOptions, ErrorLabel } from '../Atoms/Form/_helpers'
import { IAudit, IErrorResponse } from '../../types'
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

interface IProps {
  audit: IAudit
  isLoading?: boolean
  setIsLoading: (isLoading: boolean) => void
  updateAudit: () => void
  getStatus: () => Promise<IAudit>
  electionId: string
}

interface IChoiceValues {
  id?: string
  name: string
  numVotes: string | number
}

interface IContestValues {
  name: string
  totalBallotsCast: string
  numWinners: string
  votesAllowed: string
  choices: IChoiceValues[]
}

interface IEstimateSampleSizeValues {
  name: string
  online: boolean
  randomSeed: string
  riskLimit: string
  contests: IContestValues[]
}

const contestsSchema = Yup.array()
  .required()
  .of(
    Yup.object().shape({
      name: Yup.string().required('Required'),
      numWinners: number()
        .typeError('Must be a number')
        .integer('Must be an integer')
        .min(0, 'Must be a positive number')
        .required('Required'),
      votesAllowed: number()
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
          function testTotalBallotsCast(value?: unknown) {
            const ballots = parseNumber(value)
            const { choices } = this.parent
            const totalVotes = choices.reduce(
              (sum: number, choiceValue: IChoiceValues) =>
                sum + (parseNumber(choiceValue.numVotes) || 0),
              0
            )
            const allowedVotesPerBallot: number = this.parent.votesAllowed
            const totalAllowedVotes = allowedVotesPerBallot * ballots
            return totalAllowedVotes >= totalVotes || this.createError()
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

const EstimateSampleSize: React.FC<IProps> = ({
  audit,
  isLoading,
  setIsLoading,
  updateAudit,
  getStatus,
  electionId,
}: IProps) => {
  const canEstimateSampleSize = !audit.contests.length

  const handlePost = async (values: IEstimateSampleSizeValues) => {
    const data = {
      name: values.name,
      online: values.online,
      randomSeed: values.randomSeed,
      riskLimit: parseNumber(values.riskLimit),
      contests: values.contests.map(contest => ({
        id: uuidv4(),
        name: contest.name,
        totalBallotsCast: parseNumber(contest.totalBallotsCast),
        numWinners: parseNumber(contest.numWinners),
        votesAllowed: parseNumber(contest.votesAllowed),
        choices: contest.choices.map(choice => ({
          id: uuidv4(),
          name: choice.name,
          numVotes: parseNumber(choice.numVotes),
        })),
      })),
    }
    setIsLoading(true)
    const response = await api<IErrorResponse>(
      `/election/${electionId}/audit/basic`,
      {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
    if (!response) {
      setIsLoading(false)
      return
    }

    const freezeResponse = await api<IErrorResponse>(
      `/election/${electionId}/audit/freeze`,
      {
        method: 'POST',
      }
    )
    if (!freezeResponse) {
      setIsLoading(false)
      return
    }

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
    poll(condition, complete, (err: Error) => toast.error(err.message))
  }

  const contestValues = [
    {
      name: '',
      totalBallotsCast: '',
      numWinners: '1',
      votesAllowed: '1',
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
    online: audit.online,
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
        }: FormikProps<IEstimateSampleSizeValues>) => (
          <form data-testid="form-one">
            <FormWrapper title="Administer an Audit">
              <FormSection>
                {/* eslint-disable jsx-a11y/label-has-associated-control */}
                <label htmlFor="election-name" id="election-name-label">
                  Election Name
                  <Field
                    id="election-name"
                    aria-labelledby="election-name-label"
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
                      (contest: IContestValues, i: number) => (
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
                            <label htmlFor={`contests[${i}].numWinners`}>
                              Winners
                              <Field
                                id={`contests[${i}].numWinners`}
                                name={`contests[${i}].numWinners`}
                                disabled={!canEstimateSampleSize}
                                component={FormField}
                              />
                            </label>
                            <FormSectionDescription>
                              Number of selections the voter can make in the
                              contest.
                            </FormSectionDescription>
                            <label htmlFor={`contests[${i}].votesAllowed`}>
                              Votes Allowed
                              <Field
                                id={`contests[${i}].votesAllowed`}
                                name={`contests[${i}].votesAllowed`}
                                disabled={!canEstimateSampleSize}
                                component={FormField}
                              />
                            </label>
                            {/* values.contests.length > 1 &&
                              !audit.contests.length && (
                                <Action
                                  onClick={() => contestsArrayHelpers.remove(i)}
                                >
                                  Remove Contest {i + 1}
                                </Action>
                              ) */}
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
                                    (choice: IChoiceValues, j: number) => (
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
                                          numVotes: '',
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
                    {/* <FormButtonBar>
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
                    </FormButtonBar> */}
                  </>
                )}
              />
              <H2Title>Audit Settings</H2Title>
              <FormSection>
                <RadioGroup
                  name="online"
                  onChange={e =>
                    setFieldValue('online', e.currentTarget.value === 'online')
                  }
                  selectedValue={values.online ? 'online' : 'offline'}
                  disabled={!canEstimateSampleSize}
                >
                  <Radio value="online">Online</Radio>
                  <Radio value="offline">Offline</Radio>
                </RadioGroup>
              </FormSection>
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
          </form>
        )}
      </Formik>
    </>
  )
}

export default React.memo(EstimateSampleSize)
