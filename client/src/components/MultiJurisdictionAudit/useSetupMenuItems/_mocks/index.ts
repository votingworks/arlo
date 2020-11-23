import { readFileSync } from 'fs'
import { join } from 'path'
import { IAuditSettings, IContest } from '../../../../types'
import {
  IJurisdiction,
  FileProcessingStatus,
  IFileInfo,
  JurisdictionRoundStatus,
  IBallotManifestInfo,
} from '../../useJurisdictions' // uses IFileInfo instead of IBallotManifest and allows `file: null`
import { IAuditBoard } from '../../useAuditBoards'
import { IRound } from '../../useRoundsAuditAdmin'

export const manifestFile = new File(
  [readFileSync(join(__dirname, './test_manifest.csv'), 'utf8')],
  'manifest.csv',
  { type: 'text/csv' }
)
export const talliesFile = new File(
  [readFileSync(join(__dirname, './test_batch_tallies.csv'), 'utf8')],
  'tallies.csv',
  { type: 'text/csv' }
)

export const auditSettings: {
  [key in
    | 'blank'
    | 'blankBatch'
    | 'onlyState'
    | 'otherSettings'
    | 'all'
    | 'offlineAll'
    | 'batchComparisonAll']: IAuditSettings
} = {
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
    auditMathType: 'BRAVO',
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
    auditMathType: 'BRAVO',
    auditName: 'Test Audit',
  },
}

export const roundMocks: {
  [key in
    | 'empty'
    | 'singleIncomplete'
    | 'twoIncomplete'
    | 'singleComplete'
    | 'needAnother']: IRound[]
} = {
  empty: [],
  singleIncomplete: [
    {
      endedAt: null,
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000',
      id: 'round-1',
      sampledAllBallots: false,
    },
  ],
  twoIncomplete: [
    {
      endedAt: null,
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000',
      id: 'round-1',
      sampledAllBallots: false,
    },
    {
      endedAt: null,
      roundNum: 2,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000',
      id: 'round-2',
      sampledAllBallots: false,
    },
  ],
  singleComplete: [
    {
      endedAt: 'a time most proper',
      roundNum: 1,
      isAuditComplete: true,
      startedAt: '2019-07-18T16:34:07.000',
      id: 'round-1',
      sampledAllBallots: false,
    },
  ],
  needAnother: [
    {
      endedAt: 'a time most proper',
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000',
      id: 'round-1',
      sampledAllBallots: false,
    },
  ],
}

export const manifestMocks: { [key: string]: IBallotManifestInfo } = {
  empty: {
    file: null,
    processing: null,
    numBatches: 0,
    numBallots: 0,
  },
  processed: {
    file: { name: 'manifest.csv', uploadedAt: '2020-06-08T21:39:05.765' },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-06-08T21:39:05.765',
      completedAt: '2020-06-08T21:39:14.574',
      error: null,
    },
    numBatches: 10,
    numBallots: 2117,
  },
  errored: {
    file: {
      name: 'manifest.csv',
      uploadedAt: '2020-05-05T17:25:25.663592',
    },
    processing: {
      completedAt: '2020-05-05T17:25:26.09915',
      error: 'Invalid CSV',
      startedAt: '2020-05-05T17:25:26.09743',
      status: FileProcessingStatus.ERRORED,
    },
    numBallots: null,
    numBatches: null,
  },
}

export const talliesMocks: { [key: string]: IFileInfo } = {
  empty: {
    file: null,
    processing: null,
  },
  processed: {
    file: { name: 'tallies.csv', uploadedAt: '2020-06-08T21:39:05.765' },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-06-08T21:39:05.765',
      completedAt: '2020-06-08T21:39:14.574',
      error: null,
    },
  },
  errored: {
    file: {
      name: 'tallies.csv',
      uploadedAt: '2020-05-05T17:25:25.663592',
    },
    processing: {
      completedAt: '2020-05-05T17:25:26.09915',
      error: 'Invalid CSV',
      startedAt: '2020-05-05T17:25:26.09743',
      status: FileProcessingStatus.ERRORED,
    },
  },
}

export const cvrsMocks: { [key: string]: IFileInfo } = {
  empty: {
    file: null,
    processing: null,
  },
  processed: {
    file: { name: 'cvrs.csv', uploadedAt: '2020-11-18T21:39:05.765' },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-11-18T21:39:05.765',
      completedAt: '2020-11-18T21:39:14.574',
      error: null,
    },
  },
  errored: {
    file: {
      name: 'cvrs.csv',
      uploadedAt: '2020-11-15T17:25:25.663592',
    },
    processing: {
      completedAt: '2020-11-15T17:25:26.09915',
      error: 'Invalid CSV',
      startedAt: '2020-11-15T17:25:26.09743',
      status: FileProcessingStatus.ERRORED,
    },
  },
}

export const jurisdictionMocks: { [key: string]: IJurisdiction[] } = {
  empty: [],
  // Setup - Ballot polling
  noManifests: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.empty,
      currentRoundStatus: null,
    },
  ],
  oneManifest: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.errored,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: null,
    },
  ],
  allManifests: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: null,
    },
  ],
  // Setup - Batch comparison
  noManifestsNoTallies: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.empty,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.empty,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.empty,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
  ],
  twoManifestsOneTallies: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.errored,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      batchTallies: talliesMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: null,
    },
  ],
  allManifestsAllTallies: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: null,
    },
  ],
  // In progress - Batch comparison (can also be used for ballot polling)
  oneComplete: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      batchTallies: talliesMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.IN_PROGRESS,
        numUniqueAudited: 4,
        numUnique: 10,
        numSamplesAudited: 5,
        numSamples: 11,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
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
  allComplete: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
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
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
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
}

export const contestMocks: {
  [key: string]: IContest[]
} = {
  empty: [],
  oneTargeted: [
    {
      id: 'contest-id-1',
      name: 'Contest 1',
      isTargeted: true,
      totalBallotsCast: '30',
      numWinners: '1',
      votesAllowed: '1',
      jurisdictionIds: [
        'jurisdiction-id-1',
        'jurisdiction-id-2',
        'jurisdiction-id-3',
      ],
      choices: [
        {
          id: 'choice-id-1',
          name: 'Choice One',
          numVotes: '10',
        },
        {
          id: 'choice-id-2',
          name: 'Choice Two',
          numVotes: '20',
        },
      ],
    },
    {
      id: 'contest-id-2',
      name: 'Contest 2',
      isTargeted: false,
      totalBallotsCast: '400',
      numWinners: '2',
      votesAllowed: '2',
      jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
      choices: [
        {
          id: 'choice-id-3',
          name: 'Choice Three',
          numVotes: '300',
        },
        {
          id: 'choice-id-4',
          name: 'Choice Four',
          numVotes: '100',
        },
      ],
    },
  ],
}

export const fileProcessingMocks: {
  [key in 'null' | 'processed']: IFileInfo['processing']
} = {
  null: null,
  processed: {
    status: FileProcessingStatus.PROCESSED,
    startedAt: 'sometim',
    completedAt: 'a different tim',
    error: null,
  },
}

export const auditBoardMocks: {
  [key in
    | 'empty'
    | 'unfinished'
    | 'finished'
    | 'single'
    | 'double'
    | 'noBallots'
    | 'started'
    | 'signedOff']: IAuditBoard[]
} = {
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
      signedOffAt: '2019-07-18T16:34:07.000',
      passphrase: 'happy-randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 30,
      },
    },
  ],
}
