import React, { useState } from 'react'
import styled from 'styled-components'
import { Table, Column, Cell } from '@blueprintjs/table'
import { H1, Button, Checkbox } from '@blueprintjs/core'
import { AuditBoard, Ballot } from '../../types'

const RightWrapper = styled.div`
  display: flex;
  flex-direction: row-reverse;
  margin: 20px 0;
`

const PaddedCell = styled(Cell)`
  padding: 3px 5px;
`

const RightButton = styled(Button)`
  float: right;
`

const ActionWrapper = styled.div`
  margin-bottom: 20px;
  .bp3-checkbox {
    display: inline-block;
    margin-left: 20px;
  }
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

const STATUSES: { [key: string]: string } = {
  AUDITED: 'Audited',
  NOT_AUDITED: 'Not Audited',
}

const BoardTable: React.FC<Props> = ({ board }: Props) => {
  const renderCell = (rI: number, cI: number) => {
    if (board.ballots) {
      const row: Ballot = board.ballots[rI]
      if (!KEYS[cI]) {
        return <PaddedCell>{board.name}</PaddedCell>
      } else if (STATUSES[row[KEYS[cI]]]) {
        const action =
          row[KEYS[cI]] === 'AUDITED' ? (
            <RightButton small>Re-audit</RightButton>
          ) : null
        return (
          <PaddedCell>
            <>
              {STATUSES[row[KEYS[cI]]]} {action}
            </>
          </PaddedCell>
        )
        // wrapping content in React.Fragment to avoid unexpected props being passed to dom elements and throwing warnings
      } else {
        return <PaddedCell>{row[KEYS[cI]]}</PaddedCell>
      }
    } else {
      return <PaddedCell loading />
    }
  }

  const columnWidths = (): (number | null)[] => {
    const container = document.getElementsByClassName(
      'board-table-container'
    )[0]
    if (!container) return Array(5).fill(null)
    const containerSize = container.clientWidth
    const colWidth = (containerSize - 31) / 5
    return Array(5).fill(colWidth)
  }

  const [kcut, setKcut] = useState(true)
  const handleKcut = (e: React.ChangeEvent<HTMLInputElement>) =>
    setKcut(e.target.checked)

  const roundComplete =
    board.ballots && board.ballots.every(b => b.status === 'AUDITED')

  return (
    <div className="board-table-container">
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
        {roundComplete ? (
          <Button intent="primary">Review Complete - Finish Round</Button>
        ) : (
          <Button intent="primary">Start Auditing</Button>
        )}
      </RightWrapper>
      <ActionWrapper>
        {!roundComplete && (
          <>
            <Button intent="primary">Download Ballot List as CSV</Button>
            <Checkbox checked={kcut} label="Use K-CUT" onChange={handleKcut} />
          </>
        )}
      </ActionWrapper>
      <Table numRows={10} defaultRowHeight={30} columnWidths={columnWidths()}>
        <Column key="tabulator" name="Tabulator" cellRenderer={renderCell} />
        <Column key="batch" name="Batch" cellRenderer={renderCell} />
        <Column key="record" name="Record/Position" cellRenderer={renderCell} />
        <Column key="status" name="Status" cellRenderer={renderCell} />
        <Column name="Audit Board" cellRenderer={renderCell} />
      </Table>
    </div>
  )
}

export default BoardTable
