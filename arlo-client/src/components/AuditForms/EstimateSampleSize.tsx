import React, { useState } from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import { Formik, FormikProps, FormikActions } from 'formik'
import FormSection from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormTitle from '../Form/FormTitle'
import FormButton from '../Form/FormButton'
import FormField from '../Form/FormField'
import FormButtonBar from '../Form/FormButtonBar'
// import { Audit } from '../../types'
import { api } from '../utilities'
import { generateOptions } from '../Form/_helpers'

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

const EstimateSampleSize = ({
  audit,
  isLoading,
  setIsLoading,
  updateAudit,
}: Props) => {
  const [canEstimateSampleSize, setCanEstimateSampleSize] = useState(true)
  const formOneHasData = audit && audit.contests[0]

  const handlePost = async (
    values: EstimateSampleSizeValues,
    actions: FormikActions<EstimateSampleSizeValues>
  ) => {
    setCanEstimateSampleSize(false)
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
      setCanEstimateSampleSize(true)
    } finally {
      setIsLoading(false)
    }
  }

  const cleanAudit = formOneHasData
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
    : {
        name: '',
        randomSeed: 0,
        riskLimit: 0,
        totalBallotsCast: 0,
        candidateOneName: '',
        candidateTwoName: '',
        candidateOneVotes: 0,
        candidateTwoVotes: 0,
      } // improve when refactor contest form component into dynamic generation

  return (
    <Formik
      initialValues={cleanAudit}
      onSubmit={handlePost}
      render={({
        values,
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
                  />
                  <FieldRight
                    type="number"
                    name="candidateOneVotes"
                    onChange={handleChange}
                    onBlur={handleBlur}
                    value={values.candidateOneVotes}
                    disabled={!canEstimateSampleSize}
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
                  />
                  <FieldRight
                    type="number"
                    name="candidateTwoVotes"
                    onChange={handleChange}
                    onBlur={handleBlur}
                    value={values.candidateTwoVotes}
                    disabled={!canEstimateSampleSize}
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
              />
            </FormSection>
          </FormWrapper>
          {!formOneHasData && isLoading && <p>Loading...</p>}
          {!formOneHasData && !isLoading && (
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
