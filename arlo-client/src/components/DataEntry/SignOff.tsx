import React from 'react'
import { Formik, Form } from 'formik'
import { H1 } from '@blueprintjs/core'
import FormSection from '../Atoms/Form/FormSection'
import { LabelText, NameField } from './Atoms'
import FormButton from '../Atoms/Form/FormButton'
import { IAuditBoard } from '../../types'

export interface IMemberNames {
  memberName1: string
  memberName2: string
}

export interface IProps {
  auditBoard: IAuditBoard
  submitSignoff: (memberNames: IMemberNames) => void
}

const SignOff = ({ auditBoard, submitSignoff }: IProps) => {
  return (
    <>
      <H1>{auditBoard.name}: Board Member Sign-off</H1>
      <p>
        Thank you for completing the ballots assigned to your Audit Board.
        Please sign your name below to confirm that all ballots were audited to
        the best of your ability and in accordance with the appropriate state
        statutes and guidelines.
      </p>
      <p>
        If another round of auditing is needed, you will be notified by election
        officials.
      </p>
      <Formik
        initialValues={{ memberName1: '', memberName2: '' }}
        onSubmit={submitSignoff}
        render={({ values, handleSubmit }) => (
          <Form>
            <FormSection
              label={`Audit Board Member: ${auditBoard.members[0].name}`}
            >
              <LabelText htmlFor="memberName1">Full Name</LabelText>
              <NameField name="memberName1" />
            </FormSection>
            <FormSection
              label={`Audit Board Member: ${auditBoard.members[1].name}`}
            >
              <LabelText htmlFor="memberName2">Full Name</LabelText>
              <NameField name="memberName2" />
            </FormSection>
            <FormButton
              intent="primary"
              type="button"
              onClick={handleSubmit}
              disabled={
                !(
                  values.memberName1 === auditBoard.members[0].name &&
                  values.memberName2 === auditBoard.members[1].name
                )
              }
            >
              Sign Off
            </FormButton>
          </Form>
        )}
      />
    </>
  )
}

export default SignOff
