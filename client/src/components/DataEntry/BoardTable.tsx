import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { Table as BPTable, Column, Cell as BPCell } from '@blueprintjs/table'
import { H1 } from '@blueprintjs/core'
import { Link } from 'react-router-dom'
import { IAuditBoard, BallotStatus } from '../../types'
import { IBallot } from './Ballot'
import LinkButton from '../Atoms/LinkButton'

const RightWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
  margin: 20px 0;
  .bp3-button {
    margin-left: 10px;
  }
  @media (max-width: 775px) {
    .bp3-button {
      width: 100%;
    }
  }
`

const Cell = styled(BPCell)`
  padding: 7px 10px;
  font-size: inherit;
  > div {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 100%;
  }
`

const Table = styled(BPTable)`
  height: auto;
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
  boardName: IAuditBoard['name']
  ballots: IBallot[]
  url: string
}

const KEYS: ('position' | 'tabulator' | 'batch' | 'status')[] = [
  'batch',
  'position',
  'tabulator',
  'status',
]

const BoardTable: React.FC<IProps> = ({ boardName, ballots, url }: IProps) => {
  const renderCell = (rI: number, cI: number) => {
    const ballot = ballots[rI]!
    switch (KEYS[cI]) {
      case 'batch':
        return <Cell>{ballot.batch.name}</Cell>
      case 'position':
        return <Cell>{ballot.position}</Cell>
      case 'status':
        return ballot.status !== BallotStatus.NOT_AUDITED ? (
          <Cell>
            <>
              {ballot.status === BallotStatus.AUDITED ? (
                <span>Audited</span>
              ) : (
                <span>Not Found</span>
              )}
              <Link
                to={`${url}/batch/${ballot.batch.id}/ballot/${ballot.position}`}
                className="bp3-button bp3-small"
              >
                Re-audit
              </Link>
            </>
          </Cell>
        ) : (
          <Cell>Not Audited</Cell>
        )
      case 'tabulator':
        return (
          <Cell>
            {ballot.batch.tabulator === null ? 'N/A' : ballot.batch.tabulator}
          </Cell>
        )
      /* istanbul ignore next */
      default:
        return <Cell>?</Cell>
    }
  }

  const columnWidths = (): (number | undefined)[] => {
    const container = document.getElementsByClassName(
      'board-table-container'
    )[0]
    /* istanbul ignore next */
    if (!container) return Array(KEYS.length).fill(undefined)
    const containerSize = container.clientWidth
    /* istanbul ignore next */
    if (containerSize < 500) return Array(KEYS.length).fill(80)
    return Array(KEYS.length).fill(containerSize / KEYS.length)
  }

  const [cols, setCols] = useState(Array(KEYS.length).fill(undefined))

  useEffect(() => {
    setCols(columnWidths())
  }, [ballots])

  const roundComplete = ballots.every(
    b => b.status !== BallotStatus.NOT_AUDITED
  )

  const unauditedBallot = ballots.find(
    b => b.status === BallotStatus.NOT_AUDITED
  )

  return (
    <div className="board-table-container">
      <H1>{boardName}: Ballot Cards to Audit</H1>
      <p>
        The following ballots have been assigned to your audit board for this
        round of the audit. Once these ballots have been located and retrieved
        from storage, click &quot;Start Auditing&quot; to begin recording the
        votes you see marked on the paper ballots. When you are finished
        auditing these ballots, click &quot;Auditing Complete - Submit
        Results&quot; to submit the results.{' '}
        <strong>
          Note that you will not be able to make changes after results are
          submitted.
        </strong>
      </p>
      <RightWrapper>
        <LinkButton
          to={
            unauditedBallot
              ? `${url}/batch/${unauditedBallot.batch.id}/ballot/${unauditedBallot.position}`
              : ''
          }
          disabled={roundComplete}
        >
          Start Auditing
        </LinkButton>
        <LinkButton to={`${url}/signoff`} disabled={!roundComplete}>
          Auditing Complete - Submit Results
        </LinkButton>
      </RightWrapper>
      {/* <ActionWrapper> // commented out until feature is added
        {!roundComplete && (
          <>
            <Button intent="primary">Download Ballot List as CSV</Button>
          </>
        )}
      </ActionWrapper> */}
      <Table
        numRows={ballots.length}
        defaultRowHeight={40}
        columnWidths={cols}
        enableRowHeader={false}
      >
        <Column key="batch" name="Batch" cellRenderer={renderCell} />
        <Column
          key="position"
          name="Ballot Position"
          cellRenderer={renderCell}
        />
        <Column key="tabulator" name="Tabulator" cellRenderer={renderCell} />
        <Column key="status" name="Status" cellRenderer={renderCell} />
      </Table>
    </div>
  )
}

export default BoardTable
