/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
import { IFileInfo, FileProcessingStatus, CvrFileType } from './useCSV'
import { IAuditBoard } from './useAuditBoards'
import { IAuditSettings } from './useAuditSettings'
import {
  jurisdictionFile,
  standardizedContestsFile,
} from './AuditAdmin/Setup/Participants/_mocks'
import { IRound, ISampleSizes } from './AuditAdmin/useRoundsAuditAdmin'
import { IBallot } from './JurisdictionAdmin/useBallots'
import { IBatches } from './JurisdictionAdmin/useBatchResults'
import { IOrganization, ITallyEntryUser, IMember } from './UserContext'
import mapTopology from '../../public/us-states-counties.json'
import { IContest } from '../types'
import { INewAudit } from './HomeScreen'
import { mocksOfType } from './testUtilities'
import { ITallyEntryAccountStatus } from './JurisdictionAdmin/BatchRoundSteps/TallyEntryAccountsStep'
import {
  JurisdictionRoundStatus,
  ICvrFileInfo,
  IBallotManifestInfo,
  IBatchTalliesFileInfo,
  IJurisdiction,
} from './useJurisdictions'
import { IStandardizedContest } from './useStandardizedContests'
import { ISampleSizesResponse } from './AuditAdmin/Setup/Review/useSampleSizes'

export const manifestFile = new File(
  ['fake manifest - contents dont matter'],
  'manifest.csv',
  { type: 'text/csv' }
)
export const talliesFile = new File(
  ['fake tallies - contents dont matter'],
  'tallies.csv',
  { type: 'text/csv' }
)
export const cvrsFile = new File(
  ['fake cvrs - contents dont matter'],
  'cvrs.csv',
  { type: 'text/csv' }
)

export const auditSettingsMocks = mocksOfType<IAuditSettings>()({
  blank: {
    state: null,
    electionName: null,
    online: null,
    randomSeed: null,
    riskLimit: null,
    auditType: 'BALLOT_POLLING',
    auditMathType: 'BRAVO',
    auditName: 'Test Audit',
  },
  blankBatch: {
    state: null,
    electionName: null,
    online: null,
    randomSeed: null,
    riskLimit: null,
    auditType: 'BATCH_COMPARISON',
    auditMathType: 'MACRO',
    auditName: 'Test Audit',
  },
  blankBallotComparison: {
    state: null,
    electionName: null,
    online: true,
    randomSeed: null,
    riskLimit: null,
    auditType: 'BALLOT_COMPARISON',
    auditMathType: 'SUPERSIMPLE',
    auditName: 'Test Audit',
  },
  blankHybrid: {
    state: null,
    electionName: null,
    online: null,
    randomSeed: null,
    riskLimit: null,
    auditType: 'HYBRID',
    auditMathType: 'SUITE',
    auditName: 'Test Audit',
  },
  onlyState: {
    state: 'AL',
    electionName: null,
    online: null,
    randomSeed: null,
    riskLimit: null,
    auditType: 'BALLOT_POLLING',
    auditMathType: 'BRAVO',
    auditName: 'Test Audit',
  },
  otherSettings: {
    state: null,
    electionName: 'Election Name',
    online: true,
    randomSeed: '12345',
    riskLimit: 10,
    auditType: 'BALLOT_POLLING',
    auditMathType: 'BRAVO',
    auditName: 'Test Audit',
  },
  all: {
    state: 'AL',
    electionName: 'Election Name',
    online: true,
    randomSeed: '12345',
    riskLimit: 10,
    auditType: 'BALLOT_POLLING',
    auditMathType: 'BRAVO',
    auditName: 'Test Audit',
  },
  offlineAll: {
    state: 'AL',
    electionName: 'Election Name',
    online: false,
    randomSeed: '12345',
    riskLimit: 10,
    auditType: 'BALLOT_POLLING',
    auditMathType: 'BRAVO',
    auditName: 'Test Audit',
  },
  batchComparisonAll: {
    state: 'AL',
    electionName: 'Election Name',
    online: false,
    randomSeed: '12345',
    riskLimit: 10,
    auditType: 'BATCH_COMPARISON',
    auditMathType: 'MACRO',
    auditName: 'Test Audit',
  },
  ballotComparisonAll: {
    state: 'AL',
    electionName: 'Election Name',
    online: true,
    randomSeed: '12345',
    riskLimit: 10,
    auditType: 'BALLOT_COMPARISON',
    auditMathType: 'SUPERSIMPLE',
    auditName: 'Test Audit',
  },
  hybridAll: {
    state: 'AL',
    electionName: 'Election Name',
    online: false,
    randomSeed: '12345',
    riskLimit: 10,
    auditType: 'HYBRID',
    auditMathType: 'SUITE',
    auditName: 'Test Audit',
  },
})

