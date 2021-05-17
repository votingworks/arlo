/* eslint-disable react/display-name */
import React from 'react'
import styled from 'styled-components'
import { H3, H4, Colors, OL, Icon } from '@blueprintjs/core'
import { Column } from 'react-table'
import { Table } from '../Atoms/Table'
import { Inner } from '../Atoms/Wrapper'
import { BallotStatus } from '../../types'
import LinkButton from '../Atoms/LinkButton'
import { IBallot } from '../MultiJurisdictionAudit/RoundManagement/useBallots'
import { IAuditBoard } from '../UserContext'

const LeftSection = styled.div`
  .summary-label {
    margin-right: 10px;
  }
`

const RightSection = styled.div`
  @media (max-width: 768px) {
    display: flex;
    margin-top: 10px;
  }
`

const HeaderWrapper = styled.div`
  background-color: #eeeeee;
  padding: 30px;
`

const HeaderInnerWrapper = styled(Inner)`
  display: flex;
  align-items: center;
  justify-content: space-between;

  @media only screen and (max-width: 767px) {
    flex-direction: column;
  }
`

const ContentWrapper = styled.div`
  display: flex;
  margin-top: 30px;
  width: 100%;

  @media only screen and (max-width: 767px) {
    flex-direction: column;
  }
`

const TableWrapper = styled.div`
  width: 70%;

  @media only screen and (max-width: 767px) {
    order: 2;
    width: 100%;
  }
`

const InstructionsWrapper = styled.div`
  width: 30%;
  padding-left: 30px;
  @media only screen and (max-width: 767px) {
    order: 1;
    width: 100%;
    padding-left: 0;
  }
`

const AuditBtn = styled(LinkButton)`
  border: 1px solid ${Colors.GRAY4};
  border-radius: 5px;
  @media only screen and (max-width: 768px) {
    min-width: auto;
  }
`

const grayColor = {
  color: `${Colors.GRAY3}`,
}

const DangerLabel = styled.span`
  color: ${Colors.RED4};
`

const SuccessLabel = styled.span`
  color: ${Colors.GREEN4};
`

const WarningLabel = styled.span`
  color: ${Colors.ORANGE3};
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
      accessor: ballot => (
        <p style={ballot.status !== BallotStatus.NOT_AUDITED ? grayColor : {}}>
          {ballot.batch.name}
        </p>
      ),
    },
    {
      Header: 'Position',
      accessor: ballot => (
        <p style={ballot.status !== BallotStatus.NOT_AUDITED ? grayColor : {}}>
          {ballot.position}
        </p>
      ),
    },
    {
      Header: 'Status',
      // eslint-disable-next-line react/display-name
      accessor: ballot => {
        return ballot.status !== BallotStatus.NOT_AUDITED ? (
          <>
            {ballot.status === BallotStatus.AUDITED ? (
              <p style={grayColor}>
                <Icon icon="tick" /> Audited
              </p>
            ) : (
              <p style={grayColor}>
                <Icon icon="tick" /> Not Found
              </p>
            )}
          </>
        ) : (
          <WarningLabel>Not Audited</WarningLabel>
        )
      },
    },
    {
      Header: 'Actions',
      accessor: ballot => {
        return ballot.status === BallotStatus.AUDITED ||
          ballot.status === BallotStatus.NOT_FOUND ? (
          <AuditBtn
            to={`${url}/batch/${ballot.batch.id}/ballot/${ballot.position}`}
            minimal
            fill
          >
            Re-Audit
          </AuditBtn>
        ) : (
          <AuditBtn
            to={`${url}/batch/${ballot.batch.id}/ballot/${ballot.position}`}
            minimal
            fill
          >
            <strong>Audit Ballot</strong>
          </AuditBtn>
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

  const totalAudited = ballots.filter(
    ballot => ballot.status === BallotStatus.AUDITED
  ).length

  const totalNotFound = ballots.filter(
    ballot => ballot.status === BallotStatus.NOT_FOUND
  ).length

  const totalNotAudited = ballots.filter(
    ballot => ballot.status === BallotStatus.NOT_AUDITED
  ).length

  const HeaderButton = roundComplete ? (
    <LinkButton to={`${url}/signoff`} intent="success" large>
      Submit Audited Ballots
    </LinkButton>
  ) : (
    <LinkButton
      to={
        unauditedBallot
          ? `${url}/batch/${unauditedBallot.batch.id}/ballot/${unauditedBallot.position}`
          : ''
      }
      intent="success"
      large
    >
      {totalAudited === 0 ? 'Audit First Ballot' : 'Audit Next Ballot'}
    </LinkButton>
  )

  return (
    <div className="board-table-container">
      <HeaderWrapper>
        <HeaderInnerWrapper>
          <LeftSection>
            <p className="bp3-text-large">
              {totalAudited + totalNotFound} of {ballots.length} ballots have
              been audited.
            </p>
            <SuccessLabel className="summary-label">
              Audited: {totalAudited}
            </SuccessLabel>
            <WarningLabel className="summary-label">
              Not Audited: {totalNotAudited}
            </WarningLabel>
            {totalNotFound > 0 && (
              <DangerLabel className="summary-label">
                Not Found: {totalNotFound}
              </DangerLabel>
            )}
          </LeftSection>
          <RightSection>{HeaderButton}</RightSection>
        </HeaderInnerWrapper>
      </HeaderWrapper>
      <Inner>
        <ContentWrapper>
          <TableWrapper>
            <H3>Ballots for {boardName}</H3>
            <Table data={ballots} columns={columns} />
            <LinkButton
              to={`${url}/signoff`}
              disabled={!roundComplete}
              intent={roundComplete ? 'success' : 'none'}
              style={{ float: 'right', marginTop: '10px' }}
              large
            >
              Submit Audited Ballots
            </LinkButton>
          </TableWrapper>
          <InstructionsWrapper>
            <H4>Instructions</H4>
            <OL>
              <li>
                Locate and retrieve the list of ballots to audit from storage.
              </li>
              <li>Audit each ballot by indicating the votes you see marked.</li>
              <li>
                Once all ballots are audited, Submit audited ballots. Once
                results are submitted, no further edits can be made.
              </li>
            </OL>
          </InstructionsWrapper>
        </ContentWrapper>
      </Inner>
    </div>
  )
}

export default BoardTable
