import Papa from 'papaparse'
import { afterEach, describe, expect, test, vi } from 'vitest'

import { BOM, redactCsvColumns } from './csv'

const createCsvFile = (contents: BlobPart) =>
  new File([contents], 'cvr.csv', { type: 'text/csv' })

const redactDominionColumns = (file: File) =>
  redactCsvColumns(file, ['RecordId', 'ImprintedId'], {
    // Dominion CVRs have 3 metadata rows above the header row
    numRowsToSkip: 3,
  })

const expectRedactedFile = async (
  input: BlobPart,
  expectedOutput: BlobPart,
  redactFn: (file: File) => Promise<File> = redactDominionColumns
) => {
  const inputFile = createCsvFile(input)
  const outputFile = await redactFn(inputFile)
  if (typeof input === 'string' && typeof expectedOutput === 'string') {
    // Present a more readable diff if possible
    expect(await outputFile.text()).toEqual(expectedOutput)
  } else {
    expect(new Uint8Array(await outputFile.arrayBuffer())).toEqual(
      new Uint8Array(await new Blob([expectedOutput]).arrayBuffer())
    )
  }
  expect(outputFile.name).toEqual(inputFile.name)
  expect(outputFile.type).toEqual(inputFile.type)
}

const expectOriginalFile = async (
  input: BlobPart,
  redactFn: (file: File) => Promise<File> = redactDominionColumns
) => {
  const inputFile = createCsvFile(input)
  const outputFile = await redactFn(inputFile)
  expect(new Uint8Array(await outputFile.arrayBuffer())).toEqual(
    new Uint8Array(await inputFile.arrayBuffer())
  )
}

const DOMINION_CVR = `Test Audit CVR Upload,5.2.16.1,,,,,,,,,
,,,,,,,,"Contest 1
(Vote For=1)",Contest 1 (Vote For=1),Contest 2 (Vote For=1)
,,,,,,,,Choice 1-1,Choice 1-2,"Choice ""2-1"", Jr."
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM,LBR
1,TABULATOR1,BATCH1,1,1-1-1,Election Day,12345,COUNTY,0,1,1
2,TABULATOR1,BATCH1,2,1-1-2,Election Day,12345,COUNTY,1,0,1
`

const DOMINION_CVR_REDACTED = `Test Audit CVR Upload,5.2.16.1,,,,,,,,,
,,,,,,,,"Contest 1
(Vote For=1)",Contest 1 (Vote For=1),Contest 2 (Vote For=1)
,,,,,,,,Choice 1-1,Choice 1-2,"Choice ""2-1"", Jr."
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId,CountingGroup,PrecinctPortion,BallotType,REP,DEM,LBR
1,TABULATOR1,BATCH1,REDACTED,REDACTED,Election Day,12345,COUNTY,0,1,1
2,TABULATOR1,BATCH1,REDACTED,REDACTED,Election Day,12345,COUNTY,1,0,1
`

afterEach(() => {
  vi.restoreAllMocks()
})

