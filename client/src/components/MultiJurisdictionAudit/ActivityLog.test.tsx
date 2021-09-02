import React from 'react'
import { screen, waitFor } from '@testing-library/react'
import { QueryClientProvider } from 'react-query'
import userEvent from '@testing-library/user-event'
import { aaApiCalls } from './_mocks'
import { withMockFetch, renderWithRouter } from '../testUtilities'
import ActivityLog from './ActivityLog'
import AuthDataProvider from '../UserContext'
import { PrivateRoute, queryClient } from '../../App'
import * as utilities from '../utilities'

const mockElection = {
  id: 'election-id-1',
  auditName: 'Test Audit',
  auditType: 'BALLOT_POLLING',
}

const mockAuditAdmin = {
  key: 'admin@example.gov',
  type: 'audit_admin',
  supportUser: null,
}

const mockJurisdictionAdmin = {
  key: 'admin@example.gov',
  type: 'jurisdiction_admin',
  supportUser: null,
}

const mockSupportUser = {
  key: 'admin@example.gov',
  type: 'audit_admin',
  supportUser: 'support@example.gov',
}

// Adds a minute each time it's called
const nextTimestamp = (() => {
  let lastTimestamp = new Date('2021-08-31T22:52:49.762Z')
  return () => {
    lastTimestamp = new Date(lastTimestamp.getTime() + 60 * 1000)
    return lastTimestamp
  }
})()

const nextId = (() => {
  let lastId = 0
  return () => {
    lastId += 1
    return lastId
  }
})()

const apiCalls = {
  getActivities: {
    url: `/api/organizations/org-id/activities`,
    response: [
      {
        id: nextId(),
        activityName: 'CreateAudit',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: mockAuditAdmin,
        info: {},
      },
      {
        id: nextId(),
        activityName: 'JurisdictionAdminLogin',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: mockJurisdictionAdmin,
        info: {},
      },
      {
        id: nextId(),
        activityName: 'UploadFile',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: null,
        info: {
          jurisdiction_id: 'jurisdiction-id-1', // eslint-disable-line @typescript-eslint/camelcase
          jurisdiction_name: 'Jurisdiction 1', // eslint-disable-line @typescript-eslint/camelcase
          file_type: 'ballot_manifest', // eslint-disable-line @typescript-eslint/camelcase
          error: 'failed',
        },
      },
      {
        id: nextId(),
        activityName: 'UploadFile',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: null,
        info: {
          jurisdiction_id: 'jurisdiction-id-1', // eslint-disable-line @typescript-eslint/camelcase
          jurisdiction_name: 'Jurisdiction 1', // eslint-disable-line @typescript-eslint/camelcase
          file_type: 'batch_tallies', // eslint-disable-line @typescript-eslint/camelcase
          error: null,
        },
      },
      {
        id: nextId(),
        activityName: 'UploadFile',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: null,
        info: {
          jurisdiction_id: 'jurisdiction-id-1', // eslint-disable-line @typescript-eslint/camelcase
          jurisdiction_name: 'Jurisdiction 1', // eslint-disable-line @typescript-eslint/camelcase
          file_type: 'cvrs', // eslint-disable-line @typescript-eslint/camelcase
          error: null,
        },
      },
      {
        id: nextId(),
        activityName: 'CalculateSampleSizes',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: mockAuditAdmin,
        info: {},
      },
      {
        id: nextId(),
        activityName: 'StartRound',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: mockSupportUser,
        info: { round_num: 1 }, // eslint-disable-line @typescript-eslint/camelcase
      },
      {
        id: nextId(),
        activityName: 'CreateAuditBoards',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: mockJurisdictionAdmin,
        info: {
          jurisdiction_id: 'jurisdiction-id-1', // eslint-disable-line @typescript-eslint/camelcase
          jurisdiction_name: 'Jurisdiction 1', // eslint-disable-line @typescript-eslint/camelcase
          num_audit_boards: 2, // eslint-disable-line @typescript-eslint/camelcase
        },
      },
      {
        id: nextId(),
        activityName: 'RecordResults',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: mockJurisdictionAdmin,
        info: {
          jurisdiction_id: 'jurisdiction-id-1', // eslint-disable-line @typescript-eslint/camelcase
          jurisdiction_name: 'Jurisdiction 1', // eslint-disable-line @typescript-eslint/camelcase
        },
      },
      {
        id: nextId(),
        activityName: 'AuditBoardSignOff',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: {
          key: 'audit-board-id-1',
          type: 'audit_board',
          supportUser: false,
        },
        info: {
          jurisdiction_id: 'jurisdiction-id-1', // eslint-disable-line @typescript-eslint/camelcase
          jurisdiction_name: 'Jurisdiction 1', // eslint-disable-line @typescript-eslint/camelcase
          audit_board_name: 'Audit Board #1', // eslint-disable-line @typescript-eslint/camelcase
        },
      },
      {
        id: nextId(),
        activityName: 'EndRound',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: {
          key: 'audit-board-id-1',
          type: 'audit_board',
          supportUser: false,
        },
        info: { round_num: 1, is_audit_complete: true }, // eslint-disable-line @typescript-eslint/camelcase
      },
      {
        id: nextId(),
        activityName: 'DeleteAudit',
        timestamp: nextTimestamp(),
        election: mockElection,
        user: mockAuditAdmin,
        info: {},
      },
    ].reverse(),
  },
}

