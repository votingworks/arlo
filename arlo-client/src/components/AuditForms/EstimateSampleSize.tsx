import React from 'react'
import styled from 'styled-components'
import FormSection from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormTitle from '../Form/FormTitle'

const Section = styled.div`
  margin: 20px 0 20px 0;
`

const SectionDetail = styled.div`
  margin-top: 10px;
  font-size: 0.4em;
`

const SectionLabel = styled.div`
  font-size: 0.5em;
  font-weight: 700;
`

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

const Field = styled.input`
  width: 45%;
`

const FieldRight = styled.input`
  margin-left: 50px;
  width: 45%;
`

const InputLabel = styled.label`
  display: inline-block;
`

const InputLabelRight = styled.label`
  margin-left: 75px;
`

const ButtonBar = styled.div`
  margin: 50px 0 50px 0;
  text-align: center;
`

const Button = styled.button`
  margin: 0 auto;
  border-radius: 5px;
  background: rgb(211, 211, 211);
  width: 200px;
  height: 30px;
  color: #000000;
  font-size: 0.4em;
  font-weight: 700;
`

interface Props {
  formOneHasData?: any
  audit?: any
  generateOptions?: any
  isLoading?: any
  submitFormOne?: any
  canEstimateSampleSize: boolean
}

const EstimateSampleSize = (props: Props) => {
  const {
    formOneHasData,
    audit,
    generateOptions,
    isLoading,
    submitFormOne,
    canEstimateSampleSize,
  } = props
  return (
    <form id="formOne">
      <FormWrapper title="Contest Information">
        <Section>
          <SectionLabel>Contest Name</SectionLabel>
          <SectionDetail>
            Enter the name of the contest that will drive the audit.
          </SectionDetail>
          <Field
            name="name"
            defaultValue={formOneHasData && audit.contests[0].name}
            disabled={!canEstimateSampleSize}
          />
        </Section>
        <FormSection
          label="Contest Name"
          description="Enter the name of the contest that will drive the audit."
        >
          <Field
            name="name"
            defaultValue={formOneHasData && audit.contests[0].name}
            disabled={!canEstimateSampleSize}
          />
        </FormSection>

        <Section>
          <SectionLabel>Candidates/Choices & Vote Totals</SectionLabel>
          <SectionDetail>
            Enter the name of each candidate choice that appears on the ballot
            for this contest.
          </SectionDetail>
          <TwoColumnSection>
            <InputLabelRow>
              <InputLabel>Name of Candidate/Choice 1</InputLabel>
              <InputLabelRight>Votes for Candidate/Choice 1</InputLabelRight>
            </InputLabelRow>
            <InputFieldRow>
              <Field
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
              <Field
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
        </Section>
        <Section>
          <SectionLabel>Total Ballots Cast</SectionLabel>
          <SectionDetail>
            Enter the overall number of ballot cards cast in jurisdictoins
            containing this contest.
          </SectionDetail>
          <Field
            type="number"
            name="totalBallotsCast"
            defaultValue={formOneHasData && audit.contests[0].totalBallotsCast}
            disabled={!canEstimateSampleSize}
          />
        </Section>
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
          <Field
            type="number"
            defaultValue={formOneHasData && audit.randomSeed}
            name="randomSeed"
            disabled={!canEstimateSampleSize}
          />
        </FormSection>
      </FormWrapper>
      {!formOneHasData && isLoading && <p>Loading...</p>}
      {!formOneHasData && !isLoading && (
        <ButtonBar>
          <Button
            disabled={!canEstimateSampleSize}
            onClick={e => submitFormOne(e)}
          >
            Estimate Sample Size
          </Button>
        </ButtonBar>
      )}
    </form>
  )
}

export default React.memo(EstimateSampleSize)
