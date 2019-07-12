import React from 'react'
import FormSection, { FormSectionDescription } from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormButton from '../Form/FormButton'
import FormButtonBar from '../Form/FormButtonBar'

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
      <FormWrapper>
        {/* <Section>
            <SectionLabel>Estimated Sample Size</SectionLabel>
            <SectionDetail>
                Choose the initial sample size you would like to use for Round 1 of the audit from the options below.
                <div><input name="sampleSize" type="radio" value="223" onChange={e => this.inputChange(e)} /><InputLabel>223 samples (80% chance of reaching risk limit in one round)</InputLabel></div>
                <div><input name="sampleSize" type="radio" value="456" onChange={e => this.inputChange(e)} /><InputLabel>456 samples (90% chance of reaching risk limit in one round)</InputLabel></div>
            </SectionDetail>
        </Section> */}
        <FormSection
          label="Number of Audit Boards"
          description="Set the number of audit boards you with to use."
        >
          <select
            id="auditBoards"
            name="auditBoards"
            defaultValue={
              formTwoHasData && audit.jurisdictions[0].auditBoards.length
            }
          >
            {generateOptions(5)}
          </select>
        </FormSection>
        <FormSection label="Ballot Manifest">
          {manifestUploaded ? (
            <React.Fragment>
              <FormSectionDescription>
                <b>Filename:</b>{' '}
                {audit.jurisdictions[0].ballotManifest.filename}
              </FormSectionDescription>
              <FormSectionDescription>
                <b>Ballots:</b>{' '}
                {audit.jurisdictions[0].ballotManifest.numBallots}
              </FormSectionDescription>
              <FormSectionDescription>
                <b>Batches:</b>{' '}
                {audit.jurisdictions[0].ballotManifest.numBatches}
              </FormSectionDescription>
              {!formThreeHasData && (
                <FormButton onClick={deleteBallotManifest}>
                  Delete File
                </FormButton>
              )}
            </React.Fragment>
          ) : (
            <React.Fragment>
              <FormSectionDescription>
                Click &quot;Browse&quot; to choose the appropriate Ballot
                Manifest file from your computer
              </FormSectionDescription>
              <input
                type="file"
                accept=".csv"
                onChange={fileInputChange}
              ></input>
            </React.Fragment>
          )}
        </FormSection>
      </FormWrapper>
      {!formThreeHasData && isLoading && <p>Loading...</p>}
      {!formThreeHasData && !isLoading && (
        <FormButtonBar>
          <FormButton onClick={submitFormTwo}>
            Select Ballots To Audit
          </FormButton>
        </FormButtonBar>
      )}
    </form>
  ) : (
    <div></div>
  )
}

export default React.memo(SelectBallotsToAudit)
