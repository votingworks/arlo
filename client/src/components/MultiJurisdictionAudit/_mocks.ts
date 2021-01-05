import { contestMocks } from './AASetup/Contests/_mocks'
import { IFileInfo } from './useCSV'
import {
  manifestFile,
  talliesFile,
  cvrsFile,
  auditBoardMocks,
} from './useSetupMenuItems/_mocks'
import { FileProcessingStatus } from './useSetupMenuItems/getJurisdictionFileStatus'
import { IBallot } from './RoundManagement/useBallots'
import { IAuditBoard } from './useAuditBoards'
import { IRound } from './useRoundsAuditAdmin'
import { IAuditSettings } from './useAuditSettings'

const manifestFormData: FormData = new FormData()
manifestFormData.append('manifest', manifestFile, manifestFile.name)
const talliesFormData: FormData = new FormData()
talliesFormData.append('batchTallies', talliesFile, talliesFile.name)
const cvrsFormData: FormData = new FormData()
cvrsFormData.append('cvrs', cvrsFile, cvrsFile.name)

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
    response: { user: null, superadminUser: null },
  },
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
            },
          },
          {
            id: 'jurisdiction-id-2',
            name: 'Jurisdiction Two',
            election: {
              id: '2',
              auditName: 'audit two',
              electionName: 'election two',
              state: 'AL',
            },
          },
          {
            id: 'jurisdiction-id-3',
            name: 'Jurisdiction Three',
            election: {
              id: '1',
              auditName: 'audit one',
              electionName: 'election one',
              state: 'AL',
            },
          },
        ],
        organizations: [],
      },
      superadminUser: null,
    },
  },
  getRounds: {
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/round',
    response: { rounds: [] },
  },
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
  getAuditBoards: (auditBoards: IAuditBoard[]) => ({
    url:
      '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/audit-board',
    response: { auditBoards },
  }),
  getBallots: (ballots: IBallot[]) => ({
    url: '/api/election/1/jurisdiction/jurisdiction-id-1/round/round-1/ballots',
    response: { ballots },
  }),
}

const aaUser = {
  type: 'audit_admin',
  name: 'Joe',
  email: 'auditadmin@email.org',
  jurisdictions: [],
  organizations: [
    {
      id: 'org-id',
      name: 'State of California',
      elections: [],
    },
  ],
}

export const aaApiCalls = {
  getUser: {
    url: '/api/me',
    response: {
      user: aaUser,
      superadminUser: null,
    },
  },
  getUserWithAudit: {
    url: '/api/me',
    response: {
      user: {
        ...aaUser,
        organizations: [
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
      },
      superadminUser: null,
    },
  },
  getUserMultipleOrgs: {
    url: '/api/me',
    response: {
      user: {
        ...aaUser,
        organizations: [
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
      },
      superadminUser: null,
    },
  },
  postNewAudit: (body: {}) => ({
    url: '/api/election',
    options: {
      method: 'POST',
      body: JSON.stringify(body),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    response: { electionId: '1' },
  }),
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
          ballotManifest: { file: null, processing: null },
          currentRoundStatus: null,
        },
        {
          id: 'jurisdiction-id-2',
          name: 'Jurisdiction Two',
          ballotManifest: { file: null, processing: null },
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
          ballotManifest: { file: null, processing: null },
          batchTallies: { file: null, processing: null },
          currentRoundStatus: null,
        },
        {
          id: 'jurisdiction-id-2',
          name: 'Jurisdiction Two',
          ballotManifest: { file: null, processing: null },
          batchTallies: { file: null, processing: null },
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
        uploadedAt: 'a long time ago in a galaxy far far away',
      },
      processing: {
        status: FileProcessingStatus.Processed,
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
    url: '/api/election/1/sample-sizes',
    response: { sampleSizes: null },
  },
}

export const superadminApiCalls = {
  getUser: {
    url: '/api/me',
    response: {
      user: null,
      superadminUser: { email: 'superadmin@example.com' },
    },
  },
  getUserImpersonatingAA: {
    url: '/api/me',
    response: {
      user: aaUser,
      superadminUser: { email: 'superadmin@example.com' },
    },
  },
  getUserImpersonatingJA: {
    url: '/api/me',
    response: {
      user: jaApiCalls.getUser.response.user,
      superadminUser: { email: 'superadmin@example.com' },
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
      superadminUser: null,
    },
  },
}
