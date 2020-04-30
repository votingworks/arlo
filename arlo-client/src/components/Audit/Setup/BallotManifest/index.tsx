/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState, useEffect } from 'react'
import { Formik, FormikProps, Form } from 'formik'
import { useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import styled from 'styled-components'
import { HTMLSelect, FileInput, H4 } from '@blueprintjs/core'
import { IErrorResponse } from '../../../../types'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import schema from './schema'
import { ErrorLabel } from '../../../Atoms/Form/_helpers'
import FormSection, {
  FormSectionDescription,
} from '../../../Atoms/Form/FormSection'
import { api, checkAndToast } from '../../../utilities'
import { useAuthDataContext } from '../../../UserContext'
import { IJurisdictionsFileResponse } from '../../useSetupMenuItems/getJurisdictionFileStatus'

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

interface IValues {
  csv: File | null
}

const BallotManifest: React.FC<{}> = () => {
  const { electionId } = useParams()
  const { meta } = useAuthDataContext()
  const { jurisdictions } = meta!
  const [file, setFile] = useState<IJurisdictionsFileResponse>({
    file: null,
    processing: null,
  })
  useEffect(() => {
    try {
      ;(async () => {
        const fileResponse:
          | IJurisdictionsFileResponse
          | IErrorResponse = await api(
          `/election/${electionId}/jurisdiction/${jurisdictions[0].id}/ballot-manifest`
        )
        // checkAndToast left here for consistency and reference but not tested since it's vestigial
        /* istanbul ignore next */
        if (checkAndToast(fileResponse)) return
        setFile(fileResponse)
      })()
    } catch (err) /* istanbul ignore next */ {
      // TEST TODO
      toast.error(err.message)
    }
  }, [electionId, jurisdictions, setFile])
  const submit = async (values: IValues) => {
    try {
      /* istanbul ignore else */
      if (values.csv) {
        const formData: FormData = new FormData()
        formData.append('manifest', values.csv, values.csv.name)
        const errorResponse: IErrorResponse = await api(
          `/election/${electionId}/jurisdiction/${jurisdictions[0].id}/ballot-manifest`,
          {
            method: 'PUT',
            body: formData,
          }
        )
        if (checkAndToast(errorResponse)) return
      }
    } catch (err) /* istanbul ignore next */ {
      // TEST TODO
      toast.error(err.message)
    }
  }
  return (
    <Formik
      initialValues={{ csv: null }}
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
        <Form data-testid="form-one">
          <FormWrapper title="Audit Source Data">
            <H4>Ballot Manifest</H4>
            <FormSection>
              <FormSectionDescription>
                Click &quot;Browse&quot; to choose the appropriate Ballot
                Manifest file from your computer. This file should be a
                comma-separated list of all the ballot boxes/containers used to
                store ballots for this particular election, plus a count of how
                many ballot cards (individual pieces of paper) are stored in
                each container.
                <br />
                <br />
                <a
                  href={`${window.location.origin}/sample_ballot_manifest.csv`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  (Click here to view a sample file in the correct format.)
                </a>
              </FormSectionDescription>
            </FormSection>
            <FormSection>
              {file.file ? (
                <>
                  <span>{file.file.name} </span>
                  <FormButton
                    onClick={() => setFile({ file: null, processing: null })}
                  >
                    Replace File
                  </FormButton>
                </>
              ) : (
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
              )}
            </FormSection>
          </FormWrapper>
          <FormButtonBar>
            <FormButton type="submit" intent="primary" onClick={handleSubmit}>
              Upload File
            </FormButton>
          </FormButtonBar>
        </Form>
      )}
    </Formik>
  )
}

export default BallotManifest
