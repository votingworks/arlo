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

// const ActionWrapper = styled.div` // commented out until feature is used
//   margin-bottom: 20px;
//   .bp3-checkbox {
//     display: inline-block;
//     margin-left: 20px;
//   }
//   @media (max-width: 775px) {
//     .bp3-button {
//       width: 100%;
//     }
//   }
// `

interface IProps {
  setIsLoading: (arg0: boolean) => void
  isLoading: boolean
  boardName: IAuditBoard['name']
  ballots: IBallot[]
  url: string
  round: number
}

const KEYS: ('position' | 'tabulator' | 'batch' | 'status' | 'round')[] = [
  'position',
  'batch',
  'status',
  'tabulator',
  'round',
]

const BoardTable: React.FC<IProps> = ({
  boardName,
  ballots,
  url,
  round,
}: IProps) => {
  const renderCell = (rI: number, cI: number) => {
    /* istanbul ignore else */
    if (ballots) {
      const ballot: IBallot = ballots[rI]
      switch (KEYS[cI]) {
        case 'position':
          return <PaddedCell>{ballot.position}</PaddedCell>
        case 'batch':
          return <PaddedCell>{ballot.batch.name}</PaddedCell>
        case 'status':
          return ballot.status ? (
            <PaddedCell>
              <>
                <Link
                  to={`${url}/round/1/batch/${ballot.batch.id}/ballot/${ballot.position}`}
                  className="bp3-button bp3-small"
                >
                  Re-audit
                </Link>
              </>
            </PaddedCell>
          ) : (
            <PaddedCell>Not Audited</PaddedCell>
          )
        case 'tabulator':
          return (
            <PaddedCell>
              {ballot.batch.tabulator === null ? 'N/A' : ballot.batch.tabulator}
            </PaddedCell>
          )
        /* istanbul ignore next */
        case 'round':
          return <PaddedCell>{round}</PaddedCell>
        /* istanbul ignore next */
        default:
          return <PaddedCell>?</PaddedCell>
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
    /* istanbul ignore next */
    if (containerSize < 775) return Array(length).fill(80)
    return Array(length).fill(containerSize / length)
  }

  const roundComplete = ballots && ballots.every(b => b.status === 'AUDITED')

  let numRows = 10
  /* istanbul ignore next */
  if (ballots && ballots.length < 10) numRows = ballots.length

  return (
    <div className="board-table-container">
      <H1>{boardName}: Ballot Cards to Audit</H1>
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
          ballots && (
            <Link
              to={
                url +
                `/round/1/batch/${ballots[0].batch.id}/ballot/${ballots[0].position}`
              }
              className="bp3-button bp3-intent-primary"
            >
              Start Auditing
            </Link>
          )
        )}
      </RightWrapper>
      {/* <ActionWrapper> // commented out until feature is added
        {!roundComplete && (
          <>
            <Button intent="primary">Download Ballot List as CSV</Button>
          </>
        )}
      </ActionWrapper> */}
      <Table
        numRows={numRows}
        defaultRowHeight={30}
        columnWidths={columnWidths(5)}
        enableRowHeader={false}
      >
        <Column
          key="position"
          name="Ballot Position"
          cellRenderer={renderCell}
        />
        <Column key="batch" name="Batch" cellRenderer={renderCell} />
        <Column key="status" name="Status" cellRenderer={renderCell} />
        <Column key="tabulator" name="Tabulator" cellRenderer={renderCell} />
        <Column key="round" name="Audit Round" cellRenderer={renderCell} />
      </Table>
    </div>
  )
}

export default BoardTable
