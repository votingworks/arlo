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
import { HTMLSelect, Label } from '@blueprintjs/core'
import FormSection from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormTitle from '../Form/FormTitle'
import FormButton from '../Form/FormButton'
import FormField from '../Form/FormField'
import FormButtonBar from '../Form/FormButtonBar'
import { api } from '../utilities'
import { generateOptions, ErrorLabel } from '../Form/_helpers'
import { Audit } from '../../types'

export const TwoColumnSection = styled.div`
  display: block;
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

export const FieldLeft = styled(FormField)`
  flex-grow: 2;
  width: unset;
`

export const FieldRight = styled(FieldLeft)`
  margin-left: 50px;
`

export const InputLabel = styled(Label)`
  display: inline-block;
  flex-grow: 2;
  width: unset;
`

export const InputLabelRight = styled(InputLabel)`
  margin-left: 60px;
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
}

interface ChoiceValues {
  id?: string
  name: string
  numVotes: string | number
}

interface ContestValues {
  name: string
  totalBallotsCast: string
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
      totalBallotsCast: Yup.number()
        .typeError('Must be a number')
        .integer('Must be an integer')
        .min(0, 'Must be a positive number')
        .required('Required'),
      choices: Yup.array()
        .required()
        .of(
          Yup.object().shape({
            name: Yup.string().required('Required'),
            numVotes: Yup.number()
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
    .max(20, 'Must be 20 digits or less')
    .matches(/^\d+$/, 'Must be only numbers')
    .required('Required'),
  riskLimit: Yup.number()
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
}: Props) => {
  const canEstimateSampleSize = !audit.contests.length

  const handlePost = async (values: EstimateSampleSizeValues) => {
    const data = {
      name: values.name,
      randomSeed: values.randomSeed,
      riskLimit: Number(values.riskLimit),
      contests: values.contests.map(contest => ({
        id: uuidv4(),
        name: contest.name,
        totalBallotsCast: Number(contest.totalBallotsCast),
        choices: contest.choices.map(choice => ({
          id: uuidv4(),
          name: choice.name,
          numVotes: Number(choice.numVotes),
        })),
      })),
    }
    try {
      setIsLoading(true)
      await api(`/audit/basic`, {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      updateAudit()
    } catch (err) {
      toast.error(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const contestValues = [
    {
      name: '',
      totalBallotsCast: '',
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
      >
        {({
          values,
          handleSubmit,
          setFieldValue,
        }: FormikProps<EstimateSampleSizeValues>) => (
          <Form data-testid="form-one">
            <FormWrapper title="Contest Information">
              <FormSection label="Election Name">
                <Field
                  name="name"
                  data-testid="audit-name"
                  disabled={audit.contests.length}
                  component={FormField}
                />
              </FormSection>
              <FieldArray
                name="contests"
                render={contestsArrayHelpers => (
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
                            } Name`}
                            description="Enter the name of the contest that will drive the audit."
                          >
                            <Field
                              name={`contests[${i}].name`}
                              disabled={!canEstimateSampleSize}
                              component={FormField}
                              data-testid={`contest-${i + 1}-name`}
                            />
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
                                        <InputLabelRow>
                                          <InputLabel>
                                            Name of Candidate/Choice {j + 1}
                                          </InputLabel>
                                          <InputLabelRight>
                                            Votes for Candidate/Choice {j + 1}
                                          </InputLabelRight>
                                        </InputLabelRow>
                                        <InputFieldRow>
                                          <Field
                                            name={`contests[${i}].choices[${j}].name`}
                                            disabled={!canEstimateSampleSize}
                                            component={FieldLeft}
                                            data-testid={`contest-${i +
                                              1}-choice-${j + 1}-name`}
                                          />
                                          <Field
                                            name={`contests[${i}].choices[${j}].numVotes`}
                                            type="number"
                                            disabled={!canEstimateSampleSize}
                                            component={FieldRight}
                                            data-testid={`contest-${i +
                                              1}-choice-${j + 1}-votes`}
                                          />
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
                            <Field
                              type="number"
                              name={`contests[${i}].totalBallotsCast`}
                              disabled={!canEstimateSampleSize}
                              component={FormField}
                              data-testid={`contest-${i + 1}-total-ballots`}
                            />
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
              <FormSection
                label="Desired Risk Limit"
                description='Set the risk for the audit as a percentage (e.g. "5" = 5%)'
              >
                <Field
                  name="riskLimit"
                  disabled={!canEstimateSampleSize}
                  component={HTMLSelect}
                  data-testid="risk-limit"
                  defaultValue={values.riskLimit}
                  onChange={(e: React.FormEvent<HTMLSelectElement>) =>
                    setFieldValue('riskLimit', e.currentTarget.value)
                  }
                >
                  {generateOptions(20)}
                </Field>
                <ErrorMessage name="riskLimit" component={ErrorLabel} />
              </FormSection>
              <FormSection
                label="Random Seed"
                description="Enter the random number to seed the pseudo-random number generator."
              >
                <Field
                  type="text"
                  name="randomSeed"
                  disabled={!canEstimateSampleSize}
                  component={FormField}
                  data-testid="random-seed"
                />
              </FormSection>
            </FormWrapper>
            {!audit.contests.length && isLoading && <p>Loading...</p>}
            {!audit.contests.length && !isLoading && (
              <FormButtonBar>
                <FormButton
                  type="submit"
                  intent="primary"
                  data-testid="submit-form-one"
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
