/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState, useEffect } from 'react'
import { Formik, FormikProps, Field, ErrorMessage } from 'formik'
import { useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import styled from 'styled-components'
import { HTMLSelect, Spinner, FileInput } from '@blueprintjs/core'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { IValues } from './types'
import labelValueStates from './states'
import schema from './schema'
import { ErrorLabel } from '../../../Atoms/Form/_helpers'
import FormSection, {
  FormSectionDescription,
} from '../../../Atoms/Form/FormSection'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import useAuditSettings from '../../useAuditSettings'
import useJurisdictionFile from './useJurisdictionFile'

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

interface IProps {
  nextStage: ISidebarMenuItem
  locked: boolean
}

const Participants: React.FC<IProps> = ({ locked, nextStage }: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [auditSettings, updateSettings] = useAuditSettings(electionId)
  const [jurisdictionFile, uploadJurisdictionFile] = useJurisdictionFile(
    electionId
  )
  const [isEditing, setIsEditing] = useState<boolean>(true)
  useEffect(() => setIsEditing(!(jurisdictionFile && jurisdictionFile.file)), [
    jurisdictionFile,
  ])
  if (!auditSettings || !jurisdictionFile) return null // Still loading
  const { file } = jurisdictionFile

  const submit = async (values: IValues) => {
    try {
      const responseOne = await updateSettings({ state: values.state })
      if (!responseOne) return
      /* istanbul ignore else */
      if (values.csv) {
        if (await uploadJurisdictionFile(values.csv)) {
          setIsEditing(false)
          /* istanbul ignore else */
          if (nextStage.activate) nextStage.activate()
          else
            throw new Error('Wrong menuItems passed in: activate() is missing')
        }
      }
    } catch (err) /* istanbul ignore next */ {
      // TODO migrate toasting to api to consolidate testing
      toast.error(err.message)
    }
  }
  return (
    <Formik
      initialValues={{ state: auditSettings.state || '', csv: null }}
      validationSchema={schema}
      onSubmit={submit}
      enableReinitialize
    >
      {({
        handleSubmit,
        setFieldValue,
        values,
        touched,
        errors,
        handleBlur,
      }: FormikProps<IValues>) => (
        <form data-testid="form-one">
          <FormWrapper title="Participants">
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
            {/* When one is already uploaded, this will be toggled to show its details, with a button to reveal the form to replace it */}
            <FormSection>
              <FormSectionDescription>
                Click &quot;Browse&quot; to choose the appropriate file from
                your computer. This file should be a comma-separated list of all
                the jurisdictions participating in the audit, plus email
                addresses for audit administrators in each participating
                jurisdiction.
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
                  {errors.csv && touched.csv && (
                    <ErrorLabel>{errors.csv}</ErrorLabel>
                  )}
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

export default Participants
