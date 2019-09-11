import React from 'react'
import styled from 'styled-components'
import { Table, Column, Cell } from '@blueprintjs/table'
import { H1, Button } from '@blueprintjs/core'
import { AuditBoard, Ballot } from '../../types'

const RightWrapper = styled.div`
  display: flex;
  flex-direction: row-reverse;
  margin: 20px 0;
`

interface Props {
  setIsLoading: (arg0: boolean) => void
  isLoading: boolean
  board: AuditBoard
}

const KEYS: ('tabulator' | 'batch' | 'record' | 'status')[] = [
  'tabulator',
  'batch',
  'record',
  'status',
]

const CONSTANTS: { [key: string]: string } = {
  AUDITED: 'Audited',
  NOT_AUDITED: 'Not Audited',
}

const BoardTable: React.FC<Props> = ({ board }: Props) => {
  const renderCell = (rI: number, cI: number) => {
    if (board.ballots) {
      const row: Ballot = board.ballots[rI]
      if (!KEYS[cI]) {
        return <Cell>{board.name}</Cell>
      } else if (CONSTANTS[row[KEYS[cI]]]) {
        return <Cell>{CONSTANTS[row[KEYS[cI]]]}</Cell>
      } else {
        return <Cell>{row[KEYS[cI]]}</Cell>
      }
    } else {
      return <Cell loading />
    }
  }
  return (
    <>
      <H1>{board.name}: Ballot Cards to Audit</H1>
      <p>
        Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod
        tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
        veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
        commodo consequat. Duis aute irure dolor in reprehenderit in voluptate
        velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
        occaecat cupidatat non proident, sunt in culpa qui officia deserunt
        mollit anim id est laborum.
      </p>
      <RightWrapper>
        <Button intent="primary">Start Auditing</Button>
      </RightWrapper>
      <Table numRows={10}>
        <Column key="tabulator" name="Tabulator" cellRenderer={renderCell} />
        <Column key="batch" name="Batch" cellRenderer={renderCell} />
        <Column key="record" name="Record/Position" cellRenderer={renderCell} />
        <Column key="status" name="Status" cellRenderer={renderCell} />
        <Column name="Audit Board" cellRenderer={renderCell} />
      </Table>
    </>
  )
}

export default BoardTable
