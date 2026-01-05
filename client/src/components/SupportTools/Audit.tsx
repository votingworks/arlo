import React from 'react'
import { Link } from 'react-router-dom'
import { H1, AnchorButton, Tag } from '@blueprintjs/core'
import { useElection, IElection } from './support-api'
import RoundsTable from './RoundsTable'
import { List, LinkItem } from './List'
import Breadcrumbs from './Breadcrumbs'
import { Column, Row } from './shared'
import H2Title from '../Atoms/H2Title'

const prettyAuditType = (auditType: IElection['auditType']) =>
  ({
    BALLOT_POLLING: 'Ballot Polling',
    BALLOT_COMPARISON: 'Ballot Comparison',
    BATCH_COMPARISON: 'Batch Comparison',
    HYBRID: 'Hybrid',
  }[auditType])

const Audit = ({ electionId }: { electionId: string }) => {
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
    <div
      style={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        marginTop: '20px',
      }}
    >
      <Row>
        <Breadcrumbs>
          <Link to={`/support/orgs/${organization.id}`}>
            {organization.name}
          </Link>
        </Breadcrumbs>
      </Row>
      <Row>
        <div
          style={{
            display: 'flex',
            width: '100%',
            justifyContent: 'space-between',
            margin: '10px 0 20px 0',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <H1 style={{ marginBottom: 0 }}>{auditName}</H1>
            <Tag large>{prettyAuditType(auditType)}</Tag>
          </div>
          <AnchorButton
            href={`/api/support/elections/${id}/login`}
            icon="log-in"
            intent="primary"
          >
            Log in as audit admin
          </AnchorButton>
        </div>
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
    </div>
  )
}

export default Audit
