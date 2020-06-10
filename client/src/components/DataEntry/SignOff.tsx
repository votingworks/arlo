import React from 'react'
import { Formik, Form } from 'formik'
import { H1 } from '@blueprintjs/core'
import FormSection from '../Atoms/Form/FormSection'
import { LabelText, NameField } from './Atoms'
import FormButton from '../Atoms/Form/FormButton'
import { IAuditBoard } from '../../types'

export interface IProps {
  auditBoard: IAuditBoard
  submitSignoff: (memberNames: string[]) => void
}

const SignOff = ({ auditBoard, submitSignoff }: IProps) => {
  return (
    <div>
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
        initialValues={auditBoard.members.map(() => '')}
        onSubmit={submitSignoff}
        render={({ values, handleSubmit }) => (
          <Form>
            {auditBoard.members.map((member, i) => (
              <FormSection
                key={member.name}
                label={`Audit Board Member: ${member.name}`}
              >
                <LabelText htmlFor={`[${i}]`}>Full Name</LabelText>
                <NameField name={`[${i}]`} />
              </FormSection>
            ))}
            <FormButton
              intent="primary"
              type="button"
              onClick={handleSubmit}
              disabled={auditBoard.members.some((_, i) => !values[i])}
            >
              Sign Off
            </FormButton>
          </Form>
        )}
      />
    </div>
  )
}

export default SignOff
