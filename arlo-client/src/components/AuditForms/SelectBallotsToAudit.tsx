/* eslint-disable no-null */

import React from 'react'
import { toast } from 'react-toastify'
import { Formik, FormikProps } from 'formik'
import FormSection, { FormSectionDescription } from '../Form/FormSection'
import FormWrapper from '../Form/FormWrapper'
import FormButton from '../Form/FormButton'
import FormButtonBar from '../Form/FormButtonBar'
import { Jurisdiction, Audit } from '../../types'
import { api } from '../utilities'
import { generateOptions } from '../Form/_helpers'

interface Props {
  audit: Audit
  isLoading: boolean
  setIsLoading: (isLoading: boolean) => void
  updateAudit: () => void
  getStatus: () => Promise<Audit>
}

interface SelectBallotsToAuditValues {
  auditBoards: number
  manifest: File | null
}

const SelectBallotsToAudit = (props: Props) => {
  const { audit, isLoading, setIsLoading, updateAudit, getStatus } = props
  const formTwoHasData = audit && audit.jurisdictions && audit.jurisdictions[0]
  const manifestUploaded =
    formTwoHasData &&
    audit.jurisdictions[0].ballotManifest &&
    audit.jurisdictions[0].ballotManifest.filename &&
    audit.jurisdictions[0].ballotManifest.numBallots &&
    audit.jurisdictions[0].ballotManifest.numBatches

  const formThreeHasData =
    manifestUploaded && audit.rounds && audit.rounds.length > 0

  const handlePost = async (values: SelectBallotsToAuditValues) => {
    const auditBoards = Array.from(Array(values.auditBoards).keys()).map(i => {
      return {
        id: `audit-board-${i + 1}`,
        members: [],
      }
    })

    try {
      // upload jurisdictions
      const data: Jurisdiction[] = [
        {
          id: 'jurisdiction-1',
          name: 'Jurisdiction 1',
          contests: [`contest-1`],
          auditBoards: auditBoards,
        },
      ]
      setIsLoading(true)
      await api('/audit/jurisdictions', {
        method: 'POST',
        body: JSON.stringify({ jurisdictions: data }),
        headers: {
          'Content-Type': 'application/json',
        },
      }).then(
        async success => {
          const newStatus = await getStatus()
          const jurisdictionID: string = newStatus.jurisdictions[0].id

          // upload form data
          if (!values.manifest) {
            updateAudit()
            return
          }
          const formData: FormData = new FormData()
          formData.append('manifest', values.manifest, values.manifest.name)
          await api(`/jurisdiction/${jurisdictionID}/manifest`, {
            method: 'POST',
            body: formData,
          })

          updateAudit()
        },
        error => {
          toast.error(error.message)
          return
        }
      )
    } catch (err) {
      toast.error(err.message)
    }
  }

  const deleteBallotManifest = async (e: any) => {
    e.preventDefault()
    try {
      const jurisdictionID: string = audit.jurisdictions[0].id
      await api(`/jurisdiction/${jurisdictionID}/manifest`, {
        method: 'DELETE',
      })
      updateAudit()
    } catch (err) {
      toast.error(err.message)
    }
  }

  const initialState: SelectBallotsToAuditValues = {
    auditBoards: formTwoHasData && audit.jurisdictions[0].auditBoards.length,
    manifest: null,
  }

  return (
    <Formik
      initialValues={initialState}
      onSubmit={handlePost}
      render={({
        handleBlur,
        handleChange,
        handleSubmit,
        values,
        setFieldValue,
      }: FormikProps<SelectBallotsToAuditValues>) => (
        <form onSubmit={handleSubmit} id="formTwo">
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
                value={values.auditBoards}
                onChange={handleChange}
                onBlur={handleBlur}
              >
                {generateOptions(5)}
              </select>
            </FormSection>
            <FormSection label="Ballot Manifest">
              {manifestUploaded && audit.jurisdictions[0].ballotManifest ? ( // duplicating effect of manifestUploaded for TS
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
                  {formThreeHasData && (
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
                    name="manifest"
                    onChange={e => {
                      setFieldValue(
                        'manifest',
                        (e.currentTarget.files && e.currentTarget.files[0]) ||
                          null
                      )
                    }}
                    onBlur={handleBlur}
                  />
                </React.Fragment>
              )}
            </FormSection>
          </FormWrapper>
          {!formThreeHasData && isLoading && <p>Loading...</p>}
          {!formThreeHasData && !isLoading && (
            <FormButtonBar>
              <FormButton type="submit" onClick={handleSubmit}>
                Select Ballots To Audit
              </FormButton>
            </FormButtonBar>
          )}
        </form>
      )}
    />
  )
}

export default React.memo(SelectBallotsToAudit)
