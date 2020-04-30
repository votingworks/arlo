import React from 'react'
import styled from 'styled-components'
import { H1, RadioGroup, Radio } from '@blueprintjs/core'
import { Formik, FormikProps, Form, Field, getIn } from 'formik'
import FormWrapper from '../Atoms/Form/FormWrapper'
import FormSection from '../Atoms/Form/FormSection'
import { IAuditBoardMember } from '../../types'
import FormButton from '../Atoms/Form/FormButton'

const LabelText = styled.span`
  display: block;
  margin: 5px 0;
`

const NameField = styled(Field)`
  margin-bottom: 20px;
`

interface IProps {
  boardName: string
  jurisdictionName: string
  submitMembers: (members: IAuditBoardMember[]) => void
}

const MemberForm: React.FC<IProps> = ({
  boardName,
  jurisdictionName,
  submitMembers,
}: IProps) => {
  return (
    <>
      <H1>Member Sign in for Audit Board: {boardName}</H1>
      <p>
        Enter the information below for each member of {jurisdictionName}{' '}
        {boardName} below, then click &quot;Next&quot; to proceed.
      </p>
      <FormWrapper>
        <Formik
          initialValues={[
            {
              name: '',
              affiliation: '',
            },
            {
              name: '',
              affiliation: '',
            },
          ]}
          onSubmit={submitMembers}
          render={({
            setFieldValue,
            values,
            handleSubmit,
          }: FormikProps<[IAuditBoardMember, IAuditBoardMember]>) => (
            <Form>
              {[0, 1].map(i => (
                <FormSection label="Audit Board Member" key={i}>
                  {/* eslint-disable jsx-a11y/label-has-associated-control */}
                  <label htmlFor={`[${i}]name`}>
                    <LabelText>Full Name</LabelText>
                    <NameField name={`[${i}]name`} id={`[${i}]name`} />
                  </label>
                  <div>
                    <LabelText>
                      Party Affiliation <i>(optional)</i>
                    </LabelText>
                    <RadioGroup
                      name={`[${i}]affiliation`}
                      onChange={e =>
                        setFieldValue(
                          `[${i}]affiliation`,
                          e.currentTarget.value
                        )
                      }
                      selectedValue={getIn(values, `[${i}]affiliation`)}
                    >
                      <Radio value="DEM">Democrat</Radio>
                      <Radio value="REP">Republican</Radio>
                      <Radio value="LIB">Libertarian</Radio>
                      <Radio value="IND">Independent/Unaffiliated</Radio>
                      <Radio value="OTH">Other</Radio>
                      <Radio value="">None</Radio>
                    </RadioGroup>
                  </div>
                </FormSection>
              ))}
              <FormButton intent="primary" type="button" onClick={handleSubmit}>
                Next
              </FormButton>
            </Form>
          )}
        />
      </FormWrapper>
    </>
  )
}

export default MemberForm