export const roundMocks = mocksOfType<IRound[]>()({
  empty: [],
  singleIncomplete: [
    {
      endedAt: null,
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000+00:00',
      id: 'round-1',
      needsFullHandTally: false,
      isFullHandTally: false,
      drawSampleTask: {
        status: FileProcessingStatus.PROCESSED,
        startedAt: '2020-09-14T17:35:19.482Z',
        completedAt: '2020-09-14T17:36:19.482Z',
        error: null,
      },
    },
  ],
  twoIncomplete: [
    {
      endedAt: null,
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000+00:00',
      id: 'round-1',
      needsFullHandTally: false,
      isFullHandTally: false,
      drawSampleTask: {
        status: FileProcessingStatus.PROCESSED,
        startedAt: '2019-07-18T16:34:07.000+00:00',
        completedAt: '2019-07-18T16:35:07.000+00:00',
        error: null,
      },
    },
    {
      endedAt: null,
      roundNum: 2,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000+00:00',
      id: 'round-2',
      needsFullHandTally: false,
      isFullHandTally: false,
      drawSampleTask: {
        status: FileProcessingStatus.PROCESSED,
        startedAt: '2019-07-18T16:34:07.000+00:00',
        completedAt: '2019-07-18T16:35:07.000+00:00',
        error: null,
      },
    },
  ],
  singleComplete: [
    {
      endedAt: '2019-08-18T16:34:07.000+00:00',
      roundNum: 1,
      isAuditComplete: true,
      startedAt: '2019-07-18T16:34:07.000+00:00',
      id: 'round-1',
      needsFullHandTally: false,
      isFullHandTally: false,
      drawSampleTask: {
        status: FileProcessingStatus.PROCESSED,
        startedAt: '2019-07-18T16:34:07.000+00:00',
        completedAt: '2019-07-18T16:35:07.000+00:00',
        error: null,
      },
    },
  ],
  needAnother: [
    {
      endedAt: '2019-08-18T16:34:07.000+00:00',
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000+00:00',
      id: 'round-1',
      needsFullHandTally: false,
      isFullHandTally: false,
      drawSampleTask: {
        status: FileProcessingStatus.PROCESSED,
        startedAt: '2020-09-14T17:35:19.482Z',
        completedAt: '2020-09-14T17:36:19.482Z',
        error: null,
      },
    },
  ],
  drawSampleInProgress: [
    {
      endedAt: null,
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000+00:00',
      id: 'round-1',
      needsFullHandTally: false,
      isFullHandTally: false,
      drawSampleTask: {
        status: FileProcessingStatus.PROCESSING,
        startedAt: '2020-09-14T17:35:19.482Z',
        completedAt: null,
        error: null,
      },
    },
  ],
  drawSampleErrored: [
    {
      endedAt: null,
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000+00:00',
      id: 'round-1',
      needsFullHandTally: false,
      isFullHandTally: false,
      drawSampleTask: {
        status: FileProcessingStatus.ERRORED,
        startedAt: '2020-09-14T17:35:19.482Z',
        completedAt: '2020-09-14T17:36:19.482Z',
        error: 'something went wrong',
      },
    },
  ],
})

export const jurisdictionFileMocks = mocksOfType<IFileInfo>()({
  empty: {
    file: null,
    processing: null,
  },
  processed: {
    file: {
      name: 'jurisdictions.csv',
      uploadedAt: '2020-07-08T21:39:05.765+00:00',
    },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-07-08T21:39:05.765+00:00',
      completedAt: '2020-07-08T21:39:14.574+00:00',
      error: null,
    },
  },
  errored: {
    file: {
      name: 'jursidisctions.csv',
      uploadedAt: '2020-05-05T17:25:25.663592+00:00',
    },
    processing: {
      completedAt: '2020-05-05T17:25:26.09915+00:00',
      error: 'Invalid CSV',
      startedAt: '2020-05-05T17:25:26.09743+00:00',
      status: FileProcessingStatus.ERRORED,
    },
  },
})

