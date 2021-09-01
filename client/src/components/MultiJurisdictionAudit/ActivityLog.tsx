import React, { useState } from 'react'
import { useQuery } from 'react-query'
import { HTMLSelect, H3 } from '@blueprintjs/core'
import { useAuthDataContext, IAuditAdmin } from '../UserContext'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import { StyledTable, DownloadCSVButton } from '../Atoms/Table'
import { fetchApi } from '../SupportTools/support-api'

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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  info: any
}

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
  const [organization, setOrganization] = useState(user.organizations[0])
  const activities = useQuery(['orgs', organization.id, 'activities'], () =>
    fetchApi(`/api/organizations/${organization.id}/activities`)
  )

  if (!activities.isSuccess) return null

  const showOrgSelect = user.organizations.length > 1

  return (
    <Wrapper>
      <Inner>
        <div style={{ marginTop: '20px', width: '100%' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '10px',
            }}
          >
            <H3 style={{ margin: 0 }}>Activity Log</H3>
            <div>
              {showOrgSelect && (
                // eslint-disable-next-line jsx-a11y/label-has-associated-control
                <label htmlFor="organizationId" style={{ marginRight: '10px' }}>
                  Organization:&nbsp;
                  <HTMLSelect
                    id="organizationId"
                    name="organizationId"
                    onChange={e =>
                      setOrganization(
                        user.organizations.find(
                          ({ id }) => id === e.currentTarget.value
                        )!
                      )
                    }
                    value={organization.id}
                    options={user.organizations.map(({ id, name }) => ({
                      label: name,
                      value: id,
                    }))}
                  />
                </label>
              )}
              <DownloadCSVButton
                tableId="activityLog"
                fileName={`arlo-activity-${organization.name}.csv`}
              />
            </div>
          </div>
          <StyledTable id="activityLog" style={{ tableLayout: 'auto' }}>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>User</th>
                <th>Action</th>
                <th>Audit</th>
                <th>Jurisdiction</th>
              </tr>
            </thead>
            <tbody>
              {activities.data.map((activity: IActivity) => (
                <tr key={activity.id}>
                  <td>{new Date(activity.timestamp).toLocaleString()}</td>
                  <td>
                    {activity.user &&
                      activity.user.type !== 'audit_board' &&
                      (activity.user.supportUser || activity.user.key)}
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
