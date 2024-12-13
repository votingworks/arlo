import React from 'react'
import { Link } from 'react-router-dom'
import { H2, AnchorButton, Tag, H4 } from '@blueprintjs/core'
import { useElection, IElection } from './support-api'
import RoundsTable from './RoundsTable'
import { List, LinkItem } from './List'
import Breadcrumbs from './Breadcrumbs'
import { Column, Row } from './shared'

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
        gap: '20px',
        marginTop: '20px',
      }}
    >
      <Row>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
            alignItems: 'flex-start',
            width: '100%',
          }}
        >
          <div
            style={{
              display: 'flex',
              width: '100%',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
            }}
          >
            <H2 style={{ margin: '0', maxWidth: '80%' }}>{auditName}</H2>
            <AnchorButton
              href={`/api/support/elections/${id}/login`}
              icon="log-in"
              intent="primary"
            >
              Log in as audit admin
            </AnchorButton>
          </div>
        </div>
      </Row>
      <Row>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <Tag large>{prettyAuditType(auditType)}</Tag> for
          <Breadcrumbs>
            <Link to={`/support/orgs/${organization.id}`}>
              {organization.name}
            </Link>
          </Breadcrumbs>
        </div>
      </Row>
      <Row>
        <Column>
          <H4>Jurisdictions</H4>
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
          <H4>Rounds</H4>
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
