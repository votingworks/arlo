import React from 'react'
import { Link } from 'react-router-dom'
import { H3, H2, AnchorButton, Tag } from '@blueprintjs/core'
import { useElection, IElection } from './support-api'
import RoundsTable from './RoundsTable'
import { List, LinkItem } from './List'
import Breadcrumbs from './Breadcrumbs'
import { Column } from './shared'

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
    <div style={{ width: '100%' }}>
      <Breadcrumbs>
        <Link to={`/support/orgs/${organization.id}`}>{organization.name}</Link>
      </Breadcrumbs>
      <H2>{auditName}</H2>
      <Column>
        <div
          style={{
            alignItems: 'center',
            display: 'flex',
            marginBottom: '10px',
          }}
        >
          <Tag large style={{ marginRight: '10px' }}>
            {prettyAuditType(auditType)}
          </Tag>
          <AnchorButton
            href={`/api/support/elections/${id}/login`}
            icon="log-in"
            intent="primary"
          >
            Log in as audit admin
          </AnchorButton>
        </div>
        <div style={{ marginBottom: '10px' }}>
          <RoundsTable electionId={electionId} rounds={rounds} />
        </div>
        <H3>Jurisdictions</H3>
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
    </div>
  )
}

export default Audit
