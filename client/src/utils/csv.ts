import Papa from 'papaparse'

const DEFAULT_PARSE_OPTIONS = {
  chunkSize: 1024 * 1024, // 1MB
  delimiter: ',',

  /**
   * We don't know the file's encoding (UTF-8, Windows-1252, etc.), and
   * decoding with the wrong one could corrupt characters. Instead, decode as
   * x-user-defined, which maps ASCII bytes to themselves and bytes
   * 0x80-0xFF to U+F780-U+F7FF. See {@link encodeXUserDefined} for the inverse
   * logic.
   *
   * This makes it such that we can detect CSV delimiters and line breaks
   * without issue but treat all values as opaque blobs and round trip them
   * unchanged.
   */
  encoding: 'x-user-defined',
} as const

export const BOM = {
  UTF8: new Uint8Array([0xef, 0xbb, 0xbf]),
  UTF16LE: new Uint8Array([0xff, 0xfe]),
  UTF16BE: new Uint8Array([0xfe, 0xff]),
} as const

type BomType = keyof typeof BOM

interface FileContents {
  bom?: { type: BomType; bytes: Uint8Array<ArrayBuffer> }
  fileWithoutBom: File
}

/**
 * Given a string decoded as an x-user-defined string, returns the original
 * bytes.
 */
function encodeXUserDefined(text: string): Uint8Array<ArrayBuffer> {
  const bytes = new Uint8Array(text.length)
  for (let i = 0; i < text.length; i += 1) {
    const charCode = text.charCodeAt(i)
    bytes[i] = charCode < 0x80 ? charCode : charCode - 0xf700
  }
  return bytes
}

async function fileStartsWith(
  file: File,
  prefix: Uint8Array
): Promise<boolean> {
  const fileFirstBytes = new Uint8Array(
    await file.slice(0, prefix.length).arrayBuffer()
  )
  return (
    fileFirstBytes.length === prefix.length &&
    prefix.every((byte, i) => fileFirstBytes[i] === byte)
  )
}

async function parseBom(file: File): Promise<FileContents> {
  for (const [bomType, bomBytes] of Object.entries(BOM)) {
    // oxlint-disable-next-line no-await-in-loop
    if (await fileStartsWith(file, bomBytes)) {
      return {
        bom: { type: bomType as BomType, bytes: bomBytes },
        fileWithoutBom: new File([file.slice(bomBytes.length)], file.name, {
          lastModified: file.lastModified,
          type: file.type,
        }),
      }
    }
  }
  return {
    bom: undefined,
    fileWithoutBom: file,
  }
}

/**
 * Returns the indices of all header row cells that match one of the given
 * column names, in ascending order.
 */
function findCsvColumnIndices(
  { fileWithoutBom }: FileContents,
  columnNames: readonly string[],
  numRowsToSkip: number
): Promise<number[]> {
  return new Promise((resolve, reject) => {
    Papa.parse<string[]>(fileWithoutBom, {
      ...DEFAULT_PARSE_OPTIONS,
      preview: numRowsToSkip + 1,
      complete: ({ data, errors }) => {
        if (errors.length > 0) {
          reject(new Error(errors[0].message))
          return
        }
        if (data.length < numRowsToSkip + 1) {
          reject(new Error('Header row not found'))
          return
        }
        const headerRow = data[numRowsToSkip]
        const columnIndices = headerRow
          .map((value, columnIndex) =>
            columnNames.includes(value) ? columnIndex : null
          )
          .filter(index => index !== null)
        resolve(columnIndices)
      },
      error: reject,
    })
  })
}

/**
 * Papaparse doesn't return the last row of a chunk (unless it's the final
 * chunk) because the row may be incomplete. Instead, it re-parses that row from
 * the start as part of the next chunk. Errors attached to that discarded row
 * (error.row === data.length) can be spurious, e.g., a chunk boundary between
 * the \r and \n of a \r\n after a quoted field triggers "Trailing quote on
 * quoted field is malformed". Ignore them. Any real error will resurface when
 * the row is re-parsed in the next chunk.
 */
function throwOnRealChunkErrors(
  data: readonly string[][],
  errors: readonly Papa.ParseError[]
): void {
  const realErrors = errors.filter(
    error => error.row === undefined || error.row < data.length
  )
  if (realErrors.length > 0) {
    throw new Error(realErrors[0].message)
  }
}

