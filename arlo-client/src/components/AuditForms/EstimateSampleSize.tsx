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
import FormSection from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormTitle from '../Form/FormTitle'
import FormButton from '../Form/FormButton'
import FormField from '../Form/FormField'
import FormButtonBar from '../Form/FormButtonBar'
// import { Audit } from '../../types'
import { api } from '../utilities'
import { generateOptions, ErrorLabel } from '../Form/_helpers'

const TwoColumnSection = styled.div`
  display: block;
  margin-top: 25px;
  width: 100%;
  font-size: 0.4em;
`

const InputLabelRow = styled.div`
  display: flex;
  flex-direction: row;
  margin-bottom: 10px;
  width: 100%;
`
const InputFieldRow = styled.div`
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  margin-bottom: 25px;
  width: 100%;
`

const FieldLeft = styled(FormField)`
  flex-grow: 2;
  width: unset;
`

const FieldRight = styled(FieldLeft)`
  margin-left: 50px;
`

const InputLabel = styled.label`
  display: inline-block;
`

const InputLabelRight = styled.label`
  margin-left: 75px;
`

const Action = styled.p`
  margin: 5px 0 0 0;
  width: 100%;
  color: #000088;
  font-size: 14px;
  &:hover {
    cursor: pointer;
  }
`

interface Props {
  audit?: any
  isLoading?: any
  setIsLoading: (isLoading: boolean) => void
  updateAudit: () => void
}

interface ChoiceValues {
  id: number
  name: string
  numVotes: number
}

interface ContestValues {
  name?: string
  totalBallotsCast?: number
  choices: ChoiceValues[]
}

interface EstimateSampleSizeValues {
  name: string
  randomSeed: number
  riskLimit: number
  contests: ContestValues[]
}

const contestsSchema = Yup.array()
  .required()
  .of(
    Yup.object().shape({
      name: Yup.string()
        .min(2, 'Name must be longer than 2 characters')
        .max(50, 'Name must be shorter than 50 characters')
        .required('Required'),
      totalBallotsCast: Yup.number().required('Required'),
      choices: Yup.array()
        .required()
        .of(
          Yup.object().shape({
            name: Yup.string()
              .required('Required')
              .min(2, 'Name must be longer than 2 characters')
              .max(50, 'Name must be shorter than 50 characters'),
            numVotes: Yup.number().required('Required'),
          })
        ),
    })
  )

const schema = Yup.object().shape({
  name: Yup.string().required('Required'),
  randomSeed: Yup.number()
    .min(1, 'Must be at least 1')
    .max(99999999999999999999, 'Cannot exceed 20 digits')
    .required('Required'),
  riskLimit: Yup.number()
    .min(1, 'Must be greater than 0')
    .max(20, 'Must be less than 21')
    .required('Required'),
  contests: contestsSchema,
})

