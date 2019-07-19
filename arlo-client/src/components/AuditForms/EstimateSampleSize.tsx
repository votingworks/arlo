import React, { useState, useRef } from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import { Formik, FormikProps } from 'formik'
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
  margin-bottom: 25px;
  width: 100%;
`

const FieldRight = styled(FormField)`
  margin-left: 50px;
`

const InputLabel = styled.label`
  display: inline-block;
`

const InputLabelRight = styled.label`
  margin-left: 75px;
`

interface Props {
  audit?: any
  isLoading?: any
  setIsLoading: (isLoading: boolean) => void
  updateAudit: () => void
}

interface ContestValues {
  name: string
  totalBallotsCast: number
  candidateOneName: string
  candidateTwoName: string
  candidateOneVotes: number
  candidateTwoVotes: number
}

interface EstimateSampleSizeValues {
  randomSeed: number
  riskLimit: number
  contests?: ContestValues[]
}

const schema = Yup.object().shape({
  randomSeed: Yup.number()
    .min(1, 'Must be at least 1')
    .max(99999999999999999999, 'Cannot exceed 20 digits')
    .required('Required'),
  riskLimit: Yup.number()
    .min(1, 'Must be greater than 0')
    .max(20, 'Must be less than 21')
    .required('Required'),
})

const contestsSchema = Yup.array()
  .required()
  .of(
    Yup.object().shape({
      name: Yup.string()
        .min(2, 'Name must be longer than 2 characters')
        .max(50, 'Name must be shorter than 50 characters')
        .required('Required'),
      totalBallotsCast: Yup.number().required('Required'),
      candidateOneName: Yup.string()
        .min(2, 'Name must be longer than 2 characters')
        .max(50, 'Name must be shorter than 50 characters')
        .required('Required'),
      candidateTwoName: Yup.string()
        .min(2, 'Name must be longer than 2 characters')
        .max(50, 'Name must be shorter than 50 characters')
        .required('Required'),
      candidateOneVotes: Yup.number().required('Required'),
      candidateTwoVotes: Yup.number().required('Required'),
    })
  )

const EstimateSampleSize = ({
  audit,
  isLoading,
  setIsLoading,
  updateAudit,
}: Props) => {
  const [canEstimateSampleSize, setCanEstimateSampleSize] = useState(true)

  const handlePost = async (values: EstimateSampleSizeValues) => {
    contestForms.current.forEach((form: any) => form.handleSubmit())
    setCanEstimateSampleSize(false)
    const data = {
      // incomplete Audit
      name: 'Election', // hardcoded to 'Election'?
      randomSeed: Number(values.randomSeed),
      riskLimit: Number(values.riskLimit),
      contests: contests.current.map(contest => ({
        id: uuidv4(),
        name: contest.name,
        totalBallotsCast: Number(contest.totalBallotsCast),
        choices: [
          {
            id: 'candidate-1',
            name: contest.candidateOneName,
            numVotes: Number(contest.candidateOneVotes),
          },
          {
            id: 'candidate-2',
            name: contest.candidateTwoName,
            numVotes: Number(contest.candidateTwoVotes),
          },
        ],
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
      setCanEstimateSampleSize(true)
    } finally {
      setIsLoading(false)
    }
  }

  const [numContests, setNumContests] = useState<number>(
    audit.contests.length || 1
  )
  const addContest = () => {
    setNumContests(numContests + 1)
  }
  const contests = useRef<ContestValues[]>([])
  //const contestForms = useRef<React.RefObject<HTMLInputElement>[]>([])
  const contestForms = useRef([])

  const initialValues = {
    randomSeed: audit.randomSeed || '',
    riskLimit: audit.riskLimit || 1,
  }

  const contestValues = Array.from(Array(numContests).keys()).map(i => {
    const {
      name = '',
      totalBallotsCast = '',
      candidateOneName = '',
      candidateTwoName = '',
      candidateOneVotes = '',
      candidateTwoVotes = '',
    } = audit.contests[i] || {}
    return {
      name,
      totalBallotsCast,
      candidateOneName,
      candidateTwoName,
      candidateOneVotes,
      candidateTwoVotes,
    }
  })

  return (
    <>
      {Array.from(Array(numContests).keys()).map(i => {
        return (
          <Formik
            key={i}
            ref={contestForms.current[i]}
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
            }: FormikProps<ContestValues>) => (
              <form id="formOne">
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
            )}
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
      />
    </>
  )
}

export default React.memo(EstimateSampleSize)