function redactRow(
  row: readonly string[],
  columnIndicesToRedact: ReadonlySet<number>
): string[] {
  return row.map((value, columnIndex) =>
    value !== '' && columnIndicesToRedact.has(columnIndex) ? 'REDACTED' : value
  )
}

function redactCsvColumnsAtIndices(
  { bom, fileWithoutBom }: FileContents,
  columnIndicesToRedact: readonly number[],
  numRowsToSkip: number
): Promise<File> {
  const columnIndicesToRedactSet = new Set(columnIndicesToRedact)
  return new Promise((resolve, reject) => {
    let output = bom ? new Blob([bom.bytes]) : new Blob([])
    let rowsProcessed = 0
    Papa.parse<string[]>(fileWithoutBom, {
      ...DEFAULT_PARSE_OPTIONS,
      chunk: ({ data, errors, meta }, parser) => {
        try {
          throwOnRealChunkErrors(data, errors)
          if (data.length === 0) {
            return
          }
          const rows = data.map((row, rowIndex) => {
            const isHeaderOrAbove = rowsProcessed + rowIndex < numRowsToSkip + 1
            return isHeaderOrAbove
              ? row
              : redactRow(row, columnIndicesToRedactSet)
          })
          const csv = Papa.unparse(rows, {
            escapeFormulae: false,
            newline: meta.linebreak,
          })
          output = new Blob([
            output,
            encodeXUserDefined((rowsProcessed > 0 ? meta.linebreak : '') + csv),
          ])
          rowsProcessed += rows.length
        } catch (error) {
          // Call reject before parser.abort because parser.abort triggers the
          // complete callback
          reject(error)
          parser.abort()
        }
      },
      complete: () => {
        resolve(
          new File([output], fileWithoutBom.name, {
            lastModified: fileWithoutBom.lastModified,
            type: fileWithoutBom.type,
          })
        )
      },
      error: reject,
    })
  })
}

/**
 * Returns a cryptographically random integer in [0, maxExclusive), using
 * rejection sampling to avoid modulo bias.
 */
function secureRandomInt(maxExclusive: number): number {
  const limit = Math.floor(0x1_0000_0000 / maxExclusive) * maxExclusive
  const buffer = new Uint32Array(1)
  for (;;) {
    crypto.getRandomValues(buffer)
    if (buffer[0] < limit) {
      return buffer[0] % maxExclusive
    }
  }
}

/**
 * Fisher-Yates shuffle. Returns a new array.
 */
function shuffle<T>(items: readonly T[]): T[] {
  const shuffled = [...items]
  for (let i = shuffled.length - 1; i > 0; i -= 1) {
    const j = secureRandomInt(i + 1)
    const temp = shuffled[i]
    shuffled[i] = shuffled[j]
    shuffled[j] = temp
  }
  return shuffled
}

function encodeRow(row: readonly string[]): Uint8Array<ArrayBuffer> {
  return encodeXUserDefined(
    Papa.unparse([row as string[]], { escapeFormulae: false })
  )
}

function isEmptyRow(row: readonly string[]): boolean {
  return row.length === 0 || (row.length === 1 && row[0] === '')
}

/**
 * Like {@link redactCsvColumnsAtIndices}, but also shuffles data rows within
 * groups, where a group is the set of rows sharing the same values in the
 * group-by columns. Groups appear in the order in which they're first seen in
 * the file. Rows within a group needn't be contiguous in the input.
 *
 * Unlike {@link redactCsvColumnsAtIndices}, this holds all data rows in memory
 * (as encoded bytes) until the whole file has been read. Blank data rows are
 * dropped, though a trailing line break is preserved.
 */
