import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { Table, Column, Cell } from '@blueprintjs/table'
import { H1, AnchorButton } from '@blueprintjs/core'
import { Link } from 'react-router-dom'
import { IAuditBoard, BallotStatus } from '../../types'
import { IBallot } from './Ballot'

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

const PaddedCell = styled(Cell)`
  padding: 3px 5px;
`

const GrowingTable = styled(Table)`
  height: auto;
`

const ReauditLink = styled(Link)`
  margin-left: 50px;
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
        return <PaddedCell>{ballot.batch.name}</PaddedCell>
      case 'position':
        return <PaddedCell>{ballot.position}</PaddedCell>
      case 'status':
        return ballot.status !== BallotStatus.NOT_AUDITED ? (
          <PaddedCell>
            <>
              {ballot.status === BallotStatus.AUDITED ? (
                <>Audited</>
              ) : (
                <>Not Found</>
              )}
              <ReauditLink
                to={`${url}/batch/${ballot.batch.id}/ballot/${ballot.position}`}
                className="bp3-button bp3-small"
              >
                Re-audit
              </ReauditLink>
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
      default:
        return <PaddedCell>?</PaddedCell>
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
        <AnchorButton
          href={
            unauditedBallot
              ? `${url}/batch/${unauditedBallot.batch.id}/ballot/${unauditedBallot.position}`
              : ''
          }
          disabled={roundComplete}
        >
          Start Auditing
        </AnchorButton>
        <AnchorButton href={`${url}/signoff`} disabled={!roundComplete}>
          Auditing Complete - Submit Results
        </AnchorButton>
      </RightWrapper>
      {/* <ActionWrapper> // commented out until feature is added
        {!roundComplete && (
          <>
            <Button intent="primary">Download Ballot List as CSV</Button>
          </>
        )}
      </ActionWrapper> */}
      <GrowingTable
        numRows={ballots.length}
        defaultRowHeight={30}
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
      </GrowingTable>
    </div>
  )
}

export default BoardTable