export const standardizedContestsFileMocks = mocksOfType<IFileInfo>()({
  empty: {
    file: null,
    processing: null,
  },
  processed: {
    file: {
      name: 'standardized-contests.csv',
      uploadedAt: '2020-07-08T21:39:05.765+00:00',
    },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-07-08T21:39:05.765+00:00',
      completedAt: '2020-07-08T21:39:14.574+00:00',
      error: null,
    },
  },
  errored: {
    file: {
      name: 'standardized-contests.csv',
      uploadedAt: '2020-05-05T17:25:25.663592+00:00',
    },
    processing: {
      completedAt: '2020-05-05T17:25:26.09915+00:00',
      error: 'Invalid CSV',
      startedAt: '2020-05-05T17:25:26.09743+00:00',
      status: FileProcessingStatus.ERRORED,
    },
  },
})

export const manifestMocks = mocksOfType<IBallotManifestInfo>()({
  empty: {
    file: null,
    processing: null,
    numBatches: null,
    numBallots: null,
  },
  processing: {
    file: { name: 'manifest.csv', uploadedAt: '2020-06-08T21:39:05.765+00:00' },
    processing: {
      status: FileProcessingStatus.PROCESSING,
      startedAt: '2020-06-08T21:39:05.765+00:00',
      completedAt: null,
      error: null,
    },
    numBatches: null,
    numBallots: null,
  },
  processed: {
    file: { name: 'manifest.csv', uploadedAt: '2020-06-08T21:39:05.765+00:00' },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-06-08T21:39:05.765+00:00',
      completedAt: '2020-06-08T21:39:14.574+00:00',
      error: null,
    },
    numBatches: 10,
    numBallots: 2117,
  },
  errored: {
    file: {
      name: 'manifest.csv',
      uploadedAt: '2020-05-05T17:25:25.663592+00:00',
    },
    processing: {
      completedAt: '2020-05-05T17:25:26.09915+00:00',
      error: 'Invalid CSV',
      startedAt: '2020-05-05T17:25:26.09743+00:00',
      status: FileProcessingStatus.ERRORED,
    },
    numBallots: null,
    numBatches: null,
  },
})

export const talliesMocks = mocksOfType<IBatchTalliesFileInfo>()({
  empty: {
    file: null,
    processing: null,
    numBallots: null,
  },
  processing: {
    file: { name: 'tallies.csv', uploadedAt: '2020-07-08T21:39:05.765+00:00' },
    processing: {
      status: FileProcessingStatus.PROCESSING,
      startedAt: '2020-07-08T21:39:05.765+00:00',
      completedAt: null,
      error: null,
    },
    numBallots: null,
  },
  processed: {
    file: { name: 'tallies.csv', uploadedAt: '2020-07-08T21:39:05.765+00:00' },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-07-08T21:39:05.765+00:00',
      completedAt: '2020-07-08T21:39:14.574+00:00',
      error: null,
    },
    numBallots: 15,
  },
  errored: {
    file: {
      name: 'tallies.csv',
      uploadedAt: '2020-05-05T17:25:25.663592+00:00',
    },
    processing: {
      completedAt: '2020-05-05T17:25:26.09915+00:00',
      error: 'Invalid CSV',
      startedAt: '2020-05-05T17:25:26.09743+00:00',
      status: FileProcessingStatus.ERRORED,
    },
    numBallots: null,
  },
})

export const cvrsMocks = mocksOfType<ICvrFileInfo>()({
  empty: {
    file: null,
    processing: null,
    numBallots: null,
  },
  processing: {
    file: {
      name: 'cvrs.csv',
      uploadedAt: '2020-11-18T21:39:05.765+00:00',
      cvrFileType: CvrFileType.CLEARBALLOT,
    },
    processing: {
      status: FileProcessingStatus.PROCESSING,
      startedAt: '2020-11-18T21:39:05.765+00:00',
      completedAt: null,
      error: null,
      workProgress: 3,
      workTotal: 14,
    },
    numBallots: 10,
  },
  processed: {
    file: {
      name: 'cvrs.csv',
      uploadedAt: '2020-11-18T21:39:05.765+00:00',
      cvrFileType: CvrFileType.CLEARBALLOT,
    },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-11-18T21:39:05.765+00:00',
      completedAt: '2020-11-18T21:39:14.574+00:00',
      error: null,
      workProgress: 14,
      workTotal: 14,
    },
    numBallots: 10,
  },
  errored: {
    file: {
      name: 'cvrs.csv',
      uploadedAt: '2020-11-15T17:25:25.663592+00:00',
      cvrFileType: CvrFileType.CLEARBALLOT,
    },
    processing: {
      completedAt: '2020-11-15T17:25:26.09915+00:00',
      error: 'Invalid CSV',
      startedAt: '2020-11-15T17:25:26.09743+00:00',
      status: FileProcessingStatus.ERRORED,
    },
    numBallots: null,
  },
})

