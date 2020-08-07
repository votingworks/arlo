export interface INullResultValues {
  [contestId: string]: {
    [choiceId: string]: null | string | number
  }
}

export const resultsMocks: {
  [key in 'emptyInitial']: INullResultValues
} = {
  emptyInitial: {
    'contest-id-1': {
      'choice-id-1': null,
      'choice-id-2': null,
    },
  },
}

export default resultsMocks
