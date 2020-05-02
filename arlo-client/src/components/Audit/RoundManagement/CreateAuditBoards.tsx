import React from 'react'
import { H4 } from '@blueprintjs/core'
import { Formik, Field } from 'formik'
import styled from 'styled-components'
import { toast } from 'react-toastify'
import { IAuditBoard, IErrorResponse } from '../../../types'
import { generateOptions } from '../../Atoms/Form/_helpers'
import FormButton from '../../Atoms/Form/FormButton'
import Select from '../../Atoms/Form/Select'
import { api, checkAndToast } from '../../utilities'

const Wrapper = styled.div`
  margin: 20px 0;
`

const CreateAuditBoards = ({
  auditBoards,
  electionId,
  jurisdictionId,
  roundId,
  getAuditBoards,
}: {
  auditBoards: IAuditBoard[]
  electionId: string
  jurisdictionId: string
  roundId: string
  getAuditBoards: () => void
}) => {
  const submit = async ({
    auditBoards: auditBoardsCount,
  }: {
    auditBoards: number
  }) => {
    try {
      const body = JSON.stringify(
        [...Array(auditBoardsCount).keys()].map(i => ({
          name: `Audit Board #${i}`,
        }))
      )
      const response: IErrorResponse = await api(
        `/election/${electionId}/jurisdiction/${jurisdictionId}/round/${roundId}/audit-board`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body,
        }
      )
      // checkAndToast left here for consistency and reference but not tested since it's vestigial
      /* istanbul ignore next */
      if (checkAndToast(response)) return
      getAuditBoards()
    } catch (err) /* istanbul ignore next */ {
      // TEST TODO
      toast.error(err.message)
    }
  }
  return (
    <Wrapper>
      <H4>Number of Audit Boards</H4>
      <p>
        Select the appropriate number of audit baords based upon the personnel
        available and the number of ballots assigned to your jurisdiction for
        this round of the audit. You will have the opportunity to adjust the
        number of audit boards before the next round of the audit, if another
        round is required.
      </p>
      <Formik
        enableReinitialize
        initialValues={{ auditBoards: auditBoards.length || 1 }}
        onSubmit={submit}
      >
        {({ handleSubmit, setFieldValue }) => (
          <>
            <label htmlFor="auditBoards">
              Set the number of audit boards you wish to use.
              <Field
                component={Select}
                id="auditBoards"
                name="auditBoards"
                onChange={(e: React.FormEvent<HTMLSelectElement>) =>
                  setFieldValue('auditBoards', Number(e.currentTarget.value))
                }
                disabled={auditBoards.length}
              >
                {generateOptions(15)}
              </Field>
            </label>
            <br />
            {auditBoards.length === 0 && (
              <FormButton onClick={handleSubmit}>Save &amp; Next</FormButton>
            )}
          </>
        )}
      </Formik>
    </Wrapper>
  )
}

export default CreateAuditBoards