export const jurisdictionMocks = mocksOfType<IJurisdiction[]>()({
  empty: [],
  // Setup - Ballot polling
  noManifests: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.empty,
      expectedBallotManifestNumBallots: null,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.empty,
      expectedBallotManifestNumBallots: null,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.empty,
      expectedBallotManifestNumBallots: null,
      currentRoundStatus: null,
    },
  ],
  oneManifest: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.errored,
      expectedBallotManifestNumBallots: null,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.empty,
      expectedBallotManifestNumBallots: null,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      currentRoundStatus: null,
    },
  ],
  allManifests: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      currentRoundStatus: null,
    },
  ],
  // Setup - Batch comparison
  noManifestsNoTallies: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.empty,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.empty,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.empty,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
  ],
  twoManifestsOneTallies: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.errored,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: null,
    },
  ],
  allManifestsAllTallies: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: null,
    },
  ],
  // In progress - Batch comparison (can also be used for ballot polling)
  noneStarted: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.NOT_STARTED,
        numUniqueAudited: 0,
        numUnique: 10,
        numSamplesAudited: 0,
        numSamples: 11,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.NOT_STARTED,
        numUniqueAudited: 0,
        numUnique: 20,
        numSamplesAudited: 0,
        numSamples: 22,
      },
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 0,
        numUnique: 0,
        numSamplesAudited: 0,
        numSamples: 0,
      },
    },
  ],
  oneComplete: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.IN_PROGRESS,
        numUniqueAudited: 4,
        numUnique: 10,
        numSamplesAudited: 5,
        numSamples: 11,
        numDiscrepancies: null,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.NOT_STARTED,
        numUniqueAudited: 0,
        numUnique: 20,
        numSamplesAudited: 0,
        numSamples: 22,
        numDiscrepancies: null,
      },
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 30,
        numUnique: 30,
        numSamplesAudited: 31,
        numSamples: 31,
        numDiscrepancies: 1,
      },
    },
  ],
  allComplete: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 10,
        numUnique: 10,
        numSamplesAudited: 11,
        numSamples: 11,
        numDiscrepancies: 0,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 20,
        numUnique: 20,
        numSamplesAudited: 22,
        numSamples: 22,
        numDiscrepancies: 2,
      },
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 30,
        numUnique: 30,
        numSamplesAudited: 31,
        numSamples: 31,
        numDiscrepancies: 1,
      },
    },
  ],
  // Ballot comparison
  allManifestsSomeCVRs: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.empty,
      currentRoundStatus: null,
    },
  ],
  allManifestsWithCVRs: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.processed,
      currentRoundStatus: null,
    },
  ],
  noneStartedBallotComparison: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.NOT_STARTED,
        numUniqueAudited: 0,
        numUnique: 10,
        numSamplesAudited: 0,
        numSamples: 11,
        numDiscrepancies: null,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.NOT_STARTED,
        numUniqueAudited: 0,
        numUnique: 20,
        numSamplesAudited: 0,
        numSamples: 22,
        numDiscrepancies: null,
      },
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 30,
        numUnique: 30,
        numSamplesAudited: 31,
        numSamples: 31,
        numDiscrepancies: 0,
      },
    },
  ],
  // Hybrid
  hybridTwoManifestsOneCvr: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: {
        ...manifestMocks.processed,
        numBallotsCvr: 2000,
        numBallotsNonCvr: 117,
      },
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: {
        ...manifestMocks.processed,
        numBallotsCvr: 1000,
        numBallotsNonCvr: 1117,
      },
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.empty,
      expectedBallotManifestNumBallots: null,
      cvrs: cvrsMocks.empty,
      currentRoundStatus: null,
    },
  ],
  uploadingWithAlabamaJurisdictions: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jackson',
      ballotManifest: manifestMocks.errored,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Baldwin',
      ballotManifest: manifestMocks.empty,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Geneva',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
  ],
  allCompleteWithAlabamaJurisdictions: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jackson',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 10,
        numUnique: 10,
        numSamplesAudited: 11,
        numSamples: 11,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Baldwin County',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 20,
        numUnique: 20,
        numSamplesAudited: 22,
        numSamples: 22,
      },
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Geneva',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 30,
        numUnique: 30,
        numSamplesAudited: 31,
        numSamples: 31,
      },
    },
  ],
  allCompleteWithOneMatchedAlabamaJurisdictions: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 10,
        numUnique: 10,
        numSamplesAudited: 11,
        numSamples: 11,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 20,
        numUnique: 20,
        numSamplesAudited: 22,
        numSamples: 22,
      },
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Geneva',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 30,
        numUnique: 30,
        numSamplesAudited: 31,
        numSamples: 31,
      },
    },
  ],
  allCompleteWithTwoMatchedAlabamaJurisdictions: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 10,
        numUnique: 10,
        numSamplesAudited: 11,
        numSamples: 11,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Baldwin County',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 20,
        numUnique: 20,
        numSamplesAudited: 22,
        numSamples: 22,
      },
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Geneva',
      ballotManifest: manifestMocks.processed,
      expectedBallotManifestNumBallots: null,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numUniqueAudited: 30,
        numUnique: 30,
        numSamplesAudited: 31,
        numSamples: 31,
      },
    },
  ],
})

