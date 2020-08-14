export const settingsMock = {
  empty: [
    {
      state: null,
      electionName: null,
      online: null,
      randomSeed: null,
      riskLimit: null,
      auditType: 'BALLOT_POLLING',
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
      auditType: 'BALLOT_POLLING',
    },
    // here for type completion but not used in this context
    /* istanbul ignore next */
    async () => true,
  ],
  offline: [
    {
      state: 'AL',
      electionName: 'Election Name',
      online: false,
      randomSeed: '12345',
      riskLimit: 10,
      auditType: 'BALLOT_POLLING',
    },
    // here for type completion but not used in this context
    /* istanbul ignore next */
    async () => true,
  ],
}

export const sampleSizeMock = {
  sampleSizes: {
    'contest-id': [
      { prob: 0.54, size: 46, key: 'asn' },
      { prob: 0.7, size: 67, key: '0.7' },
      { prob: 0.5, size: 88, key: '0.5' },
      { prob: 0.9, size: 125, key: '0.9' },
    ],
  },
}

export default settingsMock