function redactAndShuffleCsvRowsWithinGroups(
  { bom, fileWithoutBom }: FileContents,
  columnIndicesToRedact: readonly number[],
  groupByColumnIndices: readonly number[],
  numRowsToSkip: number
): Promise<File> {
  const columnIndicesToRedactSet = new Set(columnIndicesToRedact)
  return new Promise((resolve, reject) => {
    const headerAndAboveRows: Uint8Array<ArrayBuffer>[] = []
    // Maps preserve insertion order, so groups stay in first-seen order
    const groups = new Map<string, Uint8Array<ArrayBuffer>[]>()
    let linebreak = '\n'
    let lastRowWasEmpty = false
    let rowsProcessed = 0
    let failed = false
    Papa.parse<string[]>(fileWithoutBom, {
      ...DEFAULT_PARSE_OPTIONS,
      chunk: ({ data, errors, meta }, parser) => {
        try {
          throwOnRealChunkErrors(data, errors)
          if (data.length === 0) {
            return
          }
          ;({ linebreak } = meta)
          data.forEach((row, rowIndex) => {
            const isHeaderOrAbove = rowsProcessed + rowIndex < numRowsToSkip + 1
            if (isHeaderOrAbove) {
              headerAndAboveRows.push(encodeRow(row))
              lastRowWasEmpty = false
              return
            }
            if (isEmptyRow(row)) {
              lastRowWasEmpty = true
              return
            }
            lastRowWasEmpty = false
            const groupKey = JSON.stringify(
              groupByColumnIndices.map(columnIndex => row[columnIndex] ?? '')
            )
            let group = groups.get(groupKey)
            if (!group) {
              group = []
              groups.set(groupKey, group)
            }
            group.push(encodeRow(redactRow(row, columnIndicesToRedactSet)))
          })
          rowsProcessed += data.length
        } catch (error) {
          // Call reject before parser.abort because parser.abort triggers the
          // complete callback
          failed = true
          reject(error)
          parser.abort()
        }
      },
      complete: () => {
        if (failed) {
          return
        }
        try {
          const encodedLinebreak = encodeXUserDefined(linebreak)
          const parts: BlobPart[] = bom ? [bom.bytes] : []
          let isFirstRow = true
          const appendRow = (row: Uint8Array<ArrayBuffer>) => {
            if (!isFirstRow) {
              parts.push(encodedLinebreak)
            }
            parts.push(row)
            isFirstRow = false
          }
          headerAndAboveRows.forEach(appendRow)
          for (const group of groups.values()) {
            shuffle(group).forEach(appendRow)
          }
          if (lastRowWasEmpty) {
            parts.push(encodedLinebreak)
          }
          resolve(
            new File(parts, fileWithoutBom.name, {
              lastModified: fileWithoutBom.lastModified,
              type: fileWithoutBom.type,
            })
          )
        } catch (error) {
          reject(error)
        }
      },
      error: reject,
    })
  })
}

interface RedactCsvColumnsOptions {
  numRowsToSkip?: number
  /**
   * If provided, data rows are also shuffled within groups of rows sharing the
   * same values in these columns. All of these columns must be present in the
   * header row, or the original file is returned.
   */
  shuffleRowsWithinGroupsBy?: readonly string[]
}

/**
 * Replaces every non-empty value in the specified columns with "REDACTED".
 * Columns that aren't in the header row are skipped. Optionally shuffles data
 * rows within groups (see {@link RedactCsvColumnsOptions}). Returns the
 * original file if none of the columns to redact are found, if any group-by
 * column isn't found, or if anything goes wrong.
 */
export async function redactCsvColumns(
  file: File,
  columnNames: readonly string[],
  { numRowsToSkip = 0, shuffleRowsWithinGroupsBy }: RedactCsvColumnsOptions = {}
): Promise<File> {
  try {
    const fileContents = await parseBom(file)
    if (
      fileContents.bom?.type === 'UTF16LE' ||
      fileContents.bom?.type === 'UTF16BE'
    ) {
      throw new Error('UTF-16-encoded files not yet handled')
    }

    const columnIndices = await findCsvColumnIndices(
      fileContents,
      columnNames,
      numRowsToSkip
    )
    if (columnIndices.length === 0) {
      return file
    }

    if (shuffleRowsWithinGroupsBy) {
      const groupByColumnIndices = await findCsvColumnIndices(
        fileContents,
        shuffleRowsWithinGroupsBy,
        numRowsToSkip
      )
      if (groupByColumnIndices.length !== shuffleRowsWithinGroupsBy.length) {
        throw new Error('Not all group-by columns found in header row')
      }
      return await redactAndShuffleCsvRowsWithinGroups(
        fileContents,
        columnIndices,
        groupByColumnIndices,
        numRowsToSkip
      )
    }

    return await redactCsvColumnsAtIndices(
      fileContents,
      columnIndices,
      numRowsToSkip
    )
  } catch (error) {
    // oxlint-disable-next-line no-console
    console.error(error instanceof Error ? error.message : String(error))

    // Return the file unchanged on error. We don't want a failure during
    // client-side redacting to interrupt server-side parsing.
    return file
  }
}
