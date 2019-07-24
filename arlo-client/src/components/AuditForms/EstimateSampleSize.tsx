import React from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import { Formik, FormikProps, FormikActions } from 'formik'
import * as Yup from 'yup'
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

interface EstimateSampleSizeValues {
  name: string
  randomSeed: number
  riskLimit: number
  totalBallotsCast: number
  candidateOneName: string
  candidateTwoName: string
  candidateOneVotes: number
  candidateTwoVotes: number
}

const defaultValues = {
  name: '',
  randomSeed: 0,
  riskLimit: 1,
  totalBallotsCast: 0,
  candidateOneName: '',
  candidateTwoName: '',
  candidateOneVotes: 0,
  candidateTwoVotes: 0,
}

const schema = Yup.object().shape({
  name: Yup.string()
    .min(2, 'Name must be longer than 2 characters')
    .max(50, 'Name must be shorter than 50 characters')
    .required('Required'),
  randomSeed: Yup.number()
    .min(1, 'Must be at least 1')
    .max(99999999999999999999, 'Cannot exceed 20 digits')
    .required('Required'),
  riskLimit: Yup.number()
    .min(1, 'Must be greater than 0')
    .max(20, 'Must be less than 21')
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

const EstimateSampleSize = ({
  audit,
  isLoading,
  setIsLoading,
  updateAudit,
}: Props) => {
  const canEstimateSampleSize = !audit.contests.length

  const handlePost = async (
    values: EstimateSampleSizeValues,
    actions: FormikActions<EstimateSampleSizeValues>
  ) => {
    const data = {
      // incomplete Audit
      name: values.name, // hardcoded to 'Election'?
      randomSeed: Number(values.randomSeed),
      riskLimit: Number(values.riskLimit),
      contests: [
        {
          id: 'contest-1',
          name: values.name,
          totalBallotsCast: Number(values.totalBallotsCast),
          choices: [
            {
              id: 'candidate-1',
              name: values.candidateOneName,
              numVotes: Number(values.candidateOneVotes),
            },
            {
              id: 'candidate-2',
              name: values.candidateTwoName,
              numVotes: Number(values.candidateTwoVotes),
            },
          ],
        },
      ],
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

  const cleanAudit = audit.contests.length
    ? {
        name: audit.contests[0].name,
        randomSeed: audit.randomSeed,
        riskLimit: audit.riskLimit,
        totalBallotsCast: audit.contests[0].totalBallotsCast,
        candidateOneName: audit.contests[0].choices[0].name,
        candidateTwoName: audit.contests[0].choices[1].name,
        candidateOneVotes: audit.contests[0].choices[0].numVotes,
        candidateTwoVotes: audit.contests[0].choices[1].numVotes,
      }
    : defaultValues // improve when refactor contest form component into dynamic generation

  return (
    <Formik
      initialValues={cleanAudit}
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
        <form id="formOne">
          <FormWrapper title="Contest Information">
            <FormSection
              label="Contest Name"
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
  )
}

export default React.memo(EstimateSampleSize)
