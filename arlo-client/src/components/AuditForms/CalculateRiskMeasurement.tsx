import React from 'react'
import styled from 'styled-components'

const Section = styled.div`
  margin: 20px 0 20px 0;
`

const SectionTitle = styled.div`
  margin: 40px 0 25px 0;
  text-align: center;
  font-size: 0.8em;
`
const SectionDetail = styled.div`
  margin-top: 10px;
  font-size: 0.4em;
`

const SectionLabel = styled.div`
  font-size: 0.5em;
  font-weight: 700;
`
const PageSection = styled.div`
  display: block;
  width: 50%;
  text-align: left;
`

const InputSection = styled.div`
  display: block;
  margin-top: 25px;
  width: 100%;
  font-size: 0.4em;
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

const InlineButton = styled.button`
  margin: 10px 0 30px 0;
  border-radius: 5px;
  background: rgb(211, 211, 211);
  width: 275px;
  height: 20px;
  color: 700;
  font-size: 0.4em;
  font-weight: 700;
`
const InlineInput = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  margin-bottom: 10px;
  width: 50%;
`

const SmallInlineButton = styled.button`
  margin: 10px 0 30px 0;
  border-radius: 5px;
  background: rgb(211, 211, 211);
  width: 170px;
  height: 20px;
  color: #000000;
  font-size: 0.4em;
  font-weight: 700;
`

interface Props {
  audit: any
  downloadBallotRetrievalList: any
  isLoading: any
  calculateRiskMeasurement: any
  downloadAuditReport: any
}

const CalculateRiskMeasurmeent = (props: Props) => {
  const {
    audit,
    downloadBallotRetrievalList,
    isLoading,
    calculateRiskMeasurement,
    downloadAuditReport,
  } = props
  if (!audit) {
    return <></>
  }
  return audit.rounds.map((v: any, i: number) => {
    const round: number = i + 1
    const contest: any = v.contests.length > 0 ? v.contests[0] : undefined
    let candidateOne = ''
    let candidateTwo = ''
    const showCalculateButton =
      i + 1 === audit.rounds.length &&
      contest &&
      contest.endMeasurements &&
      !contest.endMeasurements.isComplete
    /* eslint-disable react/no-array-index-key */
    return (
      <React.Fragment key={i}>
        <PageSection>
          <SectionTitle>Round {i + 1}</SectionTitle>

          <Section>
            <SectionLabel>
              Ballot Retrieval List{' '}
              {contest ? `${contest.sampleSize} Ballots` : ''}
            </SectionLabel>
            <InlineButton onClick={e => downloadBallotRetrievalList(round, e)}>
              Download Ballot Retrieval List for Round {i + 1}
            </InlineButton>
            <SectionLabel>Audited Results: Round {round}</SectionLabel>
            <SectionDetail>
              Enter the number of votes recorded for each candidate/choice in
              the audited ballots for Round {i + 1}
            </SectionDetail>
            <form>
              <InputSection>
                <InlineInput
                  onChange={(e: any) => (candidateOne = e.target.value)}
                >
                  <InputLabel>{audit.contests[0].choices[0].name}</InputLabel>
                  <Field />
                </InlineInput>
                <InlineInput
                  onChange={(e: any) => (candidateTwo = e.target.value)}
                >
                  <InputLabel>{audit.contests[0].choices[1].name}</InputLabel>
                  <Field />
                </InlineInput>
              </InputSection>
            </form>
          </Section>
          {isLoading && <p>Loading...</p>}
          {showCalculateButton && !isLoading && (
            <ButtonBar>
              <Button
                type="button"
                onClick={e =>
                  calculateRiskMeasurement(
                    {
                      id: round,
                      round: v,
                      candidateOne,
                      candidateTwo,
                      roundIndex: i,
                    },
                    e
                  )
                }
              >
                Calculate Risk Measurement
              </Button>
            </ButtonBar>
          )}
          {contest &&
            contest.endMeasurements.pvalue &&
            contest.endMeasurements.isComplete && (
              <Section>
                <SectionLabel>
                  Audit Status:{' '}
                  {contest.endMeasurements.isComplete
                    ? 'COMPLETE'
                    : 'INCOMPLETE'}
                </SectionLabel>
                <InputSection>
                  <InlineInput>
                    <InputLabel>Risk Limit: </InputLabel>
                    {audit.riskLimit}%
                  </InlineInput>
                  <InlineInput>
                    <InputLabel>P-value: </InputLabel>{' '}
                    {contest.endMeasurements.pvalue}
                  </InlineInput>
                </InputSection>
                {/* {Form 3} */}
                {contest.endMeasurements.isComplete && (
                  <SmallInlineButton
                    onClick={e => downloadAuditReport(i, v, e)}
                  >
                    Download Audit Report
                  </SmallInlineButton>
                )}
              </Section>
            )}
        </PageSection>
      </React.Fragment>
    )
  })
}

export default React.memo(CalculateRiskMeasurmeent)
