import React from 'react'
import { Formik, Field } from 'formik'
import styled from 'styled-components'
import { generateOptions } from '../Atoms/Form/_helpers'
import FormButton from '../Atoms/Form/FormButton'
import Select from '../Atoms/Form/Select'
import FormSection from '../Atoms/Form/FormSection'

const AuditBoardsInput = styled(Field)`
  margin-left: 0;
  width: 100px;
`
interface IValues {
  numAuditBoards: number
}

interface IProps {
  createAuditBoards: (auditBoards: { name: string }[]) => Promise<boolean>
}

const CreateAuditBoards: React.FC<IProps> = ({ createAuditBoards }) => {
  const submit = async ({ numAuditBoards }: IValues) => {
    const maxAuditBoardsIndexLength = numAuditBoards.toString().length
    const boards = [...Array(numAuditBoards).keys()].map(i => ({
      name: `Audit Board #${(i + 1)
        .toString()
        .padStart(maxAuditBoardsIndexLength, '0')}`,
    }))
    await createAuditBoards(boards)
  }

  return (
    <div>
      <p>
        Select the appropriate number of audit boards based upon the personnel
        available and the number of ballots assigned to your jurisdiction for
        this round of the audit. You will have the opportunity to adjust the
        number of audit boards before the next round of the audit, if another
        round is required.
      </p>
      <Formik initialValues={{ numAuditBoards: 1 }} onSubmit={submit}>
        {({ handleSubmit, setFieldValue, isSubmitting }) => (
          <>
            <FormSection>
              <AuditBoardsInput
                component={Select}
                id="numAuditBoards"
                data-testid="numAuditBoards"
                name="numAuditBoards"
                onChange={(e: React.FormEvent<HTMLSelectElement>) =>
                  setFieldValue('numAuditBoards', Number(e.currentTarget.value))
                }
                disabled={isSubmitting}
              >
                {generateOptions(200)}
              </AuditBoardsInput>
            </FormSection>
            <FormButton
              intent="primary"
              onClick={handleSubmit}
              loading={isSubmitting}
            >
              Save &amp; Next
            </FormButton>
          </>
        )}
      </Formik>
    </div>
  )
}

export default CreateAuditBoards
