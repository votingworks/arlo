import React from 'react'
import styled from 'styled-components'

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
const PageSection = styled.div`
  display: block;
  width: 50%;
  text-align: left;
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
  formOneHasData: any
  formTwoHasData: any
  formThreeHasData: any
  submitFormTwo: any
  audit: any
  isLoading: any
  deleteBallotManifest: any
  generateOptions: any
  fileInputChange: any
  manifestUploaded: any
}

const SelectBallotsToAudit = (props: Props) => {
  const {
    formOneHasData,
    formTwoHasData,
    formThreeHasData,
    submitFormTwo,
    audit,
    isLoading,
    deleteBallotManifest,
    generateOptions,
    fileInputChange,
    manifestUploaded,
  } = props

  return formOneHasData ? (
    <form onSubmit={submitFormTwo} id="formTwo">
      <PageSection>
        {/* <Section>
            <SectionLabel>Estimated Sample Size</SectionLabel>
            <SectionDetail>
                Choose the initial sample size you would like to use for Round 1 of the audit from the options below.
                <div><input name="sampleSize" type="radio" value="223" onChange={e => this.inputChange(e)} /><InputLabel>223 samples (80% chance of reaching risk limit in one round)</InputLabel></div>
                <div><input name="sampleSize" type="radio" value="456" onChange={e => this.inputChange(e)} /><InputLabel>456 samples (90% chance of reaching risk limit in one round)</InputLabel></div>
            </SectionDetail>
        </Section> */}
        <Section>
          <SectionLabel>Number of Audit Boards</SectionLabel>
          <SectionDetail>
            Set the number of audit boards you wish to use.
          </SectionDetail>
          <select
            id="auditBoards"
            name="auditBoards"
            defaultValue={
              formTwoHasData && audit.jurisdictions[0].auditBoards.length
            }
          >
            {generateOptions(5)}
          </select>
        </Section>
        <Section>
          <SectionLabel>Ballot Manifest</SectionLabel>
          {manifestUploaded ? (
            <React.Fragment>
              <SectionDetail>
                <b>Filename:</b>{' '}
                {audit.jurisdictions[0].ballotManifest.filename}
              </SectionDetail>
              <SectionDetail>
                <b>Ballots:</b>{' '}
                {audit.jurisdictions[0].ballotManifest.numBallots}
              </SectionDetail>
              <SectionDetail>
                <b>Batches:</b>{' '}
                {audit.jurisdictions[0].ballotManifest.numBatches}
              </SectionDetail>
              {!formThreeHasData && (
                <Button onClick={deleteBallotManifest}>Delete File</Button>
              )}
            </React.Fragment>
          ) : (
            <React.Fragment>
              <SectionDetail>
                Click &quot;Browse&quot; to choose the appropriate Ballot
                Manifest file from your computer
              </SectionDetail>
              <input
                type="file"
                accept=".csv"
                onChange={fileInputChange}
              ></input>
            </React.Fragment>
          )}
        </Section>
      </PageSection>
      {!formThreeHasData && isLoading && <p>Loading...</p>}
      {!formThreeHasData && !isLoading && (
        <ButtonBar>
          <Button onClick={submitFormTwo}>Select Ballots To Audit</Button>
        </ButtonBar>
      )}
    </form>
  ) : (
    <div></div>
  )
}

export default React.memo(SelectBallotsToAudit)
