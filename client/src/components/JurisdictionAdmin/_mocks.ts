import { IBatches } from './useBatchResults'
import { IRound } from '../AuditAdmin/useRoundsAuditAdmin'
import { FileProcessingStatus } from '../useCSV'
import {
  IFullHandTallyBatchResults,
  IFullHandTallyBatchResult,
} from './useFullHandTallyResults'
import { mocksOfType } from '../testUtilities'

export interface INullResultValues {
  [contestId: string]: {
    [choiceId: string]: null | string | number
  }
}

export const roundMocks = mocksOfType<IRound>()({
  incomplete: {
    id: 'round-1',
    roundNum: 1,
    startedAt: '2020-09-14T17:35:19.482Z',
    endedAt: null,
    isAuditComplete: false,
    needsFullHandTally: false,
    isFullHandTally: false,
    drawSampleTask: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-09-14T17:35:19.482Z',
      completedAt: '2020-09-14T17:36:19.482Z',
      error: null,
    },
  },
  complete: {
    id: 'round-1',
    roundNum: 1,
    startedAt: '2020-09-14T17:35:19.482Z',
    endedAt: '2020-09-14T17:35:19.482Z',
    needsFullHandTally: false,
    isAuditComplete: true,
    isFullHandTally: false,
    drawSampleTask: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-09-14T17:35:19.482Z',
      completedAt: '2020-09-14T17:36:19.482Z',
      error: null,
    },
  },
  fullHandTallyIncomplete: {
    id: 'round-1',
    roundNum: 1,
    startedAt: '2020-09-14T17:35:19.482Z',
    endedAt: null,
    isAuditComplete: false,
    needsFullHandTally: true,
    isFullHandTally: true,
    drawSampleTask: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-09-14T17:35:19.482Z',
      completedAt: '2020-09-14T17:36:19.482Z',
      error: null,
    },
  },
})

export const resultsMocks = mocksOfType<INullResultValues>()({
  emptyInitial: {
    'contest-id-1': {
      'choice-id-1': null,
      'choice-id-2': null,
    },
    'contest-id-2': {
      'choice-id-3': null,
      'choice-id-4': null,
    },
  },
  complete: {
    'contest-id-1': {
      'choice-id-1': 1,
      'choice-id-2': 2,
    },
    'contest-id-2': {
      'choice-id-3': 1,
      'choice-id-4': 2,
    },
  },
})

export const batchResultsMocks = mocksOfType<INullResultValues>()({
  empty: {
    'batch-1': {
      'choice-id-1': null,
      'choice-id-2': null,
    },
    'batch-2': {
      'choice-id-1': null,
      'choice-id-2': null,
    },
    'batch-3': {
      'choice-id-1': null,
      'choice-id-2': null,
    },
  },
  complete: {
    'batch-1': {
      'choice-id-1': 1,
      'choice-id-2': 2,
    },
    'batch-2': {
      'choice-id-1': 1,
      'choice-id-2': 2,
    },
    'batch-3': {
      'choice-id-1': 1,
      'choice-id-2': 2,
    },
  },
})

export const batchesMocks = mocksOfType<IBatches>()({
  emptyInitial: {
    batches: [
      {
        id: 'batch-1',
        name: 'Batch One',
        numBallots: 100,
        auditBoard: null,
        resultTallySheets: [],
      },
      {
        id: 'batch-2',
        name: 'Batch Two',
        numBallots: 100,
        auditBoard: null,
        resultTallySheets: [],
      },
      {
        id: 'batch-3',
        name: 'Batch Three',
        numBallots: 100,
        auditBoard: null,
        resultTallySheets: [],
      },
    ],
    resultsFinalizedAt: null,
  },
  complete: {
    batches: [
      {
        id: 'batch-1',
        name: 'Batch One',
        numBallots: 100,
        auditBoard: {
          id: 'ab-1',
          name: 'Audit Board One',
        },
        resultTallySheets: [
          {
            name: 'Tally Sheet #1',
            results: {
              'choice-id-1': 1,
              'choice-id-2': 2,
            },
          },
        ],
      },
      {
        id: 'batch-2',
        name: 'Batch Two',
        numBallots: 100,
        auditBoard: {
          id: 'ab-1',
          name: 'Audit Board One',
        },
        resultTallySheets: [
          {
            name: 'Tally Sheet #1',
            results: {
              'choice-id-1': 0,
              'choice-id-2': 10,
            },
          },
        ],
      },
      {
        id: 'batch-3',
        name: 'Batch Three',
        numBallots: 100,
        auditBoard: {
          id: 'ab-1',
          name: 'Audit Board One',
        },
        resultTallySheets: [
          {
            name: 'Tally Sheet #1',
            results: {
              'choice-id-1': 2000,
              'choice-id-2': 20,
            },
          },
        ],
      },
    ],
    resultsFinalizedAt: '2020-09-14T17:35:19.482Z',
  },
})

export const fullHandTallyBatchResultMock = mocksOfType<
  IFullHandTallyBatchResults
>()({
  empty: {
    finalizedAt: '',
    results: [],
  },
  complete: {
    finalizedAt: '',
    results: [
      {
        batchName: 'Batch1',
        batchType: 'Other',
        choiceResults: {
          'choice-id-1': 10,
          'choice-id-2': 20,
        },
      },
    ],
  },
  completeWithMultipleBatch: {
    finalizedAt: '',
    results: [
      {
        batchName: 'Batch1',
        batchType: 'Other',
        choiceResults: {
          'choice-id-1': 5,
          'choice-id-2': 15,
        },
      },
      {
        batchName: 'Batch2',
        batchType: 'Provisional',
        choiceResults: {
          'choice-id-1': 5,
          'choice-id-2': 5,
        },
      },
    ],
  },
  updated: {
    finalizedAt: '',
    results: [
      {
        batchName: 'Batch12',
        batchType: 'Other',
        choiceResults: {
          'choice-id-1': 10,
          'choice-id-2': 20,
        },
      },
    ],
  },
  finalized: {
    finalizedAt: '2021-04-13T15:01:00.383031+00:00',
    results: [
      {
        batchName: 'Batch12',
        batchType: 'Other',
        choiceResults: {
          'choice-id-1': 10,
          'choice-id-2': 20,
        },
      },
    ],
  },
})

export const fullHandTallyBatchResultsMock = mocksOfType<
  IFullHandTallyBatchResult
>()({
  empty: {
    batchName: '',
    batchType: '',
    choiceResults: {},
  },
  complete: {
    batchName: 'Batch1',
    batchType: 'Other',
    choiceResults: {
      'choice-id-1': 10,
      'choice-id-2': 20,
    },
  },
  updated: {
    batchName: 'Batch12',
    batchType: 'Other',
    choiceResults: {
      'choice-id-1': 10,
      'choice-id-2': 20,
    },
  },
})
