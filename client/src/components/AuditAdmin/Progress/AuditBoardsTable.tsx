import React from 'react'
import { Button } from '@blueprintjs/core'
import { Cell, Column } from 'react-table'

import { Confirm, useConfirm } from '../../Atoms/Confirm'
import { Table } from '../../Atoms/Table'

interface IAuditBoardMinimal {
  id: string
  name: string
  signedOffAt: string | null
}

interface IProps {
  areAuditBoardsOnline: boolean
  auditBoards: IAuditBoardMinimal[]
  reopenAuditBoard: (auditBoard: IAuditBoardMinimal) => Promise<void>
}

const AuditBoardsTable = ({
  areAuditBoardsOnline,
  auditBoards,
  reopenAuditBoard,
}: IProps) => {
  const { confirm, confirmProps } = useConfirm()

  const columns: Column<IAuditBoardMinimal>[] = [
    {
      Header: 'Audit Board',
      Cell: (cell: Cell<IAuditBoardMinimal>) => {
        const auditBoard = cell.row.original
        return auditBoard.name
      },
    },
  ]
  if (areAuditBoardsOnline) {
    columns.push({
      Header: 'Actions',
      // eslint-disable-next-line react/display-name
      Cell: (cell: Cell<IAuditBoardMinimal>) => {
        const auditBoard = cell.row.original
        return (
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
        )
      },
    })
  }
  return (
    <>
      <Table columns={columns} data={auditBoards} />
      <Confirm {...confirmProps} />
    </>
  )
}

export default AuditBoardsTable