export const contestMocks = mocksOfType<IContest[]>()({
  empty: [],
  oneTargeted: [
    {
      id: 'contest-id-1',
      name: 'Contest 1',
      isTargeted: true,
      totalBallotsCast: 30,
      numWinners: 1,
      votesAllowed: 1,
      jurisdictionIds: [
        'jurisdiction-id-1',
        'jurisdiction-id-2',
        'jurisdiction-id-3',
      ],
      choices: [
        {
          id: 'choice-id-1',
          name: 'Choice One',
          numVotes: 10,
        },
        {
          id: 'choice-id-2',
          name: 'Choice Two',
          numVotes: 20,
        },
      ],
    },
    {
      id: 'contest-id-2',
      name: 'Contest 2',
      isTargeted: false,
      totalBallotsCast: 400,
      numWinners: 2,
      votesAllowed: 2,
      jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
      choices: [
        {
          id: 'choice-id-3',
          name: 'Choice Three',
          numVotes: 300,
        },
        {
          id: 'choice-id-4',
          name: 'Choice Four',
          numVotes: 100,
        },
      ],
    },
  ],
  filledTargeted: [
    {
      id: 'contest-id',
      name: 'Contest Name',
      isTargeted: true,
      numWinners: 1,
      votesAllowed: 1,
      jurisdictionIds: [jurisdictionMocks.noManifests[0].id],
      choices: [
        {
          id: 'choice-id-1',
          name: 'Choice One',
          numVotes: 10,
        },
        {
          id: 'choice-id-2',
          name: 'Choice Two',
          numVotes: 20,
        },
      ],
      totalBallotsCast: 30,
    },
  ],
  filledOpportunistic: [
    {
      id: 'contest-id',
      name: 'Contest Name',
      isTargeted: false,
      totalBallotsCast: 30,
      numWinners: 1,
      votesAllowed: 1,
      jurisdictionIds: [],
      choices: [
        {
          id: 'choice-id-3',
          name: 'Choice Three',
          numVotes: 10,
        },
        {
          id: 'choice-id-4',
          name: 'Choice Four',
          numVotes: 20,
        },
      ],
    },
  ],
  filledTargetedWithJurisdictionId: [
    {
      id: 'contest-id',
      name: 'Contest Name',
      isTargeted: true,
      totalBallotsCast: 30,
      numWinners: 1,
      votesAllowed: 1,
      jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
      choices: [
        {
          id: 'choice-id-1',
          name: 'Choice One',
          numVotes: 10,
        },
        {
          id: 'choice-id-2',
          name: 'Choice Two',
          numVotes: 20,
        },
      ],
    },
  ],
  filledOpportunisticWithJurisdictionId: [
    {
      id: 'contest-id',
      name: 'Contest Name',
      isTargeted: false,
      totalBallotsCast: 30,
      numWinners: 1,
      votesAllowed: 1,
      jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
      choices: [
        {
          id: 'choice-id-3',
          name: 'Choice Three',
          numVotes: 10,
        },
        {
          id: 'choice-id-4',
          name: 'Choice Four',
          numVotes: 20,
        },
      ],
    },
  ],
  filledTargetedAndOpportunistic: [
    {
      id: 'contest-id',
      name: 'Contest 1',
      isTargeted: true,
      totalBallotsCast: 30,
      numWinners: 1,
      votesAllowed: 1,
      jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
      choices: [
        {
          id: 'choice-id-1',
          name: 'Choice One',
          numVotes: 10,
          numVotesCvr: 6,
          numVotesNonCvr: 4,
        },
        {
          id: 'choice-id-2',
          name: 'Choice Two',
          numVotes: 20,
          numVotesCvr: 12,
          numVotesNonCvr: 8,
        },
      ],
    },
    {
      id: 'contest-id-2',
      name: 'Contest 2',
      isTargeted: false,
      totalBallotsCast: 300000,
      numWinners: 2,
      votesAllowed: 2,
      jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
      choices: [
        {
          id: 'choice-id-3',
          name: 'Choice Three',
          numVotes: 10,
          numVotesCvr: 6,
          numVotesNonCvr: 4,
        },
        {
          id: 'choice-id-4',
          name: 'Choice Four',
          numVotes: 20,
          numVotesCvr: 12,
          numVotesNonCvr: 8,
        },
      ],
    },
  ],
})