describe('redactCsvColumns', () => {
  test('redacts the columns in all rows after the header row', async () => {
    await expectRedactedFile(DOMINION_CVR, DOMINION_CVR_REDACTED)
  })

  test('handles rows split across chunks', async () => {
    // Use a tiny chunk size so that content spans multiple chunks
    const originalParse = Papa.parse
    vi.spyOn(Papa, 'parse').mockImplementation(((
      input: File,
      config: Papa.ParseLocalConfig<string[], File>
    ) =>
      originalParse(input, { ...config, chunkSize: 5 })) as typeof Papa.parse)
    await expectRedactedFile(DOMINION_CVR, DOMINION_CVR_REDACTED)
  })

  test('handles CRLF line endings split across chunks after quoted fields', async () => {
    // Papaparse reports a spurious "Trailing quote on quoted field is
    // malformed" error when a chunk boundary falls between the \r and \n of a
    // \r\n after a quoted field. Try every chunk size to hit every boundary.
    const input =
      '"a"\r\n"b"\r\n"c"\r\n"CvrNumber","RecordId"\r\n"1","2"\r\n"3","4"\r\n"5","6"\r\n'
    const expectedOutput =
      'a\r\nb\r\nc\r\nCvrNumber,RecordId\r\n1,REDACTED\r\n3,REDACTED\r\n5,REDACTED\r\n'
    // Papaparse guesses the line ending from the first chunk, so the first
    // chunk needs to contain at least two complete line endings
    const minChunkSize = input.indexOf('\r\n', input.indexOf('\r\n') + 2) + 2
    const originalParse = Papa.parse
    for (
      let chunkSize = minChunkSize;
      chunkSize <= input.length;
      chunkSize += 1
    ) {
      vi.spyOn(Papa, 'parse').mockImplementation(((
        file: File,
        config: Papa.ParseLocalConfig<string[], File>
      ) => originalParse(file, { ...config, chunkSize })) as typeof Papa.parse)
      // oxlint-disable-next-line no-await-in-loop
      await expectRedactedFile(input, expectedOutput)
      vi.restoreAllMocks()
    }
  })

  test('redacts multiple columns regardless of their order in the header row', async () => {
    await expectRedactedFile(
      'a\nb\nc\nImprintedId,CvrNumber,RecordId\n1,2,3\n4,5,6\n',
      'a\nb\nc\nImprintedId,CvrNumber,RecordId\nREDACTED,2,REDACTED\nREDACTED,5,REDACTED\n'
    )
  })

  test('redacts every column with a matching name', async () => {
    await expectRedactedFile(
      'a\nb\nc\nRecordId,CvrNumber,RecordId\n1,2,3\n',
      'a\nb\nc\nRecordId,CvrNumber,RecordId\nREDACTED,2,REDACTED\n'
    )
  })

  test('leaves blank lines unchanged when redacting the first column', async () => {
    await expectRedactedFile(
      'a\nb\nc\nRecordId,CvrNumber\n1,2\n\n3,4\n',
      'a\nb\nc\nRecordId,CvrNumber\nREDACTED,2\n\nREDACTED,4\n'
    )
  })

  test('only marks a value redacted if there was something there', async () => {
    await expectRedactedFile(
      'a\nb\nc\nBatchId,RecordId,CvrNumber\n1,,3\n4,5,6\n',
      'a\nb\nc\nBatchId,RecordId,CvrNumber\n1,,3\n4,REDACTED,6\n'
    )
  })

  test('skips columns that are not in the header row', async () => {
    await expectRedactedFile(
      'a\nb\nc\nCvrNumber,RecordId\n1,2\n',
      'a\nb\nc\nCvrNumber,RecordId\n1,REDACTED\n'
    )
  })

  test('returns the original file if none of the columns are present', async () => {
    await expectOriginalFile('a\nb\nc\nCvrNumber,BatchId\n1,2\n')
  })

  test('preserves values with leading equal signs', async () => {
    // Python's csv module (used on the server) reads "=""1""" as ="1", same as the original
    await expectRedactedFile(
      `,,,,
,,,,
,,,,
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId
="1",="TABULATOR1",="BATCH1",="1",="1-1-1"
`,
      `,,,,
,,,,
,,,,
CvrNumber,TabulatorNum,BatchId,RecordId,ImprintedId
"=""1""","=""TABULATOR1""","=""BATCH1""",REDACTED,REDACTED
`
    )
  })

  test('preserves CRLF line endings', async () => {
    await expectRedactedFile(
      'a\r\nb\r\nc\r\nCvrNumber,RecordId,BatchId\r\n1,2,3\r\n4,5,6\r\n',
      'a\r\nb\r\nc\r\nCvrNumber,RecordId,BatchId\r\n1,REDACTED,3\r\n4,REDACTED,6\r\n'
    )
  })

  test('leaves rows without the column unchanged', async () => {
    await expectRedactedFile(
      'a\nb\nc\nCvrNumber,BatchId,RecordId\n1,2\n1,2,3\n',
      'a\nb\nc\nCvrNumber,BatchId,RecordId\n1,2\n1,2,REDACTED\n'
    )
  })

  test.each([
    { description: 'an empty file', contents: '' },
    {
      description: 'a CSV with fewer rows than the header row index',
      contents: 'a,b,c\n1,2,3\n',
    },
    {
      description: 'a CSV without the column in the header row',
      contents: 'a\nb\nc\nCvrNumber,BatchId\n1,2\n',
    },
    {
      description: 'a CSV with the column in a row other than the header row',
      contents: 'a\nCvrNumber,RecordId\nc\nd\n1,2\n',
    },
    {
      description: 'a tab-delimited file',
      contents: 'a\nb\nc\nCvrNumber\tRecordId\tBatchId\n1\t2\t3\n',
    },
    {
      description: 'an XML file',
      contents:
        '<?xml version="1.0"?>\n<Report>\n<Tabulator Id="1" />\n</Report>\n',
    },
    {
      description: 'a binary file (e.g., an Excel file)',
      contents: new Uint8Array([
        0x50, 0x4b, 0x03, 0x04, 0x14, 0x00, 0x22, 0x0a, 0xff,
      ]),
    },
  ])('returns the original file for $description', async ({ contents }) => {
    await expectOriginalFile(contents)
  })

  test.each([
    { description: 'UTF-8', bytes: new TextEncoder().encode('Café') },
    {
      description: 'Windows-1252',
      bytes: new Uint8Array([0x4a, 0x6f, 0x73, 0xe9]), // Café
    },
    {
      description: 'ISO-8859-1 that happens to be valid UTF-8',
      bytes: new Uint8Array([0xc3, 0xa9]), // Ã©, or é in UTF-8
    },
    {
      description: 'every non-ASCII byte',
      bytes: Uint8Array.from({ length: 0x80 }, (_, i) => 0x80 + i),
    },
  ])('preserves non-ASCII bytes - $description', async ({ bytes }) => {
    const input = new Blob([
      'a\nb\nc\nCvrNumber,RecordId,BatchId\n1,2,',
      bytes,
      '\n',
    ])
    const expectedOutput = new Blob([
      'a\nb\nc\nCvrNumber,RecordId,BatchId\n1,REDACTED,',
      bytes,
      '\n',
    ])
    await expectRedactedFile(input, expectedOutput)
  })

  test('handles multi-byte characters split across chunks', async () => {
    const originalParse = Papa.parse
    vi.spyOn(Papa, 'parse').mockImplementation(((
      input: File,
      config: Papa.ParseLocalConfig<string[], File>
    ) =>
      originalParse(input, { ...config, chunkSize: 5 })) as typeof Papa.parse)
    // é is 2 bytes in UTF-8. With 5-byte chunks, the first byte of "é" is the
    // last byte of a chunk.
    await expectRedactedFile(
      'a\nb\nc\nCvrNumber,RecordId\n10,20\nCafé,3\n',
      'a\nb\nc\nCvrNumber,RecordId\n10,REDACTED\nCafé,REDACTED\n'
    )
  })

  test('returns the original file if reading throws', async () => {
    const parseWithReadError = (
      input: File,
      config: Papa.ParseLocalConfig<string[], File>
    ) => config.error!(new Error('Read error'), input)
    vi.spyOn(Papa, 'parse').mockImplementation(
      parseWithReadError as unknown as typeof Papa.parse
    )
    await expectOriginalFile('a\nb\nc\nCvrNumber,RecordId\n1,2\n')
  })

  test('returns the original file if processing throws', async () => {
    vi.spyOn(Papa, 'unparse').mockImplementation(() => {
      throw new Error('Unexpected')
    })
    await expectOriginalFile('a\nb\nc\nCvrNumber,RecordId\n1,2\n')
  })

  test.each<{
    numRowsToSkip?: number
    input: string
    expectedOutput: string
  }>([
    {
      numRowsToSkip: undefined,
      input: 'CvrNumber,RecordId,BatchId\n1,2,3\n4,5,6\n',
      expectedOutput:
        'CvrNumber,RecordId,BatchId\n1,REDACTED,3\n4,REDACTED,6\n',
    },
    {
      numRowsToSkip: 0,
      input: 'CvrNumber,RecordId,BatchId\n1,2,3\n4,5,6\n',
      expectedOutput:
        'CvrNumber,RecordId,BatchId\n1,REDACTED,3\n4,REDACTED,6\n',
    },
    {
      numRowsToSkip: 1,
      input: 'CvrNumber,RecordId,BatchId\n1,2,3\n4,5,6\n',
      expectedOutput: 'CvrNumber,RecordId,BatchId\n1,2,3\n4,5,6\n',
    },
    {
      numRowsToSkip: 1,
      input:
        'CvrNumber,RecordId,BatchId\nCvrNumber,RecordId,BatchId\n1,2,3\n4,5,6\n',
      expectedOutput:
        'CvrNumber,RecordId,BatchId\nCvrNumber,RecordId,BatchId\n1,REDACTED,3\n4,REDACTED,6\n',
    },
    {
      numRowsToSkip: 1,
      input:
        'CvrNumber,RecordId,BatchId\nCvrNumber,NotRecordId,BatchId\n1,2,3\n4,5,6\n',
      expectedOutput:
        'CvrNumber,RecordId,BatchId\nCvrNumber,NotRecordId,BatchId\n1,2,3\n4,5,6\n',
    },
  ])(
    'numRowsToSkip ignores the specified number of rows and treats the first after as the header row',
    async ({ numRowsToSkip, input, expectedOutput }) => {
      await expectRedactedFile(input, expectedOutput, (file: File) =>
        redactCsvColumns(file, ['RecordId'], { numRowsToSkip })
      )
    }
  )

  test('preserves a UTF-8 byte order mark', async () => {
    await expectRedactedFile(
      new Blob([BOM.UTF8, 'a\nb\nc\nCvrNumber,RecordId\n1,2\n']),
      new Blob([BOM.UTF8, 'a\nb\nc\nCvrNumber,RecordId\n1,REDACTED\n'])
    )
  })

  test('preserves a UTF-8 byte order mark and non-ASCII bytes', async () => {
    const cafe = new TextEncoder().encode('Café')
    await expectRedactedFile(
      new Blob([BOM.UTF8, cafe, '\nb\nc\nCvrNumber,RecordId\n', cafe, ',2\n']),
      new Blob([
        BOM.UTF8,
        cafe,
        '\nb\nc\nCvrNumber,RecordId\n',
        cafe,
        ',REDACTED\n',
      ])
    )
  })

  test('preserves a UTF-8 byte order mark across chunks', async () => {
    const originalParse = Papa.parse
    vi.spyOn(Papa, 'parse').mockImplementation(((
      input: File,
      config: Papa.ParseLocalConfig<string[], File>
    ) =>
      originalParse(input, { ...config, chunkSize: 5 })) as typeof Papa.parse)
    await expectRedactedFile(
      new Blob([BOM.UTF8, 'a\nb\nc\nCvrNumber,RecordId\n10,20\nCaf\u00e9,3\n']),
      new Blob([
        BOM.UTF8,
        'a\nb\nc\nCvrNumber,RecordId\n10,REDACTED\nCaf\u00e9,REDACTED\n',
      ])
    )
  })

  test('finds the column when it is the first cell after a UTF-8 byte order mark', async () => {
    await expectRedactedFile(
      new Blob([BOM.UTF8, 'RecordId,CvrNumber\n1,2']),
      new Blob([BOM.UTF8, 'RecordId,CvrNumber\nREDACTED,2']),
      (file: File) => redactCsvColumns(file, ['RecordId'])
    )
  })

  test.each([
    { description: 'UTF-16 LE', bom: BOM.UTF16LE },
    { description: 'UTF-16 BE', bom: BOM.UTF16BE },
  ])(
    'returns the original file for $description with a byte order mark',
    async ({ bom }) => {
      const text = 'RecordId,CvrNumber\n1,2\n' // Not actually UTF-16 but fine for this test
      const parseSpy = vi.spyOn(Papa, 'parse')
      await expectOriginalFile(new Blob([bom, text]), (file: File) =>
        redactCsvColumns(file, ['RecordId'])
      )
      expect(parseSpy).not.toHaveBeenCalled()
    }
  )
})

