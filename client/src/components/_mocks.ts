/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
import { IFileInfo, FileProcessingStatus } from './useCSV'
import { IAuditBoard } from './useAuditBoards'
import { IAuditSettings } from './useAuditSettings'
import {
  jurisdictionFile,
  jurisdictionErrorFile,
  standardizedContestsFile,
} from './AuditAdmin/Setup/Participants/_mocks'
import {
  manifestFile,
  talliesFile,
  cvrsFile,
} from './AuditAdmin/useSetupMenuItems/_mocks'
import { IRound } from './AuditAdmin/useRoundsAuditAdmin'
import { IBallot } from './JurisdictionAdmin/useBallots'
import { IBatches } from './JurisdictionAdmin/useBatchResults'
import { IOrganization, ITallyEntryUser, IMember } from './UserContext'
import mapTopology from '../../public/us-states-counties.json'
import { contestMocks } from './AuditAdmin/Setup/Contests/_mocks'
import { IContest } from '../types'
import { INewAudit } from './HomeScreen'
import { mocksOfType } from './testUtilities'
import { ITallyEntryAccountStatus } from './JurisdictionAdmin/BatchRoundSteps/TallyEntryAccountsStep'

const jurisdictionFormData: FormData = new FormData()
jurisdictionFormData.append(
  'jurisdictions',
  jurisdictionFile,
  jurisdictionFile.name
)
const jurisdictionErrorFormData: FormData = new FormData()
jurisdictionErrorFormData.append(
  'jurisdictions',
  jurisdictionErrorFile,
  jurisdictionErrorFile.name
)
const standardizedContestsFormData: FormData = new FormData()
standardizedContestsFormData.append(
  'standardized-contests',
  standardizedContestsFile,
  standardizedContestsFile.name
)

const manifestFormData: FormData = new FormData()
manifestFormData.append('manifest', manifestFile, manifestFile.name)
const talliesFormData: FormData = new FormData()
talliesFormData.append('batchTallies', talliesFile, talliesFile.name)
const cvrsFormData: FormData = new FormData()
// Make the mock CVR file large enough to trigger an "Uploading..." progress bar
Object.defineProperty(cvrsFile, 'size', { value: 1000 * 1000 })
cvrsFormData.append('cvrs', cvrsFile, cvrsFile.name)
cvrsFormData.append('cvrFileType', 'CLEARBALLOT')

export const apiCalls = {
  serverError: (
    url: string,
    error = { status: 500, statusText: 'Server Error' }
  ) => ({
    url,
    response: {
      errors: [{ errorType: 'Server Error', message: error.statusText }],
    },
    error,
  }),
  unauthenticatedUser: {
    url: '/api/me',
    response: { user: null, supportUser: null },
  },
  requestJALoginCode: (email: string) => ({
    url: '/auth/jurisdictionadmin/code',
    options: {
      method: 'POST',
      headers: { 'Content-type': 'application/json' },
      body: JSON.stringify({ email }),
    },
    response: { status: 'ok' },
  }),
  enterJALoginCode: (email: string, code: string) => ({
    url: '/auth/jurisdictionadmin/login',
    options: {
      method: 'POST',
      headers: { 'Content-type': 'application/json' },
      body: JSON.stringify({ email, code }),
    },
    response: { status: 'ok' },
  }),
}