const renderActivityLog = () =>
  renderWithRouter(
    <QueryClientProvider client={queryClient}>
      <AuthDataProvider>
        <PrivateRoute userType="audit_admin" component={ActivityLog} />
      </AuthDataProvider>
    </QueryClientProvider>
  )

describe('Activity Log', () => {
  it('shows a table of activity for the org', async () => {
    const expectedCalls = [aaApiCalls.getUser, apiCalls.getActivities]
    await withMockFetch(expectedCalls, async () => {
      renderActivityLog()
      await screen.findByRole('heading', { name: 'Activity Log' })
      expect(
        screen.getAllByRole('columnheader').map(h => h.textContent)
      ).toEqual(['Timestamp', 'User', 'Action', 'Audit', 'Jurisdiction'])
      expect(screen.getByRole('table')).toMatchSnapshot()
    })
  })

  it('has a dropdown for audit admins with multiple orgs', async () => {
    const expectedCalls = [
      aaApiCalls.getUserMultipleOrgs,
      apiCalls.getActivities,
      { url: '/api/organizations/org-id-2/activities', response: [] },
    ]
    await withMockFetch(expectedCalls, async () => {
      renderActivityLog()
      await screen.findByRole('heading', { name: 'Activity Log' })
      // Loads the first org by default
      const orgSelect = screen.getByLabelText(/Organization:/)
      expect(orgSelect).toHaveTextContent('State of California')
      expect(screen.getAllByRole('row')).toHaveLength(
        apiCalls.getActivities.response.length + 1
      )

      // Select a different org
      userEvent.selectOptions(orgSelect, 'State of Georgia')
      await waitFor(() => expect(screen.getAllByRole('row')).toHaveLength(1))
    })
  })

  it('has a button to download the activity table as a CSV', async () => {
    // JSDOM doesn't implement innerText, so we implement it using textContent
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      get() {
        return this.textContent
      },
      configurable: true,
    })
    const downloadFileMock = jest
      .spyOn(utilities, 'downloadFile')
      .mockImplementation()

    const expectedCalls = [
      aaApiCalls.getUserMultipleOrgs,
      apiCalls.getActivities,
    ]
    await withMockFetch(expectedCalls, async () => {
      renderActivityLog()
      await screen.findByRole('heading', { name: 'Activity Log' })
      userEvent.click(screen.getByRole('button', { name: /Download as CSV/ }))
      expect(downloadFileMock).toHaveBeenCalled()
      expect(downloadFileMock.mock.calls[0][1]).toMatch(
        /arlo-activity-State of California/
      )
      const fileBlob = downloadFileMock.mock.calls[0][0] as Blob
      expect(fileBlob.type).toEqual('text/csv')
      expect(await new Response(fileBlob).text()).toMatchInlineSnapshot(`
        "\\"Timestamp\\",\\"User\\",\\"Action\\",\\"Audit\\",\\"Jurisdiction\\"
        \\"8/31/2021, 11:03:49 PM\\",\\"admin@example.gov\\",\\"Deleted audit\\",\\"Test Audit\\",\\"\\"
        \\"8/31/2021, 11:02:49 PM\\",\\"\\",\\"Ended round 1\\",\\"Test Audit\\",\\"\\"
        \\"8/31/2021, 11:01:49 PM\\",\\"\\",\\"Audit Board #1 signed off\\",\\"Test Audit\\",\\"Jurisdiction 1\\"
        \\"8/31/2021, 11:00:49 PM\\",\\"admin@example.gov\\",\\"Recorded results\\",\\"Test Audit\\",\\"Jurisdiction 1\\"
        \\"8/31/2021, 10:59:49 PM\\",\\"admin@example.gov\\",\\"Created audit boards\\",\\"Test Audit\\",\\"Jurisdiction 1\\"
        \\"8/31/2021, 10:58:49 PM\\",\\"support@example.gov\\",\\"Started round 1\\",\\"Test Audit\\",\\"\\"
        \\"8/31/2021, 10:57:49 PM\\",\\"admin@example.gov\\",\\"Calculated sample sizes\\",\\"Test Audit\\",\\"\\"
        \\"8/31/2021, 10:56:49 PM\\",\\"\\",\\"Successfully uploaded CVRs\\",\\"Test Audit\\",\\"Jurisdiction 1\\"
        \\"8/31/2021, 10:55:49 PM\\",\\"\\",\\"Successfully uploaded candidate totals by batch\\",\\"Test Audit\\",\\"Jurisdiction 1\\"
        \\"8/31/2021, 10:54:49 PM\\",\\"\\",\\"Uploaded invalid ballot manifest\\",\\"Test Audit\\",\\"Jurisdiction 1\\"
        \\"8/31/2021, 10:53:49 PM\\",\\"admin@example.gov\\",\\"Created audit\\",\\"Test Audit\\",\\"\\""
      `)

      downloadFileMock.mockRestore()
      delete HTMLElement.prototype.innerText
    })
  })
})