describe('redactCsvColumns with shuffleRowsWithinGroupsBy', () => {
  const redactAndShuffle = (file: File) =>
    redactCsvColumns(file, ['CvrNumber', 'RecordId'], {
      numRowsToSkip: 3,
      shuffleRowsWithinGroupsBy: ['TabulatorNum', 'BatchId'],
    })

  // Rows are tagged with a unique Tag value so we can track them after
  // CvrNumber is redacted. Batches are interleaved, and (T2, B1) shares a
  // BatchId with (T1, B1) to check that grouping uses both columns.
  const INPUT = `Election,5.2.16.1,,,
,,,,Contest 1 (Vote For=1)
,,,,Choice 1
CvrNumber,TabulatorNum,BatchId,RecordId,Tag
1,T1,B1,1,a
2,T1,B2,1,b
3,T1,B1,2,c
4,T2,B1,1,d
5,T1,B2,2,e
6,T1,B1,3,f
`

  const HEADER = `Election,5.2.16.1,,,
,,,,Contest 1 (Vote For=1)
,,,,Choice 1
CvrNumber,TabulatorNum,BatchId,RecordId,Tag
`

  /**
   * With getRandomValues always returning 0, Fisher-Yates always swaps with
   * index 0, which rotates each group left by one.
   */
  const EXPECTED_OUTPUT_WITH_ZERO_RANDOMNESS = `${HEADER}REDACTED,T1,B1,REDACTED,c
REDACTED,T1,B1,REDACTED,f
REDACTED,T1,B1,REDACTED,a
REDACTED,T1,B2,REDACTED,e
REDACTED,T1,B2,REDACTED,b
REDACTED,T2,B1,REDACTED,d
`

  const mockRandomValues = (values: number[]) => {
    const remaining = [...values]
    return vi.spyOn(crypto, 'getRandomValues').mockImplementation(((
      array: Uint32Array
    ) => {
      array.set([remaining.length > 0 ? remaining.shift()! : 0])
      return array
    }) as typeof crypto.getRandomValues)
  }

  const useTinyChunks = () => {
    const originalParse = Papa.parse
    vi.spyOn(Papa, 'parse').mockImplementation(((
      input: File,
      config: Papa.ParseLocalConfig<string[], File>
    ) =>
      originalParse(input, { ...config, chunkSize: 5 })) as typeof Papa.parse)
  }

  test('redacts and shuffles rows within each group, keeping groups in first-seen order', async () => {
    mockRandomValues([])
    await expectRedactedFile(
      INPUT,
      EXPECTED_OUTPUT_WITH_ZERO_RANDOMNESS,
      redactAndShuffle
    )
  })

  test('handles rows split across chunks', async () => {
    mockRandomValues([])
    useTinyChunks()
    await expectRedactedFile(
      INPUT,
      EXPECTED_OUTPUT_WITH_ZERO_RANDOMNESS,
      redactAndShuffle
    )
  })

  test('rejects random values that would bias the shuffle', async () => {
    // For a group of 3, the first draw is in [0, 3). 0xffffffff is above the
    // largest multiple of 3 below 2^32, so it should be rejected and redrawn.
    const spy = mockRandomValues([0xffffffff])
    await expectRedactedFile(
      'a\nb\nc\nCvrNumber,TabulatorNum,BatchId\n1,T1,B1\n2,T1,B1\n3,T1,B1\n',
      'a\nb\nc\nCvrNumber,TabulatorNum,BatchId\nREDACTED,T1,B1\nREDACTED,T1,B1\nREDACTED,T1,B1\n',
      redactAndShuffle
    )
    // 1 rejected + 2 accepted draws
    expect(spy).toHaveBeenCalledTimes(3)
  })

  test('produces a permutation of each group with real randomness', async () => {
    const tabulatorsAndBatches = [
      ['T1', 'B1'],
      ['T1', 'B2'],
      ['T2', 'B1'],
    ]
    const numRowsPerGroup = 50
    const dataRows = tabulatorsAndBatches.flatMap(([tabulator, batch]) =>
      Array.from(
        { length: numRowsPerGroup },
        (_, i) => `${i},${tabulator},${batch},${i},${tabulator}-${batch}-${i}`
      )
    )
    const input = `${HEADER}${dataRows.join('\n')}\n`

    const output = await (await redactAndShuffle(createCsvFile(input))).text()

    expect(output.startsWith(HEADER)).toEqual(true)
    expect(output.endsWith('\n')).toEqual(true)
    const outputRows = output
      .slice(HEADER.length)
      .trimEnd()
      .split('\n')
      .map(line => line.split(','))
    expect(outputRows).toHaveLength(dataRows.length)

    tabulatorsAndBatches.forEach(([tabulator, batch], groupIndex) => {
      // Groups are contiguous and in their original order
      const groupRows = outputRows.slice(
        groupIndex * numRowsPerGroup,
        (groupIndex + 1) * numRowsPerGroup
      )
      groupRows.forEach(row => {
        expect(row.slice(0, 4)).toEqual([
          'REDACTED',
          tabulator,
          batch,
          'REDACTED',
        ])
      })
      // Same rows as the input, but not in the same order (the chance of a
      // shuffle of 50 rows leaving them in order is 1/50!)
      const tags = groupRows.map(row => row[4])
      const originalTags = Array.from(
        { length: numRowsPerGroup },
        (_, i) => `${tabulator}-${batch}-${i}`
      )
      expect([...tags].sort()).toEqual([...originalTags].sort())
      expect(tags).not.toEqual(originalTags)
    })
  })

  test('preserves CRLF line endings and the absence of a trailing line break', async () => {
    mockRandomValues([])
    await expectRedactedFile(
      'a\r\nb\r\nc\r\nCvrNumber,TabulatorNum,BatchId,Tag\r\n1,T1,B1,x\r\n2,T1,B1,y',
      'a\r\nb\r\nc\r\nCvrNumber,TabulatorNum,BatchId,Tag\r\nREDACTED,T1,B1,y\r\nREDACTED,T1,B1,x',
      redactAndShuffle
    )
  })

  test('drops blank data rows', async () => {
    mockRandomValues([])
    await expectRedactedFile(
      'a\nb\nc\nCvrNumber,TabulatorNum,BatchId,Tag\n1,T1,B1,x\n\n2,T1,B1,y\n',
      'a\nb\nc\nCvrNumber,TabulatorNum,BatchId,Tag\nREDACTED,T1,B1,y\nREDACTED,T1,B1,x\n',
      redactAndShuffle
    )
  })

  test('groups by raw values, including leading equal signs', async () => {
    mockRandomValues([])
    await expectRedactedFile(
      'a\nb\nc\nCvrNumber,TabulatorNum,BatchId,Tag\n="1",="T1",="B1",x\n="2",="T1",="B1",y\n',
      'a\nb\nc\nCvrNumber,TabulatorNum,BatchId,Tag\nREDACTED,"=""T1""","=""B1""",y\nREDACTED,"=""T1""","=""B1""",x\n',
      redactAndShuffle
    )
  })

  test('preserves a UTF-8 byte order mark and non-ASCII bytes', async () => {
    mockRandomValues([])
    const cafe = new TextEncoder().encode('Café')
    await expectRedactedFile(
      new Blob([
        BOM.UTF8,
        'a\nb\nc\nCvrNumber,TabulatorNum,BatchId,Tag\n1,T1,B1,x\n2,T1,B1,',
        cafe,
        '\n',
      ]),
      new Blob([
        BOM.UTF8,
        'a\nb\nc\nCvrNumber,TabulatorNum,BatchId,Tag\nREDACTED,T1,B1,',
        cafe,
        '\nREDACTED,T1,B1,x\n',
      ]),
      redactAndShuffle
    )
  })

  test('returns the original file if a group-by column is missing', async () => {
    await expectOriginalFile(
      'a\nb\nc\nCvrNumber,TabulatorNum,Tag\n1,T1,x\n2,T1,y\n',
      redactAndShuffle
    )
  })

  test('returns the original file if none of the columns to redact are present', async () => {
    await expectOriginalFile(
      'a\nb\nc\nTabulatorNum,BatchId,Tag\nT1,B1,x\nT1,B1,y\n',
      redactAndShuffle
    )
  })

  test('returns the original file if processing throws', async () => {
    vi.spyOn(Papa, 'unparse').mockImplementation(() => {
      throw new Error('Unexpected')
    })
    await expectOriginalFile(INPUT, redactAndShuffle)
  })

  test('returns the original file if shuffling throws', async () => {
    vi.spyOn(crypto, 'getRandomValues').mockImplementation(() => {
      throw new Error('No randomness')
    })
    await expectOriginalFile(INPUT, redactAndShuffle)
  })
})
