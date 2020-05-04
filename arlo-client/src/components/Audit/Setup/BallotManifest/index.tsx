/* eslint-disable jsx-a11y/label-has-associated-control */
import React, { useState } from 'react'
import { Formik, FormikProps, Form } from 'formik'
import styled from 'styled-components'
import { HTMLSelect, FileInput, H4 } from '@blueprintjs/core'
import FormWrapper from '../../../Atoms/Form/FormWrapper'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import schema from './schema'
import { ErrorLabel } from '../../../Atoms/Form/_helpers'
import FormSection, {
  FormSectionDescription,
} from '../../../Atoms/Form/FormSection'
import { IFileInfo } from '../../useJurisdictions'

export const Select = styled(HTMLSelect)`
  margin-top: 5px;
`

interface IValues {
  csv: File | null
}

interface IProps {
  ballotManifest: IFileInfo
  uploadBallotManifest: (csv: File) => Promise<boolean>
}

const BallotManifest: React.FC<IProps> = ({
  ballotManifest,
  uploadBallotManifest,
}: IProps) => {
  const { file } = ballotManifest
  const [isEditing, setIsEditing] = useState<boolean>(!!file)

  return (
    <Formik
      initialValues={{ csv: null }}
      validationSchema={schema}
      onSubmit={async (values: IValues) => {
        if (values.csv) {
          if (await uploadBallotManifest(values.csv)) {
            setIsEditing(false)
          }
        }
      }}
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
              {isEditing ? (
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
                  <span>{file!.name}</span>
                  <FormButton onClick={() => setIsEditing(true)}>
                    Replace File
                  </FormButton>
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
