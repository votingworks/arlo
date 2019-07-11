import React, { useState } from 'react'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import FormSection from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormTitle from '../Form/FormTitle'
import FormButton from '../Form/FormButton'
import FormField from '../Form/FormField'
import FormButtonBar from '../Form/FormButtonBar'
import { Audit } from '../../types'
import { api } from '../utilities'

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
  formOneHasData?: any
  audit?: any
  generateOptions?: any
  isLoading?: any
  submitFormOne?: any
  setIsLoading: (isLoading: boolean) => void
  updateAudit: () => void
}

const EstimateSampleSize = ({
  formOneHasData,
  audit,
  generateOptions,
  isLoading,
  setIsLoading,
  updateAudit,
}: Props) => {
  const [canEstimateSampleSize, setCanEstimateSampleSize] = useState(true)

  const submitFormOne = async (e: any) => {
    e.preventDefault()
    setCanEstimateSampleSize(false)
    const formData = new FormData(document.getElementById(
      'formOne'
    ) as HTMLFormElement)
    const data: Audit = {
      name: 'Election',
      randomSeed: Number(formData.get('randomSeed')),
      riskLimit: Number(formData.get('desiredRiskLimit')),
      contests: [
        {
          id: 'contest-1',
          name: formData.get('name') as string,
          totalBallotsCast: Number(formData.get('totalBallotsCast')),
          choices: [
            {
              id: 'candidate-1',
              name: formData.get('candidateOneName') as string,
              numVotes: Number(formData.get('candidateOneVotes')),
            },
            {
              id: 'candidate-2',
              name: formData.get('candidateTwoName') as string,
              numVotes: Number(formData.get('candidateTwoVotes')),
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

  return (
    <form id="formOne">
      <FormWrapper title="Contest Information">
        <FormSection
          label="Contest Name"
          description="Enter the name of the contest that will drive the audit."
        >
          <FormField
            name="name"
            defaultValue={formOneHasData && audit.contests[0].name}
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
              <InputLabelRight>Votes for Candidate/Choice 1</InputLabelRight>
            </InputLabelRow>
            <InputFieldRow>
              <FormField
                name="candidateOneName"
                defaultValue={
                  formOneHasData && audit.contests[0].choices[0].name
                }
                disabled={!canEstimateSampleSize}
              />
              <FieldRight
                type="number"
                name="candidateOneVotes"
                defaultValue={
                  formOneHasData && audit.contests[0].choices[0].numVotes
                }
                disabled={!canEstimateSampleSize}
              />
            </InputFieldRow>
            <InputLabelRow>
              <InputLabel>Name of Candidate/Choice 2</InputLabel>
              <InputLabelRight>Votes for Candidate/Choice 2</InputLabelRight>
            </InputLabelRow>
            <InputFieldRow>
              <FormField
                name="candidateTwoName"
                defaultValue={
                  formOneHasData && audit.contests[0].choices[1].name
                }
                disabled={!canEstimateSampleSize}
              />
              <FieldRight
                type="number"
                name="candidateTwoVotes"
                defaultValue={
                  formOneHasData && audit.contests[0].choices[1].numVotes
                }
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
            defaultValue={formOneHasData && audit.contests[0].totalBallotsCast}
            disabled={!canEstimateSampleSize}
          />
        </FormSection>
        <FormTitle>Audit Settings</FormTitle>
        <FormSection
          label="Desired Risk Limit"
          description='Set the risk for the audit as as percentage (e.g. "5" = 5%'
        >
          <select
            name="desiredRiskLimit"
            defaultValue={formOneHasData && audit.riskLimit}
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
            defaultValue={formOneHasData && audit.randomSeed}
            name="randomSeed"
            disabled={!canEstimateSampleSize}
          />
        </FormSection>
      </FormWrapper>
      {!formOneHasData && isLoading && <p>Loading...</p>}
      {!formOneHasData && !isLoading && (
        <FormButtonBar>
          <FormButton disabled={!canEstimateSampleSize} onClick={submitFormOne}>
            Estimate Sample Size
          </FormButton>
        </FormButtonBar>
      )}
    </form>
  )
}

export default React.memo(EstimateSampleSize)
