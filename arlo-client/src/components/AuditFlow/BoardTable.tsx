import React from 'react'
import styled from 'styled-components'
import { Table, Column, Cell } from '@blueprintjs/table'
import { H1, Button } from '@blueprintjs/core'
import { Link } from 'react-router-dom'
import { IAuditBoard, IBallot } from '../../types'

const RightWrapper = styled.div`
  display: flex;
  flex-direction: row-reverse;
  margin: 20px 0;
  @media (max-width: 775px) {
    .bp3-button {
      width: 100%;
    }
  }
`

const PaddedCell = styled(Cell)`
  padding: 3px 5px;
`

const ActionWrapper = styled.div`
  margin-bottom: 20px;
  .bp3-checkbox {
    display: inline-block;
    margin-left: 20px;
  }
  @media (max-width: 775px) {
    .bp3-button {
      width: 100%;
    }
  }
`

interface IProps {
  setIsLoading: (arg0: boolean) => void
  isLoading: boolean
  board: IAuditBoard
  url: string
}

const KEYS: ('id' | 'tabulator' | 'batch' | 'position' | 'status')[] = [
  'id',
  'batch',
  'status',
  'tabulator',
  'position',
]

const STATUSES: { [key: string]: string } = {
  AUDITED: 'Audited',
  NOT_AUDITED: 'Not Audited',
}

const BoardTable: React.FC<IProps> = ({ board, url }: IProps) => {
  const renderCell = (rI: number, cI: number) => {
    if (board.ballots) {
      const row: IBallot = board.ballots[rI]
      if (!KEYS[cI]) {
        return <PaddedCell>{board.name}</PaddedCell>
      } else if (STATUSES[row[KEYS[cI]]]) {
        const content =
          row[KEYS[cI]] === 'AUDITED' ? (
            <Link
              to={`${url}/round/1/ballot/${row.id}`}
              className="bp3-button bp3-small"
            >
              Re-audit
            </Link>
          ) : (
            STATUSES[row[KEYS[cI]]]
          )
        return (
          <PaddedCell>
            <>{content}</>
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

  const columnWidths = (length: number): (number | null)[] => {
    const container = document.getElementsByClassName(
      'board-table-container'
    )[0]
    if (!container) return Array(length).fill(null)
    const containerSize = container.clientWidth
    if (containerSize < 775) return Array(length).fill(80)
    return Array(length).fill(containerSize / length)
  }

  const roundComplete =
    board.ballots && board.ballots.every(b => b.status === 'AUDITED')

  let numRows = 10
  if (board.ballots && board.ballots.length < 10) numRows = board.ballots.length

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
          board.ballots && (
            <Link
              to={url + '/round/1/ballot/1'}
              className="bp3-button bp3-intent-primary"
            >
              Start Auditing
            </Link>
          )
        )}
      </RightWrapper>
      <ActionWrapper>
        {!roundComplete && (
          <>
            <Button intent="primary">Download Ballot List as CSV</Button>
          </>
        )}
      </ActionWrapper>
      <Table
        numRows={numRows}
        defaultRowHeight={30}
        columnWidths={columnWidths(6)}
        enableRowHeader={false}
      >
        <Column key="id" name="Ballot" cellRenderer={renderCell} />
        <Column key="batch" name="Batch" cellRenderer={renderCell} />
        <Column key="status" name="Status" cellRenderer={renderCell} />
        <Column key="tabulator" name="Tabulator" cellRenderer={renderCell} />
        <Column
          key="position"
          name="Record/Position"
          cellRenderer={renderCell}
        />
        <Column name="Audit Board" cellRenderer={renderCell} />
      </Table>
    </div>
  )
}

export default BoardTable
