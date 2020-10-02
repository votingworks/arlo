/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState, useEffect } from 'react'
import { Formik, FormikProps, Field, ErrorMessage, useFormik } from 'formik'
import { useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import styled from 'styled-components'
import * as Yup from 'yup'
import { HTMLSelect, Spinner, FileInput } from '@blueprintjs/core'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { IValues } from './types'
import labelValueStates from './states'
import { ErrorLabel } from '../../../Atoms/Form/_helpers'
import FormSection, {
  FormSectionDescription,
} from '../../../Atoms/Form/FormSection'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import useAuditSettings from '../../useAuditSettings'
import useJurisdictionFile from './useJurisdictionFile'
import { IFileInfo } from '../../useJurisdictions'
import useContestFile from './useContestFile'

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

interface IProps {
  nextStage: ISidebarMenuItem
  locked: boolean
}

type IFileSubmitStatus = 'submit' | 'success' | 'failure' | null

const Participants: React.FC<IProps> = ({ locked, nextStage }: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [auditSettings, updateSettings] = useAuditSettings(electionId)
  const [jurisdictionFileStatus, setJurisdictionFileStatus] = useState<
    IFileSubmitStatus
  >(null)
  const [contestFileStatus, setContestFileStatus] = useState<IFileSubmitStatus>(
    null
  )
  useEffect(() => {
    // if both files are successfully submitted, go to the next screen
    /* istanbul ignore else */
    if (
      jurisdictionFileStatus === 'success' &&
      contestFileStatus === 'success'
    ) {
      /* istanbul ignore else */
      if (nextStage.activate) nextStage.activate()
      else toast.error('Wrong menuItems passed in: activate() is missing')
    }
  }, [jurisdictionFileStatus, contestFileStatus, nextStage])

  if (!auditSettings) return null // Still loading

  const submit = async (values: IValues) => {
    const responseOne = await updateSettings({ state: values.state })
    if (!responseOne) return
    setJurisdictionFileStatus('submit') // tell the jurisdiction file component to submit
    setContestFileStatus('submit') // tell the contest file component to submit
  }

  return (
    <Formik
      initialValues={{ state: auditSettings.state || '' }}
      validationSchema={Yup.object().shape({
        state: Yup.string().required('Required'),
      })}
      onSubmit={submit}
      enableReinitialize
    >
      {({ handleSubmit, setFieldValue, values }: FormikProps<IValues>) => (
        <form data-testid="form-one">
          <FormWrapper
            title={
              auditSettings.auditType === 'BALLOT_COMPARISON'
                ? 'Participants & Contests'
                : 'Participants'
            }
          >
            <label htmlFor="state">
              Choose your state from the options below
              <br />
              <Field
                component={Select}
                id="state"
                data-testid="state-field"
                name="state"
                onChange={(e: React.FormEvent<HTMLSelectElement>) =>
                  setFieldValue('state', e.currentTarget.value)
                }
                disabled={locked}
                value={values.state || ''}
                options={[{ value: '' }, ...labelValueStates]}
              />
            </label>
            <ErrorMessage name="state" component={ErrorLabel} />
            <JurisdictionFileForm
              electionId={electionId}
              setJurisdictionFileStatus={setJurisdictionFileStatus}
              jurisdictionFileStatus={jurisdictionFileStatus}
            />
            {auditSettings.auditType === 'BALLOT_COMPARISON' && (
              <ContestFileForm
                electionId={electionId}
                setContestFileStatus={setContestFileStatus}
                contestFileStatus={contestFileStatus}
              />
            )}
          </FormWrapper>
          {nextStage.state === 'processing' ? (
            <Spinner />
          ) : (
            <FormButtonBar>
              <FormButton type="submit" intent="primary" onClick={handleSubmit}>
                Save &amp; Next
              </FormButton>
            </FormButtonBar>
          )}
        </form>
      )}
    </Formik>
  )
}

const JurisdictionFileForm = ({
  electionId,
  jurisdictionFileStatus,
  setJurisdictionFileStatus,
}: {
  electionId: string
  jurisdictionFileStatus: IFileSubmitStatus
  setJurisdictionFileStatus: (status: IFileSubmitStatus) => void
}) => {
  const [jurisdictionFile, uploadJurisdictionFile] = useJurisdictionFile(
    electionId
  )
  return (
    <FileForm
      fileInfo={jurisdictionFile}
      fileStatus={jurisdictionFileStatus}
      setFileStatus={setJurisdictionFileStatus}
      uploadFile={uploadJurisdictionFile}
    />
  )
}

const ContestFileForm = ({
  electionId,
  contestFileStatus,
  setContestFileStatus,
}: {
  electionId: string
  contestFileStatus: IFileSubmitStatus
  setContestFileStatus: (status: IFileSubmitStatus) => void
}) => {
  const [contestFile, uploadContestFile] = useContestFile(electionId)
  return (
    <FileForm
      fileInfo={contestFile}
      fileStatus={contestFileStatus}
      setFileStatus={setContestFileStatus}
      uploadFile={uploadContestFile}
    />
  )
}

const FileForm = ({
  fileInfo,
  fileStatus,
  setFileStatus,
  uploadFile,
}: {
  fileInfo: IFileInfo | null
  fileStatus: IFileSubmitStatus
  setFileStatus: (status: IFileSubmitStatus) => void
  uploadFile: (csv: File) => Promise<boolean>
}) => {
  const [isEditing, setIsEditing] = useState<boolean>(true)
  useEffect(() => setIsEditing(!(fileInfo && fileInfo.file)), [fileInfo])
  const onSubmit = async (values: { csv: File | null }) => {
    /* istanbul ignore else */
    if (values.csv) {
      if (await uploadFile(values.csv)) {
        setIsEditing(false)
        setFileStatus('success')
      } else {
        setFileStatus('failure')
      }
    }
  }
  const {
    setFieldValue,
    values,
    errors,
    touched,
    handleBlur,
    handleSubmit,
    isSubmitting,
  } = useFormik<{
    csv: File | null
  }>({
    initialValues: { csv: null },
    validationSchema: Yup.object().shape({
      csv: Yup.mixed().required('You must upload a file'),
    }),
    onSubmit,
    enableReinitialize: true,
  })

  useEffect(() => {
    if (fileStatus === 'submit' && !isSubmitting) handleSubmit()
  }, [fileStatus, isSubmitting, handleSubmit])

  if (!fileInfo) return null // still loading
  const { file } = fileInfo
  return (
    <>
      {/* When one is already uploaded, this will be toggled to show its details, with a button to reveal the form to replace it */}
      <FormSection>
        <FormSectionDescription>
          Click &quot;Browse&quot; to choose the appropriate file from your
          computer. This file should be a comma-separated list of all the
          jurisdictions participating in the audit, plus email addresses for
          audit administrators in each participating jurisdiction.
          <br />
          <br />
          <a
            href="/sample_jurisdiction_filesheet.csv"
            target="_blank"
            rel="noopener noreferrer"
          >
            (Click here to view a sample file in the correct format.)
          </a>
        </FormSectionDescription>
      </FormSection>
      <FormSection>
        {isEditing || !file ? (
          <>
            <FileInput
              inputProps={{
                accept: '.csv',
                name: 'csv',
              }}
              onInputChange={e => {
                setFieldValue(
                  'csv',
                  (e.currentTarget.files && e.currentTarget.files[0]) ||
                    undefined
                )
              }}
              hasSelection={!!values.csv}
              text={values.csv ? values.csv.name : 'Select a CSV...'}
              onBlur={handleBlur}
            />
            {errors.csv && touched.csv && <ErrorLabel>{errors.csv}</ErrorLabel>}
          </>
        ) : (
          <>
            <span>{file.name} </span>
            <FormButton key="replace" onClick={() => setIsEditing(true)}>
              {/* needs a key in order to not trigger submit */}
              Replace File
            </FormButton>
          </>
        )}
      </FormSection>
    </>
  )
}

export default Participants
