import { afterEach, describe, expect, test, vi } from 'vitest'
import Papa from 'papaparse'
import { redactCsvColumn } from './csv'

const readFileText = (file: File) =>
  new Promise<string>(resolve => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.readAsText(file)
  })

const createCsvFile = (contents: BlobPart) =>
  new File([contents], 'cvr.csv', { type: 'text/csv' })

// Dominion CVRs have 3 metadata rows above the header row
const redactRecordIdColumn = (file: File) =>
  redactCsvColumn(file, 'RecordId', { numRowsToSkip: 3 })

const expectRecordIdColumnRedacted = async (
  input: string,
  expected: string
) => {
  const result = await redactRecordIdColumn(createCsvFile(input))
  expect(await readFileText(result)).toEqual(expected)
}

const expectOriginalFile = async (contents: BlobPart) => {
  const file = createCsvFile(contents)
  expect(await redactRecordIdColumn(file)).toEqual(file)
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
1,TABULATOR1,BATCH1,REDACTED,1-1-1,Election Day,12345,COUNTY,0,1,1
2,TABULATOR1,BATCH1,REDACTED,1-1-2,Election Day,12345,COUNTY,1,0,1
`

describe('redactCsvColumn', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('redacts the column in all rows after the header row', async () => {
    const file = createCsvFile(DOMINION_CVR)
    const result = await redactRecordIdColumn(file)
    expect(result.name).toEqual(file.name)
    expect(result.type).toEqual(file.type)
    expect(await readFileText(result)).toEqual(DOMINION_CVR_REDACTED)
  })

  test('handles rows split across chunks', async () => {
    // Use a tiny chunk size so that the skipped rows and header row span multiple chunks
    const originalParse = Papa.parse
    vi.spyOn(Papa, 'parse').mockImplementation(((
      input: File,
      config: Papa.ParseLocalConfig<string[], File>
    ) =>
      originalParse(input, { ...config, chunkSize: 5 })) as typeof Papa.parse)
    await expectRecordIdColumnRedacted(DOMINION_CVR, DOMINION_CVR_REDACTED)
  })

  test('preserves values with leading equal signs', async () => {
    // Python's csv module (used on the server) reads "=""1""" as ="1", same as the original
    await expectRecordIdColumnRedacted(
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
"=""1""","=""TABULATOR1""","=""BATCH1""",REDACTED,"=""1-1-1"""
`
    )
  })

  test('preserves CRLF line endings', async () => {
    await expectRecordIdColumnRedacted(
      'a\r\nb\r\nc\r\nCvrNumber,RecordId,BatchId\r\n1,2,3\r\n4,5,6',
      'a\r\nb\r\nc\r\nCvrNumber,RecordId,BatchId\r\n1,REDACTED,3\r\n4,REDACTED,6\r\n'
    )
  })

  test('leaves rows without the column unchanged', async () => {
    await expectRecordIdColumnRedacted(
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
      description: 'a CSV with errors in the header rows',
      contents: 'CvrNumber,RecordId\n"1,2\n3,4\n',
    },
    {
      description: 'a CSV with errors after the header rows',
      contents: 'a\nb\nc\nCvrNumber,RecordId\n1,2\n3,4\n"5,6\n',
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

  test('returns the original file if reading the file fails', async () => {
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
})