export const jaApiCalls = {
  getUser: {
    url: '/api/me',
    response: {
      user: {
        type: 'jurisdiction_admin',
        name: 'Joe',
        email: 'jurisdictionadmin@email.org',
        jurisdictions: [
          {
            id: 'jurisdiction-id-1',
            name: 'Jurisdiction One',
            election: {
              id: '1',
              auditName: 'audit one',
              electionName: 'election one',
              state: 'AL',
              organizationId: 'org-id',
            },
            numBallots: 100,
          },
          {
            id: 'jurisdiction-id-2',
            name: 'Jurisdiction Two',
            election: {
              id: '2',
              auditName: 'audit two',
              electionName: 'election two',
              state: 'AL',
              organizationId: 'org-id',
            },
            numBallots: 200,
          },
          {
            id: 'jurisdiction-id-3',
            name: 'Jurisdiction Three',
            election: {
              id: '1',
              auditName: 'audit one',
              electionName: 'election one',
              state: 'AL',
              organizationId: 'org-id',
            },
            numBallots: 300,
          },
        ],
        organizations: [],
      },
      supportUser: null,
    },
  },
  getUserWithOneElection: {
    url: '/api/me',
    response: {
      user: {
        type: 'jurisdiction_admin',
        name: 'Joe',
        email: 'jurisdictionadmin@email.org',
        jurisdictions: [
          {
            id: 'jurisdiction-id-1',
            name: 'Jurisdiction One',
            election: {
              id: '1',
              auditName: 'audit one',
              electionName: 'election one',
              state: 'AL',
              organizationId: 'org-id',
            },
          },
        ],
        organizations: [],
      },
      supportUser: null,
    },
  },
  getUserWithoutElections: {
    url: '/api/me',
    response: {
      user: {
        type: 'jurisdiction_admin',
        name: 'Joe',
        email: 'jurisdictionadmin@email.org',
        jurisdictions: [],
        organizations: [],
      },
      supportUser: null,
    },
  },
  getRounds: (rounds: IRound[]) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/round',
    response: { rounds },
  }),
  getBallotManifestFile: (response: IFileInfo) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/ballot-manifest',
    response,
  }),
  getBatchTalliesFile: (response: IFileInfo) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/batch-tallies',
    response,
  }),
  getCVRSfile: (response: IFileInfo) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/cvrs',
    response,
  }),
  getSettings: (response: IAuditSettings) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/settings',
    response,
  }),
  putManifest: {
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/ballot-manifest',
    options: {
      method: 'PUT',
      body: manifestFormData,
    },
    response: { status: 'ok' },
  },
  putTallies: {
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/batch-tallies',
    options: {
      method: 'PUT',
      body: talliesFormData,
    },
    response: { status: 'ok' },
  },
  putCVRs: {
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/cvrs',
    options: {
      method: 'PUT',
      body: cvrsFormData,
    },
    response: { status: 'ok' },
  },
  deleteCVRs: {
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/cvrs',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
  getAuditBoards: (auditBoards: IAuditBoard[]) => ({
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/audit-board',
    response: { auditBoards },
  }),
  getBallots: (ballots: IBallot[]) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/ballots',
    response: { ballots },
  }),
  getBallotCount: (ballots: IBallot[]) => ({
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/ballots?count=true',
    response: { count: ballots.length },
  }),
  getBatches: (batches: IBatches) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/batches',
    response: batches,
  }),
  finalizeBatchResults: {
    url: `/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/batches/finalize`,
    options: { method: 'POST' },
    response: { status: 'ok' },
  },
  unfinalizeBatchResults: {
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/batches/finalize',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
  deleteManifest: {
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/ballot-manifest',
    options: {
      method: 'DELETE',
    },
    response: { status: 'ok' },
  },
  deleteTallies: {
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/batch-tallies',
    options: {
      method: 'DELETE',
    },
    response: { status: 'ok' },
  },
  getJurisdictionContests: (contests: IContest[]) => ({
    url: `/api/election/1/jurisdiction/jurisdiction-id-1/contest`,
    response: { contests },
  }),
  getTallyEntryAccountStatus: (status: ITallyEntryAccountStatus) => ({
    url: `/auth/tallyentry/election/1/jurisdiction/jurisdiction-id-1`,
    response: status,
  }),
  postTurnOnTallyEntryAccounts: {
    url: `/auth/tallyentry/election/1/jurisdiction/jurisdiction-id-1`,
    options: {
      method: 'POST',
    },
    response: { status: 'ok' },
  },
  postConfirmTallyEntryLoginCode: {
    url: `/auth/tallyentry/election/1/jurisdiction/jurisdiction-id-1/confirm`,
    options: {
      method: 'POST',
      body: JSON.stringify({
        tallyEntryUserId: 'tally-entry-user-id-1',
        loginCode: '123',
      }),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  },
  postRejectTallyEntryLoginRequest: {
    url: `/auth/tallyentry/election/1/jurisdiction/jurisdiction-id-1/reject`,
    options: {
      method: 'POST',
      body: JSON.stringify({
        tallyEntryUserId: 'tally-entry-user-id-2',
      }),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  },
}

export const mockOrganizations = {
  oneOrgNoAudits: [
    {
      id: 'org-id',
      name: 'State of California',
      elections: [],
    },
  ],
  oneOrgOneAudit: [
    {
      id: 'org-id',
      name: 'State of California',
      elections: [
        {
          id: '1',
          auditName: 'November Presidential Election 2020',
          electionName: '',
          state: 'CA',
        },
      ],
    },
  ],
  twoOrgs: [
    {
      id: 'org-id',
      name: 'State of California',
      elections: [
        {
          id: '1',
          auditName: 'November Presidential Election 2020',
          electionName: '',
          state: 'CA',
        },
      ],
    },
    {
      id: 'org-id-2',
      name: 'State of Georgia',
      elections: [],
    },
  ],
}

export const aaApiCalls = {
  getUser: {
    url: '/api/me',
    response: {
      user: {
        type: 'audit_admin',
        email: 'auditadmin@email.org',
        id: 'audit-admin-1-id',
      },
      supportUser: null,
    },
  },
  getOrganizations: (organizations: IOrganization[]) => ({
    url: '/api/audit_admins/audit-admin-1-id/organizations',
    response: organizations,
  }),
  postNewAudit: (newAudit: INewAudit) => ({
    url: '/api/election',
    options: {
      method: 'POST',
      body: JSON.stringify(newAudit),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    response: { electionId: '1' },
  }),
  deleteAudit: {
    url: '/api/election/1',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
  getRounds: (rounds: IRound[]) => ({
    url: '/api/election/1/round',
    response: { rounds },
  }),
  getJurisdictions: {
    url: '/api/election/1/jurisdiction',
    response: {
      jurisdictions: [
        {
          id: 'jurisdiction-id-1',
          name: 'Jurisdiction One',
          ballotManifest: {
            file: null,
            processing: null,
            numBallots: null,
            numBatches: null,
          },
          currentRoundStatus: null,
        },
        {
          id: 'jurisdiction-id-2',
          name: 'Jurisdiction Two',
          ballotManifest: {
            file: null,
            processing: null,
            numBallots: null,
            numBatches: null,
          },
          currentRoundStatus: null,
        },
      ],
    },
  },
  getBatchJurisdictions: {
    url: '/api/election/1/jurisdiction',
    response: {
      jurisdictions: [
        {
          id: 'jurisdiction-id-1',
          name: 'Jurisdiction One',
          ballotManifest: {
            file: null,
            processing: null,
            numBallots: null,
            numBatches: null,
          },
          batchTallies: { file: null, processing: null, numBallots: null },
          currentRoundStatus: null,
        },
        {
          id: 'jurisdiction-id-2',
          name: 'Jurisdiction Two',
          ballotManifest: {
            file: null,
            processing: null,
            numBallots: null,
            numBatches: null,
          },
          batchTallies: { file: null, processing: null, numBallots: null },
          currentRoundStatus: null,
        },
      ],
    },
  },
  getJurisdictionFile: {
    url: '/api/election/1/jurisdiction/file',
    response: {
      file: {
        name: 'file name',
        uploadedAt: '2020-12-04T02:31:15.419+00:00',
      },
      processing: {
        status: FileProcessingStatus.PROCESSED,
        error: null,
        startedAt: '2020-12-04T02:32:15.419+00:00',
        completedAt: '2020-12-04T02:32:15.419+00:00',
      },
    },
  },
  getStandardizedContestsFile: {
    url: '/api/election/1/standardized-contests/file',
    response: { file: null, processing: null },
  },
  getContests: {
    url: '/api/election/1/contest',
    response: contestMocks.filledTargeted,
  },
  getSettings: (response: IAuditSettings) => ({
    url: '/api/election/1/settings',
    response,
  }),
  putSettings: (settings: IAuditSettings) => ({
    url: '/api/election/1/settings',
    options: {
      method: 'PUT',
      body: JSON.stringify(settings),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  }),
  getSampleSizes: {
    url: '/api/election/1/sample-sizes/1',
    response: {
      sampleSizes: null,
      selected: null,
      task: {
        status: 'READY_TO_PROCESS',
        startedAt: null,
        completedAt: null,
        error: null,
      },
    },
  },
  putJurisdictionFile: {
    url: '/api/election/1/jurisdiction/file',
    options: {
      method: 'PUT',
      body: jurisdictionFormData,
    },
    response: { status: 'ok' },
  },
  putJurisdictionErrorFile: {
    url: '/api/election/1/jurisdiction/file',
    options: {
      method: 'PUT',
      body: jurisdictionErrorFormData,
    },
    response: { status: 'ok' },
  },
  getJurisdictionFileWithResponse: (response: IFileInfo) => ({
    url: '/api/election/1/jurisdiction/file',
    response,
  }),
  putStandardizedContestsFile: {
    url: '/api/election/1/standardized-contests/file',
    options: {
      method: 'PUT',
      body: standardizedContestsFormData,
    },
    response: { status: 'ok' },
  },
  getStandardizedContestsFileWithResponse: (response: IFileInfo) => ({
    url: '/api/election/1/standardized-contests/file',
    response,
  }),
  getMapData: {
    url: '/us-states-counties.json',
    response: mapTopology,
  },
  reopenAuditBoard: {
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/audit-board/audit-board-1/sign-off',
    options: { method: 'DELETE' },
    response: { status: 'ok' },
  },
}

export const supportApiCalls = {
  getUser: {
    url: '/api/me',
    response: {
      user: null,
      supportUser: { email: 'support@example.com' },
    },
  },
  getUserImpersonatingAA: {
    url: '/api/me',
    response: {
      user: aaApiCalls.getUser.response.user,
      supportUser: { email: 'support@example.com' },
    },
  },
  getUserImpersonatingJA: {
    url: '/api/me',
    response: {
      user: jaApiCalls.getUser.response.user,
      supportUser: { email: 'support@example.com' },
    },
  },
}

export const auditBoardApiCalls = {
  getUser: {
    url: '/api/me',
    response: {
      user: {
        type: 'audit_board',
        id: 'audit-board-1',
        name: 'Audit Board #1',
        jurisdictionId: 'jurisdiction-1',
        jurisdictionName: 'Jurisdiction 1',
        roundId: 'round-1',
        members: [
          {
            name: 'John Doe',
            affiliation: '',
          },
          {
            name: 'Jane Doe',
            affiliation: 'LIB',
          },
        ],
        signedOffAt: null,
      },
      supportUser: null,
    },
  },
}

export const tallyEntryUser = mocksOfType<ITallyEntryUser>()({
  initial: {
    type: 'tally_entry',
    id: 'tally-entry-user-1',
    jurisdictionId: 'jurisdiction-id-1',
    jurisdictionName: 'Jurisdiction One',
    electionId: '1',
    auditName: 'Test Audit',
    roundId: 'round-1',
    loginCode: null,
    loginConfirmedAt: null,
    members: [],
  },
  unconfirmed: {
    type: 'tally_entry',
    id: 'tally-entry-user-1',
    jurisdictionId: 'jurisdiction-id-1',
    jurisdictionName: 'Jurisdiction One',
    electionId: '1',
    auditName: 'Test Audit',
    roundId: 'round-1',
    loginCode: '123',
    loginConfirmedAt: null,
    members: [
      {
        name: 'John Doe',
        affiliation: 'DEM',
      },
      { name: 'Jane Doe', affiliation: null },
    ],
  },
  confirmed: {
    type: 'tally_entry',
    id: 'tally-entry-user-1',
    jurisdictionId: 'jurisdiction-id-1',
    jurisdictionName: 'Jurisdiction One',
    electionId: '1',
    auditName: 'Test Audit',
    roundId: 'round-1',
    loginCode: '123',
    loginConfirmedAt: '2022-10-17T21:12:42.600Z',
    members: [
      {
        name: 'John Doe',
        affiliation: 'DEM',
      },
      { name: 'Jane Doe', affiliation: null },
    ],
  },
})

export const tallyEntryApiCalls = {
  getUser: (user: ITallyEntryUser) => ({
    url: '/api/me',
    response: {
      user,
      supportUser: null,
    },
  }),
  postRequestLoginCode: (body: { members: IMember[] }) => ({
    url: '/auth/tallyentry/code',
    options: {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
    response: { status: 'ok' },
  }),
  getBatches: jaApiCalls.getBatches,
  getContests: jaApiCalls.getJurisdictionContests,
}

export const fileInfoMocks = mocksOfType<IFileInfo>()({
  empty: { file: null, processing: null },
  processing: {
    file: {
      name: 'test-file.csv',
      uploadedAt: '2020-06-08T21:39:05.765+00:00',
    },
    processing: {
      status: FileProcessingStatus.PROCESSING,
      startedAt: '2020-06-08T21:39:05.765+00:00',
      completedAt: null,
      error: null,
      workProgress: 1,
      workTotal: 2,
    },
  },
  processed: {
    file: {
      name: 'test-file.csv',
      uploadedAt: '2020-06-08T21:39:05.765+00:00',
    },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-06-08T21:39:05.765+00:00',
      completedAt: '2020-06-08T21:40:05.765+00:00',
      error: null,
    },
  },
  errored: {
    file: {
      name: 'test-file.csv',
      uploadedAt: '2020-06-08T21:39:05.765+00:00',
    },
    processing: {
      status: FileProcessingStatus.ERRORED,
      startedAt: '2020-06-08T21:39:05.765+00:00',
      completedAt: '2020-06-08T21:40:05.765+00:00',
      error: 'something went wrong',
    },
  },
})
