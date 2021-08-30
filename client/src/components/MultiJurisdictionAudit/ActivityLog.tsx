import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from 'react-query'
import { HTMLSelect, H1, H2, H5, HTMLTable, H3 } from '@blueprintjs/core'
import { api } from '../utilities'
import { fetchApi } from '../SupportTools/support-api'
import { useAuthDataContext, IAuditAdmin } from '../UserContext'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import { StyledTable } from '../Atoms/Table'

interface IActivity {
  id: string
  activityName: string
  timestamp: string
  user: {
    type: string
    key: string
    supportUser: boolean
  } | null
  election: {
    id: string
    auditName: string
    auditType: string
  } | null
  info: any
}

const camelToSentenceCase = (text: string) => text.replace(/([A-Z])/g, ' $1')
const snakeToSentenceCase = (text: string) => text.replace(/_/g, ' ')

const prettyAction = (activity: IActivity) => {
  switch (activity.activityName) {
    case 'CreateAudit':
      return `Created audit`
    case 'DeleteAudit':
      return `Deleted audit`
    case 'StartRound':
      return `Started round ${activity.info.round_num}`
    case 'EndRound':
      return `Ended round ${activity.info.round_num}`
    case 'CalculateSampleSizes':
      return `Calculated sample sizes`
    case 'UploadFile': {
      const fileType = ({
        ballot_manifest: 'ballot manifest', // eslint-disable-line @typescript-eslint/camelcase
        batch_tallies: 'candidate totals by batch', // eslint-disable-line @typescript-eslint/camelcase
        cvrs: 'CVRs',
      } as { [k: string]: string })[activity.info.file_type]
      return activity.info.error
        ? `Uploaded invalid ${fileType}`
        : `Successfully uploaded ${fileType}`
    }
    case 'CreateAuditBoards':
      return 'Created audit boards'
    case 'RecordResults':
      return 'Recorded results'
    case 'AuditBoardSignOff':
      return `${activity.info.audit_board_name} signed off`
    default:
      throw Error(`Unknown activity: ${activity.activityName}`)
  }
}

const ActivityLog = () => {
  const auth = useAuthDataContext()
  const { user } = auth! as { user: IAuditAdmin }
  const [organizationId, setOrganizationId] = useState(user.organizations[0].id)
  const activities = useQuery(['orgs', organizationId, 'activities'], () =>
    fetchApi(`/api/organizations/${organizationId}/activities`)
  )

  if (!activities.isSuccess) return null

  return (
    <Wrapper>
      <Inner>
        <div style={{ marginTop: '20px', width: '100%' }}>
          <H3>Activity Log</H3>
          <div style={{ marginBottom: '15px', marginTop: '15px' }}>
            {user.organizations.length > 1 && (
              // eslint-disable-next-line jsx-a11y/label-has-associated-control
              <label htmlFor="organizationId">
                Organization:&nbsp;
                <HTMLSelect
                  id="organizationId"
                  name="organizationId"
                  onChange={e => setOrganizationId(e.currentTarget.value)}
                  value={organizationId}
                  options={user.organizations.map(({ id, name }) => ({
                    label: name,
                    value: id,
                  }))}
                />
              </label>
            )}
          </div>
          <StyledTable style={{ tableLayout: 'auto' }}>
            <thead>
              <th>Timestamp</th>
              <th>User</th>
              <th>Action</th>
              <th>Audit</th>
              <th>Jurisdiction</th>
            </thead>
            <tbody>
              {activities.data.map((activity: IActivity) => (
                <tr key={activity.id}>
                  <td>{new Date(activity.timestamp).toLocaleString()}</td>
                  <td>
                    {activity.user &&
                      activity.user.type !== 'audit_board' &&
                      (activity.user.supportUser
                        ? 'VotingWorks Support'
                        : activity.user.key)}
                  </td>
                  <td>{prettyAction(activity)}</td>
                  <td>{activity.election && activity.election.auditName}</td>
                  <td>
                    {'jurisdiction_name' in activity.info &&
                      activity.info.jurisdiction_name}
                  </td>
                </tr>
              ))}
            </tbody>
          </StyledTable>
        </div>
      </Inner>
    </Wrapper>
  )
}

export default ActivityLog
