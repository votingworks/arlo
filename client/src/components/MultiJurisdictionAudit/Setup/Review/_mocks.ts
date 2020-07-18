export const settingsMock = {
  empty: [
    {
      state: null,
      electionName: null,
      online: null,
      randomSeed: null,
      riskLimit: null,
    },
    // here for type completion but not used in this context
    /* istanbul ignore next */
    async () => true,
  ],
  full: [
    {
      state: 'AL',
      electionName: 'Election Name',
      online: true,
      randomSeed: '12345',
      riskLimit: 10,
    },
    // here for type completion but not used in this context
    /* istanbul ignore next */
    async () => true,
  ],
}

export const sampleSizeMock = {
  sampleSizes: {
    'contest-id': [
      { prob: 0.54, size: 46, type: 'ASN' },
      { prob: 0.7, size: 67, type: null },
      { prob: null, size: 88, type: null },
      { prob: 0.9, size: 125, type: null },
    ],
  },
}

export default settingsMock
