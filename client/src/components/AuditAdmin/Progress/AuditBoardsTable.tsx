import React from 'react'
import { Button } from '@blueprintjs/core'

import { Confirm, useConfirm } from '../../Atoms/Confirm'
import { StyledTable } from '../../Atoms/Table'

interface IAuditBoardMinimal {
  id: string
  name: string
  signedOffAt: string | null
}

interface IProps {
  auditBoards: IAuditBoardMinimal[]
  reopenAuditBoard?: (auditBoard: IAuditBoardMinimal) => Promise<void>
}

const AuditBoardsTable = ({ auditBoards, reopenAuditBoard }: IProps) => {
  const { confirm, confirmProps } = useConfirm()

  return (
    <>
      <StyledTable>
        <thead>
          <tr>
            <th>Audit Board</th>
            {reopenAuditBoard && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {auditBoards.map(auditBoard => (
            <tr key={auditBoard.id}>
              <td>{auditBoard.name}</td>
              {reopenAuditBoard && (
                <td>
                  <Button
                    disabled={!auditBoard.signedOffAt}
                    onClick={() =>
                      confirm({
                        title: 'Confirm',
                        description: `Are you sure you want to reopen ${auditBoard.name}?`,
                        yesButtonLabel: 'Reopen',
                        onYesClick: () => reopenAuditBoard(auditBoard),
                      })
                    }
                  >
                    Reopen
                  </Button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </StyledTable>
      <Confirm {...confirmProps} />
    </>
  )
}

export default AuditBoardsTable
