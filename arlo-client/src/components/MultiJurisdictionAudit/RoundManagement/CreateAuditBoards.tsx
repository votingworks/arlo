import React from 'react'
import { H4 } from '@blueprintjs/core'
import { Formik, Field } from 'formik'
import styled from 'styled-components'
import { generateOptions } from '../../Atoms/Form/_helpers'
import FormButton from '../../Atoms/Form/FormButton'
import Select from '../../Atoms/Form/Select'
import { IAuditBoard } from '../useAuditBoards'

const Wrapper = styled.div`
  margin: 20px 0;
`

const AuditBoardsInput = styled(Field)`
  margin-left: 0;
  width: 100px;
`

const BallotsToAudit = styled.p`
  margin: 15px 0;
  font-weight: 500;
`

interface IValues {
  numAuditBoards: number
}

interface IProps {
  createAuditBoards: (auditBoards: { name: string }[]) => Promise<boolean>
  auditBoards: IAuditBoard[]
  numBallots: number
  roundNum: number
}

const CreateAuditBoards = ({
  createAuditBoards,
  auditBoards,
  numBallots,
  roundNum,
}: IProps) => {
  const submit = async ({ numAuditBoards }: IValues) => {
    const boards = [...Array(numAuditBoards).keys()].map(i => ({
      name: `Audit Board #${i + 1}`,
    }))
    createAuditBoards(boards)
  }

  const disabled = auditBoards.length > 0

  return (
    <Wrapper>
      <H4>Number of Audit Boards</H4>
      <p>
        Select the appropriate number of audit boards based upon the personnel
        available and the number of ballots assigned to your jurisdiction for
        this round of the audit. You will have the opportunity to adjust the
        number of audit boards before the next round of the audit, if another
        round is required.
      </p>
      <Formik
        enableReinitialize
        initialValues={{ numAuditBoards: auditBoards.length || 1 }}
        onSubmit={submit}
      >
        {({ handleSubmit, setFieldValue }) => (
          <>
            <AuditBoardsInput
              component={Select}
              id="numAuditBoards"
              name="numAuditBoards"
              onChange={(e: React.FormEvent<HTMLSelectElement>) =>
                setFieldValue('numAuditBoards', Number(e.currentTarget.value))
              }
              disabled={disabled}
            >
              {generateOptions(15)}
            </AuditBoardsInput>
            <BallotsToAudit>
              {numBallots} Ballots to Audit in Round {roundNum}
            </BallotsToAudit>
            {!disabled && (
              <FormButton onClick={handleSubmit}>Save &amp; Next</FormButton>
            )}
          </>
        )}
      </Formik>
    </Wrapper>
  )
}

export default CreateAuditBoards