export const fileProcessingMocks = mocksOfType<IFileInfo['processing']>()({
  null: null,
  processed: {
    status: FileProcessingStatus.PROCESSED,
    startedAt: '2019-07-18T16:34:07.000+00:00',
    completedAt: '2019-07-18T16:35:07.000+00:00',
    error: null,
  },
  errored: {
    status: FileProcessingStatus.ERRORED,
    startedAt: '2019-07-18T16:34:07.000+00:00',
    completedAt: '2019-07-18T16:35:07.000+00:00',
    error: 'something went wrong',
  },
})

export const auditBoardMocks = mocksOfType<IAuditBoard[]>()({
  empty: [],
  unfinished: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: null,
      passphrase: 'happy-rebel-base',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 0,
      },
    },
  ],
  finished: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: null,
      passphrase: 'happy-rebel-base',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 30,
      },
    },
  ],
  single: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: null,
      passphrase: 'happy-randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 0,
      },
    },
  ],
  double: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: null,
      passphrase: 'happy-randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 0,
      },
    },
    {
      id: 'audit-board-2',
      name: 'Audit Board #02',
      signedOffAt: null,
      passphrase: 'happy-secondary-randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 0,
      },
    },
  ],
  noBallots: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: null,
      passphrase: 'happy-randomness',
      currentRoundStatus: {
        numSampledBallots: 0,
        numAuditedBallots: 0,
      },
    },
    {
      id: 'audit-board-2',
      name: 'Audit Board #02',
      signedOffAt: null,
      passphrase: 'happy-secondary-randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 0,
      },
    },
    {
      id: 'audit-board-3',
      name: 'Audit Board #03',
      signedOffAt: null,
      passphrase: 'happy-tertiary-randomness',
      currentRoundStatus: {
        numSampledBallots: 0,
        numAuditedBallots: 0,
      },
    },
  ],
  started: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: null,
      passphrase: 'happy-randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 15,
      },
    },
  ],
  signedOff: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: '2019-07-18T16:34:07.000+00:00',
      passphrase: 'happy-randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 30,
      },
    },
  ],
})

const jurisdictionFormData: FormData = new FormData()
jurisdictionFormData.append(
  'jurisdictions',
  jurisdictionFile,
  jurisdictionFile.name
)
const jurisdictionErrorFormData: FormData = new FormData()
jurisdictionErrorFormData.append(
  'jurisdictions',
  jurisdictionFile,
  jurisdictionFile.name
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
  postRound: (sampleSizes: ISampleSizes) => ({
    url: '/api/election/1/round',
    response: { status: 'ok' },
    options: {
      body: JSON.stringify({
        roundNum: 1,
        sampleSizes,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
      method: 'POST',
    },
  }),
  postFinishRound: {
    url: '/api/election/1/round/current/finish',
    options: { method: 'POST' },
    response: { status: 'ok' },
  },
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
  getStandardizedContestsFile: (response: IFileInfo | null) => ({
    url: '/api/election/1/standardized-contests/file',
    response,
  }),
  getContests: (contests: IContest[]) => ({
    url: '/api/election/1/contest',
    response: { contests },
  }),
  putContests: (contests: IContest[]) => ({
    url: '/api/election/1/contest',
    options: {
      method: 'PUT',
      body: JSON.stringify(contests),
      headers: {
        'Content-Type': 'application/json',
      },
    },
    response: { status: 'ok' },
  }),
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
  getStandardizedContests: (
    standardizedContests: IStandardizedContest[] | null
  ) => ({
    url: '/api/election/1/standardized-contests',
    response: standardizedContests,
  }),
  getSampleSizes: (response: ISampleSizesResponse) => ({
    url: '/api/election/1/sample-sizes/1',
    response,
  }),
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
