import { contestMocks } from './AASetup/Contests/_mocks'
import { IFileInfo } from './useJurisdictions'
import {
  auditSettings,
  manifestFile,
  talliesFile,
} from './useSetupMenuItems/_mocks'
import { FileProcessingStatus } from './useSetupMenuItems/getJurisdictionFileStatus'
import { IAuditSettings } from '../../types'
import { IBallot } from './RoundManagement/useBallots'
import { IAuditBoard } from './useAuditBoards'
import { IStandardizedContest } from './useStandardizedContests'

const manifestFormData: FormData = new FormData()
manifestFormData.append('manifest', manifestFile, manifestFile.name)
const talliesFormData: FormData = new FormData()
talliesFormData.append('batchTallies', talliesFile, talliesFile.name)

export const jaApiCalls = {
  getUser: {
    url: '/api/me',
    response: {
      type: 'jurisdiction_admin',
      name: 'Joe',
      email: 'test@email.org',
      jurisdictions: [
        {
          id: 'jurisdiction-id-1',
          name: 'Jurisdiction One',
          election: {
            id: '1',
            auditName: 'audit one',
            electionName: 'election one',
            state: 'AL',
            isMultiJurisdiction: true,
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
            isMultiJurisdiction: true,
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
            isMultiJurisdiction: true,
          },
        },
      ],
      organizations: [],
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

export const aaApiCalls = {
  getUser: {
    url: '/api/me',
    response: {
      type: 'audit_admin',
      name: 'Joe',
      email: 'test@email.org',
      jurisdictions: [],
      organizations: [
        {
          id: 'org-id',
          name: 'State of California',
          elections: [],
        },
      ],
    },
  },
  getRounds: {
    url: '/api/election/1/round',
    response: { rounds: [] },
  },
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
        contents: null,
        name: 'file name',
        uploadedAt: 'a long time ago in a galaxy far far away',
      },
      processing: {
        status: FileProcessingStatus.Processed,
        error: null,
        startedAt: 'once upon a time',
        endedAt: 'and they lived happily ever after',
      },
    },
  },
  getContests: {
    url: '/api/election/1/contest',
    response: contestMocks.filledTargeted,
  },
  getSettings: (response: IAuditSettings) => ({
    url: '/api/election/1/settings',
    response,
  }),
  putSettings: {
    url: '/api/election/1/settings',
    options: {
      method: 'PUT',
      body: JSON.stringify(auditSettings.all),
      headers: { 'Content-Type': 'application/json' },
    },
    response: { status: 'ok' },
  },
  getSampleSizes: {
    url: '/api/election/1/sample-sizes',
    response: { sampleSizes: null },
  },
}
