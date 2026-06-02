import React from 'react'
import { Link } from 'react-router-dom'
import { H1, AnchorButton, Tag } from '@blueprintjs/core'
import styled from 'styled-components'
import { useElection, IElection } from './support-api'
import RoundsTable from './RoundsTable'
import { List, LinkItem } from './List'
import Breadcrumbs from './Breadcrumbs'
import { Column, Row } from './shared'
import H2Title from '../Atoms/H2Title'

const Container = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 20px;
`

const Header = styled.div`
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: center;
  gap: 10px;

  @media (max-width: 480px) {
    flex-direction: column;
    align-items: flex-start;
  }
`

const AuditInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
`

const prettyAuditType = (auditType: IElection['auditType']) =>
  ({
    BALLOT_POLLING: 'Ballot Polling',
    BALLOT_COMPARISON: 'Ballot Comparison',
    BATCH_COMPARISON: 'Batch Comparison',
    HYBRID: 'Hybrid',
  }[auditType])

const Audit = ({
  electionId,
}: {
  electionId: string
}): React.ReactElement | null => {
  const election = useElection(electionId)

  if (!election.isSuccess) return null

  const {
    id,
    auditName,
    auditType,
    organization,
    jurisdictions,
    rounds,
  } = election.data

  return (
    <Container>
      <Row>
        <Header>
          <AuditInfo>
            <Breadcrumbs>
              <Link to={`/support/orgs/${organization.id}`}>
                {organization.name}
              </Link>
            </Breadcrumbs>
            <H1 style={{ marginBottom: 0 }}>{auditName}</H1>
            <Tag large>{prettyAuditType(auditType)}</Tag>
          </AuditInfo>
          <AnchorButton
            href={`/api/support/elections/${id}/login`}
            icon="log-in"
            intent="primary"
          >
            Log in as audit admin
          </AnchorButton>
        </Header>
      </Row>
      <Row>
        <Column>
          <H2Title>Jurisdictions</H2Title>
          <List>
            {jurisdictions.map(jurisdiction => (
              <LinkItem
                to={`/support/jurisdictions/${jurisdiction.id}`}
                key={jurisdiction.id}
              >
                {jurisdiction.name}
                <AnchorButton
                  href={`/api/support/jurisdictions/${jurisdiction.id}/login`}
                  icon="log-in"
                  onClick={(e: React.MouseEvent) => e.stopPropagation()}
                >
                  Log in
                </AnchorButton>
              </LinkItem>
            ))}
          </List>
        </Column>
        <Column>
          <H2Title>Rounds</H2Title>
          <div
            style={{
              alignItems: 'center',
              display: 'flex',
              marginBottom: '10px',
            }}
          ></div>
          <div style={{ marginBottom: '10px' }}>
            <RoundsTable electionId={electionId} rounds={rounds} />
          </div>
        </Column>
      </Row>
    </Container>
  )
}

export default Audit
