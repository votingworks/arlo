import React from 'react'
import styled from 'styled-components'
import { H1 } from '@blueprintjs/core'
import { Link } from 'react-router-dom'
import { Column } from 'react-table'
import { Table } from '../Atoms/Table'
import { BallotStatus } from '../../types'
import LinkButton from '../Atoms/LinkButton'
import { IBallot } from '../MultiJurisdictionAudit/RoundManagement/useBallots'
import { IAuditBoard } from '../UserContext'

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

interface IProps {
  boardName: IAuditBoard['name']
  ballots: IBallot[]
  url: string
}

const BoardTable: React.FC<IProps> = ({ boardName, ballots, url }: IProps) => {
  const columns: Column<IBallot>[] = [
    {
      Header: 'Batch',
      accessor: ({ batch: { name } }) => name,
    },
    {
      Header: 'Ballot Position',
      accessor: 'position',
    },
    {
      Header: 'Status',
      // eslint-disable-next-line react/display-name
      accessor: ballot => {
        return ballot.status !== BallotStatus.NOT_AUDITED ? (
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
        ) : (
          'Not Audited'
        )
      },
    },
  ]
  if (ballots.length && ballots[0].batch.tabulator)
    columns.unshift({
      Header: 'Tabulator',
      accessor: ({ batch: { tabulator } }) => tabulator,
    })
  if (ballots.length && ballots[0].batch.container)
    columns.unshift({
      Header: 'Container',
      accessor: ({ batch: { container } }) => container,
    })

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
      <Table data={ballots} columns={columns} />
    </div>
  )
}

export default BoardTable
