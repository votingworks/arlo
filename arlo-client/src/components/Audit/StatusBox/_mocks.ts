import {
  IJurisdictionsResponse,
  FileProcessingStatus,
} from './getJurisdictions'
import { IRound } from '../../../types'

export const jurisdictionMocks: {
  [key in
    | 'none'
    | 'noUploads'
    | 'halfUploads'
    | 'allFinishedFirstRound']: IJurisdictionsResponse
} = {
  none: { jurisdictions: [] },
  noUploads: {
    jurisdictions: [
      {
        id: 'jurisdiction-1',
        name: 'Jurisdiction One',
        currentRoundStatus: null,
        ballotManifest: {
          file: null,
          numBallots: null,
          numBatches: null,
          processing: null,
        },
      },
      {
        id: 'jurisdiction-2',
        name: 'Jurisdiction Two',
        currentRoundStatus: null,
        ballotManifest: {
          file: null,
          numBallots: null,
          numBatches: null,
          processing: null,
        },
      },
    ],
  },
  halfUploads: {
    jurisdictions: [
      {
        id: 'jurisdiction-1',
        name: 'Jurisdiction One',
        currentRoundStatus: null,
        ballotManifest: {
          file: 'ballot manifest',
          numBallots: 10,
          numBatches: 1,
          processing: FileProcessingStatus.Processed,
        },
      },
      {
        id: 'jurisdiction-2',
        name: 'Jurisdiction Two',
        currentRoundStatus: null,
        ballotManifest: {
          file: null,
          numBallots: null,
          numBatches: null,
          processing: null,
        },
      },
    ],
  },
  allFinishedFirstRound: {
    jurisdictions: [
      {
        id: 'jurisdiction-1',
        name: 'Jurisdiction One',
        currentRoundStatus: 1,
        ballotManifest: {
          file: 'ballot manifest',
          numBallots: 10,
          numBatches: 1,
          processing: FileProcessingStatus.Processed,
        },
      },
      {
        id: 'jurisdiction-2',
        name: 'Jurisdiction Two',
        currentRoundStatus: 1,
        ballotManifest: {
          file: 'ballot manifest',
          numBallots: 10,
          numBatches: 1,
          processing: FileProcessingStatus.Processed,
        },
      },
    ],
  },
}

export const roundMocks: {
  [key in
    | 'none'
    | 'firstRoundComplete'
    | 'firstRoundIncomplete'
    | 'secondRoundIncomplete']: { rounds: IRound[] }
} = {
  none: { rounds: [] },
  firstRoundIncomplete: {
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: null,
              pvalue: null,
            },
            id: 'contest-1',
            results: {},
            sampleSize: null,
            sampleSizeOptions: null,
          },
        ],
        endedAt: null,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
    ],
  },
  firstRoundComplete: {
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: true,
              pvalue: 0.00020431431380638307,
            },
            id: 'contest-1',
            results: {
              'choice-1': 100,
              'choice-2': 167,
            },
            sampleSize: 379,
            sampleSizeOptions: [
              { size: 269, type: 'ASN', prob: null },
              { size: 379, prob: 0.8, type: null },
              { size: 78, prob: null, type: null },
            ],
          },
        ],
        endedAt: '2019-07-18T16:59:34.000Z',
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
    ],
  },
  secondRoundIncomplete: {
    rounds: [
      {
        contests: [
          {
            endMeasurements: {
              isComplete: false,
              pvalue: 1,
            },
            id: 'contest-1',
            results: {
              'choice-1': 0,
              'choice-2': 0,
            },
            sampleSize: null,
            sampleSizeOptions: [
              { size: 269, type: 'ASN', prob: null },
              { size: 379, prob: 0.8, type: null },
              { size: 78, prob: null, type: null },
            ],
          },
        ],
        endedAt: '2019-07-18T16:35:07.000Z',
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-1',
      },
      {
        contests: [
          {
            endMeasurements: {
              isComplete: null,
              pvalue: null,
            },
            id: 'contest-1',
            results: {},
            sampleSize: null,
            sampleSizeOptions: [
              { size: 269, type: 'ASN', prob: null },
              { size: 379, prob: 0.8, type: null },
              { size: 78, prob: null, type: null },
            ],
          },
        ],
        endedAt: null,
        startedAt: '2019-07-18T16:34:07.000Z',
        id: 'round-2',
      },
    ],
  },
}