const EstimateSampleSize = ({
  audit,
  isLoading,
  setIsLoading,
  updateAudit,
}: Props) => {
  const canEstimateSampleSize = !audit.contests.length

  const handlePost = async (values: EstimateSampleSizeValues) => {
    const data = {
      // incomplete Audit
      name: values.name,
      randomSeed: Number(values.randomSeed),
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
    riskLimit: audit.riskLimit || 1,
    name: audit.name || '',
    contests: audit.contests.length ? audit.contests : contestValues,
  }

  return (
    <>
      <h1>Audit Setup</h1>
      <Formik
        initialValues={initialValues}
        validationSchema={schema}
        onSubmit={handlePost}
        enableReinitialize
      >
        {({ values, handleSubmit }: FormikProps<EstimateSampleSizeValues>) => (
          <Form>
            <FormWrapper>
              <FormSection label="Audit Name">
                <Field name="name" component={FormField} />
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
                            <FormSection>
                              <hr />
                            </FormSection>
                          )}
                          <FormSection
                            label={`Contest ${
                              values.contests.length > 1 ? i + 1 : ''
                            } Name`}
                            description="Enter the name of the contest that will drive the audit."
                          >
                            <Field
                              name={`contests[${i}].name`}
                              disabled={!canEstimateSampleSize}
                              component={FormField}
                            />
                            {values.contests.length > 1 &&
                              !audit.jurisdictions.length && (
                                <Action
                                  onClick={() => contestsArrayHelpers.remove(i)}
                                >
                                  Remove Contest {i + 1}
                                </Action>
                              )}
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
                                          />
                                          <Field
                                            name={`contests[${i}].choices[${j}].numVotes`}
                                            type="number"
                                            disabled={!canEstimateSampleSize}
                                            component={FieldRight}
                                          />
                                          {contest.choices.length > 2 &&
                                            !audit.jurisdictions.length && (
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
                                  {!audit.jurisdictions.length && (
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
                            <Field
                              type="number"
                              name={`contests[${i}].totalBallotsCast`}
                              disabled={!canEstimateSampleSize}
                              component={FormField}
                            />
                          </FormSection>
                        </React.Fragment>
                      )
                    )}
                    <FormButtonBar>
                      {!audit.jurisdictions.length && (
                        <FormButton
                          type="button"
                          onClick={() =>
                            contestsArrayHelpers.push({ ...contestValues[0] })
                          }
                        >
                          Add another targeted contest
                        </FormButton>
                      )}
                    </FormButtonBar>
                  </>
                )}
              />
              <FormTitle>Audit Settings</FormTitle>
              <FormSection
                label="Desired Risk Limit"
                description='Set the risk for the audit as as percentage (e.g. "5" = 5%'
              >
                <Field
                  name="riskLimit"
                  disabled={!canEstimateSampleSize}
                  component="select"
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
                  type="number"
                  name="randomSeed"
                  disabled={!canEstimateSampleSize}
                  component={FormField}
                />
              </FormSection>
            </FormWrapper>
            {!audit.contests.length && isLoading && <p>Loading...</p>}
            {!audit.contests.length && !isLoading && (
              <FormButtonBar>
                <FormButton
                  type="submit"
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

      {/** old code
      {Array.from(Array(numContests).keys()).map(i => {
        return (
          <Formik
            key={i}
            initialValues={contestValues[i]}
            validationSchema={contestsSchema}
            onSubmit={values => {
              contests.current.push(values)
            }}
            enableReinitialize
            render={({
              values,
              errors,
              touched,
              handleChange,
              handleBlur,
              submitForm,
              handleSubmit,
            }: FormikProps<ContestValues>) => {
              contestForms.current[i] = submitForm
              return (
                <form onSubmit={handleSubmit}>
                  <FormWrapper title="Contest Information">
                    <React.Fragment key={i}>
                      {i > 0 && (
                        <FormSection>
                          <hr />
                        </FormSection>
                      )}
                      <FormSection
                        label={`Contest ${numContests > 1 ? i + 1 : ''} Name`}
                        description="Enter the name of the contest that will drive the audit."
                      >
                        <FormField
                          name="name"
                          value={values.name}
                          onChange={handleChange}
                          onBlur={handleBlur}
                          disabled={!canEstimateSampleSize}
                          error={errors.name}
                          touched={touched.name}
                        />
                      </FormSection>
                      <FormSection
                        label="Candidates/Choices & Vote Totals"
                        description="Enter the name of each candidate choice that appears on the ballot for this contest."
                      >
                        <TwoColumnSection>
                          <InputLabelRow>
                            <InputLabel>Name of Candidate/Choice 1</InputLabel>
                            <InputLabelRight>
                              Votes for Candidate/Choice 1
                            </InputLabelRight>
                          </InputLabelRow>
                          <InputFieldRow>
                            <FormField
                              name="candidateOneName"
                              value={values.candidateOneName}
                              onChange={handleChange}
                              onBlur={handleBlur}
                              disabled={!canEstimateSampleSize}
                              error={errors.candidateOneName}
                              touched={touched.candidateOneName}
                            />
                            <FieldRight
                              type="number"
                              name="candidateOneVotes"
                              onChange={handleChange}
                              onBlur={handleBlur}
                              value={values.candidateOneVotes}
                              disabled={!canEstimateSampleSize}
                              error={errors.candidateOneVotes}
                              touched={touched.candidateOneVotes}
                            />
                          </InputFieldRow>
                          <InputLabelRow>
                            <InputLabel>Name of Candidate/Choice 2</InputLabel>
                            <InputLabelRight>
                              Votes for Candidate/Choice 2
                            </InputLabelRight>
                          </InputLabelRow>
                          <InputFieldRow>
                            <FormField
                              name="candidateTwoName"
                              onChange={handleChange}
                              onBlur={handleBlur}
                              value={values.candidateTwoName}
                              disabled={!canEstimateSampleSize}
                              error={errors.candidateTwoName}
                              touched={touched.candidateTwoName}
                            />
                            <FieldRight
                              type="number"
                              name="candidateTwoVotes"
                              onChange={handleChange}
                              onBlur={handleBlur}
                              value={values.candidateTwoVotes}
                              disabled={!canEstimateSampleSize}
                              error={errors.candidateTwoVotes}
                              touched={touched.candidateTwoVotes}
                            />
                          </InputFieldRow>
                        </TwoColumnSection>
                      </FormSection>

                      <FormSection
                        label="Total Ballots Cast"
                        description="Enter the overall number of ballot cards cast in jurisdictions containing this contest."
                      >
                        <FormField
                          type="number"
                          name="totalBallotsCast"
                          onChange={handleChange}
                          onBlur={handleBlur}
                          value={values.totalBallotsCast}
                          disabled={!canEstimateSampleSize}
                          error={errors.totalBallotsCast}
                          touched={
                            touched.totalBallotsCast &&
                            touched.candidateOneVotes &&
                            touched.candidateTwoVotes
                          }
                        />
                      </FormSection>
                    </React.Fragment>
                  </FormWrapper>
                </form>
              )
            }}
          />
        )
      })}
      <Formik
        initialValues={initialValues}
        validationSchema={schema}
        onSubmit={handlePost}
        enableReinitialize
        render={({
          values,
          errors,
          touched,
          handleChange,
          handleBlur,
          handleSubmit,
        }: FormikProps<EstimateSampleSizeValues>) => (
          <form>
            <FormWrapper>
              <FormTitle>Audit Settings</FormTitle>
              <FormSection
                label="Desired Risk Limit"
                description='Set the risk for the audit as as percentage (e.g. "5" = 5%'
              >
                <select
                  name="riskLimit"
                  onChange={handleChange}
                  onBlur={handleBlur}
                  value={values.riskLimit}
                  disabled={!canEstimateSampleSize}
                >
                  {generateOptions(20)}
                </select>
                {errors.riskLimit && touched.riskLimit && (
                  <ErrorLabel>{errors.riskLimit}</ErrorLabel>
                )}
              </FormSection>
              <FormSection
                label="Random Seed"
                description="Enter the random number to seed the pseudo-random number generator."
              >
                <FormField
                  type="number"
                  onChange={handleChange}
                  value={values.randomSeed}
                  onBlur={handleBlur}
                  name="randomSeed"
                  disabled={!canEstimateSampleSize}
                  error={errors.randomSeed}
                  touched={touched.randomSeed}
                />
              </FormSection>
            </FormWrapper>
            <FormButtonBar>
              <FormButton type="button" onClick={addContest}>
                Add another targeted contest
              </FormButton>
            </FormButtonBar>
            {!audit.contests.length && isLoading && <p>Loading...</p>}
            {!audit.contests.length && !isLoading && (
              <FormButtonBar>
                <FormButton
                  type="submit"
                  disabled={!canEstimateSampleSize}
                  onClick={handleSubmit}
                >
                  Estimate Sample Size
                </FormButton>
              </FormButtonBar>
            )}
          </form>
        )}
      />
      */}
    </>
  )
}

export default React.memo(EstimateSampleSize)
