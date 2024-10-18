import autoTable from 'jspdf-autotable'
import jsPDF from 'jspdf'
import { Colors } from '@blueprintjs/core'
import { getBallots, IBallot } from './useBallots'
import { IAuditBoard } from '../useAuditBoards'
import { IBatch } from './useBatchResults'
import { IRound } from '../AuditAdmin/useRoundsAuditAdmin'
import { blankLine } from '../../utils/string'

// Page constants in points
// Note that these aren't used consistently yet, since they were added later
const pageHeight = 792 // 11 inches * 72 pts per inch
const pageWidth = 612 // 8.5 inches
const pageMargin = 72 // 1 inch
const pageContentWidth = pageWidth - pageMargin * 2

// Text constants in points
// Note that these aren't used consistently yet, since they were added later
const defaultFontSize = 12
const headingFontSize = 18
const subHeadingFontSize = 16
const sectionBottomMargin = 24
const pBottomMargin = 10
const drawingLineWidth = 1

/**
 * renderTextWrapped renders the provided text, wrapping at the specified wrap width, appending the
 * specified bottom margin, and returning the updated y position
 *
 * Consistent units should be used for all numerical values
 */
function renderTextWrapped({
  doc,
  text,
  wrapWidth,
  x,
  y,
  bottomMargin,
}: {
  doc: jsPDF
  text: string
  wrapWidth: number
  x: number
  y: number
  bottomMargin: number
}): number {
  const textSplit = doc.splitTextToSize(text, wrapWidth)
  doc.text(textSplit, x, y)
  return y + doc.getLineHeight() * textSplit.length + bottomMargin
}

/**
 * addPageBreakIfNecessary adds a page break if the next addition to the document requires it and
 * returns the updated y position
 *
 * Consistent units should be used for all numerical values
 */
function addPageBreakIfNecessary({
  doc,
  y,
  yMax,
  heightOfNextAddition,
  pageMargin, // eslint-disable-line no-shadow
}: {
  doc: jsPDF
  y: number
  yMax: number
  heightOfNextAddition: number
  pageMargin: number
}): number {
  if (y + heightOfNextAddition > yMax) {
    doc.addPage()
    return pageMargin
  }
  return y
}

// Label constants in points
const LABEL_HEIGHT = 72
const LABEL_WIDTH = 190
const LABEL_START_Y = 36
const LABEL_START_X = 13
const LABEL_MARGIN_X = 9
const LABEL_PADDING_Y = 7
const LABEL_PADDING_X = 7

const generateLabelPages = (labels: jsPDF, ballots: IBallot[]): string[][][] =>
  ballots.reduce(
    (a, ballot, ballotIndex) => {
      const lines: string[] = [
        `${ballot.auditBoard!.name} - Ballot Number: ${ballot.position}`,
        ballot.batch.container && `Container: ${ballot.batch.container}`,
        ballot.batch.tabulator && `Tabulator: ${ballot.batch.tabulator}`,
        `Batch: ${ballot.batch.name}`,
        ballot.imprintedId !== undefined
          ? `Imprinted ID: ${ballot.imprintedId}`
          : null,
      ].filter(line => line) as string[] // ts is not seeing us filtering out the nulls
      const finalLines: string[] = []
      lines.forEach(line => {
        if (lines.length < 8) {
          finalLines.push(
            ...labels.splitTextToSize(line, LABEL_WIDTH - LABEL_PADDING_X * 2)
          )
        } else {
          finalLines.push(
            ...labels.splitTextToSize(
              line,
              LABEL_WIDTH - LABEL_PADDING_X * 2
            )[0]
          )
        }
      })
      // add an empty array for next page
      if (Math.floor(ballotIndex / 30) + 1 > a.length) {
        // eslint-disable-next-line no-param-reassign
        a[Math.floor(ballotIndex / 30)] = []
      }
      a[Math.floor(ballotIndex / 30)].push(finalLines)
      return a
    },
    [[]] as string[][][]
  )

export const downloadLabels = async (
  electionId: string,
  jurisdictionId: string,
  round: IRound,
  jurisdictionName: string,
  auditName: string
): Promise<string> => {
  const ballots = await getBallots(electionId, jurisdictionId, round.id)
  if (ballots && ballots.length) {
    const labels = new jsPDF({ format: 'letter', unit: 'pt' })
    labels.setFontSize(9)
    let labelPages = generateLabelPages(labels, ballots)
    if (labelPages.some(page => page.some(label => label.length > 6))) {
      labels.setFontSize(7)
      labelPages = generateLabelPages(labels, ballots)
    }
    labelPages.forEach((page, i) => {
      if (i > 0) labels.addPage('letter')
      page.forEach((label, j) => {
        const labelCount = j + 1
        const column = (labelCount - 1) % 3
        const row = Math.floor((labelCount - 1) / 3)
        const leftX = LABEL_START_X + column * (LABEL_WIDTH + LABEL_MARGIN_X)
        const topY = LABEL_START_Y + row * LABEL_HEIGHT

        // Useful for drawing the actual label boundary when testing
        // labels.roundedRect(leftX, topY, LABEL_WIDTH, LABEL_HEIGHT, 7, 7, 'S')

        labels.text(label, leftX + LABEL_PADDING_X, topY + LABEL_PADDING_Y, {
          baseline: 'top',
        })
      })
    })
    await labels.save(
      `Round ${round.roundNum} Labels - ${jurisdictionName} - ${auditName}.pdf`,
      { returnPromise: true }
    )
    return labels.output() // returned for test snapshots
  }
  return ''
}

// Placeholder constants in millimeters
const PLACEHOLDERS_WIDTH = 180
const PLACEHOLDERS_START_X = 20
const PLACEHOLDERS_START_Y = 20

export const downloadPlaceholders = async (
  electionId: string,
  jurisdictionId: string,
  round: IRound,
  jurisdictionName: string,
  auditName: string
): Promise<string> => {
  const ballots = await getBallots(electionId, jurisdictionId, round.id)
  if (ballots && ballots.length) {
    const placeholders = new jsPDF({ format: 'letter' })
    placeholders.setFontSize(20)
    let pageCount = 0
    ballots.forEach(ballot => {
      if (pageCount > 0) placeholders.addPage('letter')

      const lines = [
        ballot.auditBoard!.name,
        ballot.batch.container && `Container: ${ballot.batch.container}`,
        ballot.batch.tabulator && `Tabulator: ${ballot.batch.tabulator}`,
        `Batch: ${ballot.batch.name}`,
        `Ballot Number: ${ballot.position}`,
        ballot.imprintedId !== undefined
          ? `Imprinted ID: ${ballot.imprintedId}`
          : null,
      ]
        .filter(line => line)
        .map(line => placeholders.splitTextToSize(line!, PLACEHOLDERS_WIDTH))
        .flat()

      placeholders.text(lines, PLACEHOLDERS_START_X, PLACEHOLDERS_START_Y, {
        baseline: 'top',
        lineHeightFactor: 2,
      })
      pageCount += 1
    })
    await placeholders.save(
      `Round ${round.roundNum} Placeholders - ${jurisdictionName} - ${auditName}.pdf`,
      { returnPromise: true }
    )
    return placeholders.output() // returned for test snapshots
  }
  return ''
}

export const downloadAuditBoardCredentials = async (
  auditBoards: IAuditBoard[],
  jurisdictionName: string,
  auditName: string
): Promise<string> => {
  const doc = new jsPDF({ format: 'letter', unit: 'pt' })

  const auditBoardsWithBallots = auditBoards.filter(
    board => board.currentRoundStatus.numSampledBallots > 0
  )
  const auditBoardsWithoutBallots = auditBoards.filter(
    board => board.currentRoundStatus.numSampledBallots === 0
  )
  auditBoardsWithBallots.forEach((board, i) => {
    const qr: HTMLCanvasElement | null = document.querySelector(
      `#qr-${board.passphrase} > canvas`
    )
    /* istanbul ignore next */
    if (!qr) return
    if (i > 0) doc.addPage('letter')

    let y = pageMargin
    const x = pageMargin
    const wrapWidth = pageContentWidth
    doc.setFont('Helvetica', 'normal').setFontSize(defaultFontSize)

    doc.setFillColor('#F8EDE2') // Light yellow from Blueprint
    const calloutPadding = 15
    doc.roundedRect(
      x - calloutPadding,
      y,
      pageContentWidth + calloutPadding * 2,
      doc.getLineHeight() * 3 + calloutPadding * 2,
      3,
      3,
      'F'
    )
    doc.setFont('Helvetica', 'bold').setFontSize(defaultFontSize)
    y = renderTextWrapped({
      doc,
      text: 'Keep Secure!',
      wrapWidth: pageContentWidth - calloutPadding,
      x,
      y: y + calloutPadding + doc.getLineHeight() * (2 / 3),
      bottomMargin: doc.getLineHeight() / 4,
    })
    doc.setFont('Helvetica', 'normal').setFontSize(defaultFontSize)
    y = renderTextWrapped({
      doc,
      text: 'Share these login credentials with audit board members only.',
      wrapWidth: pageContentWidth - calloutPadding,
      x,
      y,
      bottomMargin: 0,
    })
    y = renderTextWrapped({
      doc,
      text: 'Do not post publicly.',
      wrapWidth: pageContentWidth - calloutPadding,
      x,
      y,
      bottomMargin: 0,
    })
    y += calloutPadding + sectionBottomMargin

    doc.setFont('Helvetica', 'bold').setFontSize(headingFontSize)
    y = renderTextWrapped({
      doc,
      text: board.name,
      wrapWidth,
      x,
      y,
      bottomMargin: pBottomMargin,
    })
    doc.setFont('Helvetica', 'normal').setFontSize(defaultFontSize)
    y = renderTextWrapped({
      doc,
      text: 'Scan this QR code to log in to Arlo:',
      wrapWidth,
      x,
      y,
      bottomMargin: pBottomMargin,
    })

    const qrCodeImage = qr.toDataURL()
    const qrCodeWidth = 200
    const qrCodeHeight = 200
    doc.addImage(qrCodeImage, 'JPEG', x, y, qrCodeWidth, qrCodeHeight)
    y += qrCodeHeight + sectionBottomMargin * 2

    y = renderTextWrapped({
      doc,
      text: 'Alternatively, you can use this link:',
      wrapWidth,
      x,
      y,
      bottomMargin: pBottomMargin,
    })

    doc.setFont('Helvetica', 'bold').setFontSize(defaultFontSize)
    const loginUrl = `${window.location.origin}/auditboard/${board.passphrase}`
    const yBeforeUrl = y
    y = renderTextWrapped({
      doc,
      text: loginUrl,
      wrapWidth,
      x,
      y,
      bottomMargin: 0,
    })
    doc.link(x, yBeforeUrl, pageContentWidth, y - yBeforeUrl, {
      url: loginUrl,
    })
  })
  if (auditBoardsWithoutBallots.length > 0) {
    doc.addPage('letter')
    let y = pageMargin
    doc.setFont('Helvetica', 'bold').setFontSize(defaultFontSize)
    auditBoardsWithoutBallots.forEach(board => {
      y = renderTextWrapped({
        doc,
        text: `${board.name}: No ballots`,
        wrapWidth: pageContentWidth,
        x: pageMargin,
        y,
        bottomMargin: 0,
      })
    })
  }
  await doc.save(
    `Audit Board Credentials - ${jurisdictionName} - ${auditName}.pdf`,
    { returnPromise: true }
  )
  return doc.output() // returned for test snapshots
}

export interface IMinimalContest {
  choices: { name: string }[]
  name: string
}

export const downloadBatchTallySheets = async (
  batches: IBatch[],
  contests: IMinimalContest[],
  jurisdictionName: string,
  auditName: string
): Promise<string> => {
  const doc = new jsPDF({ format: 'letter', unit: 'pt' })

  const checkboxSize = 10
  const checkboxLeftMargin = 10
  const checkboxRightMargin = 6
  const checkboxTopMargin = 1 // To properly align checkboxes with text

  const tableCellMinWidth = 100
  const tableCellPadding = 6

  const signatureLineLabelFontSize = 10
  const signatureLineRightMargin = 10
  const signatureLineLabelTopMargin = 6

  let y = pageMargin
  const yMax = pageHeight - pageMargin
  for (let i = 0; i < batches.length; i += 1) {
    const batch = batches[i]

    doc.setFont('Helvetica', 'normal').setFontSize(headingFontSize)
    doc.setLineWidth(drawingLineWidth).setDrawColor('black')

    doc.text('Audit Board Batch Tally Sheet', pageMargin, y)
    y += doc.getLineHeight() + pBottomMargin

    doc.setFont('Helvetica', 'bold').setFontSize(subHeadingFontSize)

    y = renderTextWrapped({
      doc,
      text: `Batch Name: ${batch.name}`,
      wrapWidth: pageContentWidth,
      x: pageMargin,
      y,
      bottomMargin: sectionBottomMargin,
    })

    doc.setFont('Helvetica', 'normal').setFontSize(defaultFontSize)

    y = renderTextWrapped({
      doc,
      text: `Jurisdiction: ${jurisdictionName}`,
      wrapWidth: pageContentWidth,
      x: pageMargin,
      y,
      bottomMargin: pBottomMargin,
    })

    doc.text(`Audit Board (Optional): ${blankLine(20)}`, pageMargin, y)
    y += doc.getLineHeight() + pBottomMargin

    doc.text(`Batch Type (Optional): ${blankLine(20)}`, pageMargin, y)
    y += doc.getLineHeight() + sectionBottomMargin

    const sealedPrompt =
      'Was the container sealed when received by the audit board?'
    const sealedPromptDimensions = doc.getTextDimensions(sealedPrompt)
    doc.text(sealedPrompt, pageMargin, y)
    const sealedCheckboxX =
      pageMargin + sealedPromptDimensions.w + checkboxLeftMargin
    const sealedCheckboxY = y - checkboxSize + checkboxTopMargin
    doc.rect(sealedCheckboxX, sealedCheckboxY, checkboxSize, checkboxSize)
    doc.text('Yes', sealedCheckboxX + checkboxSize + checkboxRightMargin, y)
    y += sectionBottomMargin

    //
    // Assume up until this point that we won't spill onto a second page. From here onward, no
    // longer make that assumption.
    //

    // Add 3 blank lines to contest entries table to allow for additional entries (i.e. overvotes)
    const blankLines: string[][] = new Array(3).fill(['', ''])

    for (const [contestIndex, contest] of contests.entries()) {
      // manually add page break if table will only print header rows before the
      // page ends as it will then re-print headers on the subsequent page
      y = addPageBreakIfNecessary({
        doc,
        y,
        yMax,
        heightOfNextAddition:
          // vertical height of three cells to ensure two header cells + at least one content cell will fit before page break
          3 * (doc.getLineHeight() + 2 * tableCellPadding) +
          4 * drawingLineWidth,
        pageMargin,
      })

      // autoTable automatically adds page breaks
      autoTable(doc, {
        head: [
          [{ content: contest.name, colSpan: 2 }],
          ['Candidates/Choices', 'Enter Stack Totals'],
        ],
        body: contest.choices
          .map(choice => [
            choice.name,
            '', // Stack totals left blank for the audit board to fill out
          ])
          .concat(blankLines),
        startY: y,
        margin: {
          bottom: pageMargin,
          left: pageMargin,
          right: pageMargin,
          top: pageMargin,
        },
        rowPageBreak: 'avoid',
        theme: 'grid',
        styles: {
          cellPadding: tableCellPadding,
          fillColor: 'white',
          fontSize: defaultFontSize,
          fontStyle: 'normal',
          lineColor: 'black',
          lineWidth: drawingLineWidth,
          minCellWidth: tableCellMinWidth,
          textColor: 'black',
        },
        headStyles: {
          fontStyle: 'bold',
        },
        didParseCell(data) {
          // The best way to apply a style to the first (and only first) header row
          if (data.cell.section === 'head' && data.row.index === 0) {
            // eslint-disable-next-line no-param-reassign
            data.cell.styles.fillColor = Colors.LIGHT_GRAY1
          }
        },
        willDrawCell(data) {
          // Indicate if a table is continuing from a previous page
          if (
            data.cell.section === 'head' &&
            data.row.index === 0 &&
            data.pageNumber > 1
          ) {
            // eslint-disable-next-line no-param-reassign
            data.cell.text[0] += ' (continued)'
          }
        },
      })

      // https://github.com/simonbengtsson/jsPDF-AutoTable/issues/728
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      y = (doc as any).lastAutoTable.finalY
      y += sectionBottomMargin
      if (contestIndex === contests.length - 1) {
        y += doc.getLineHeight()
      }
    }

    // Reset drawing settings, since autoTable seems to adjust them internally
    doc.setLineWidth(drawingLineWidth).setDrawColor('black')

    y = addPageBreakIfNecessary({
      doc,
      y,
      yMax,
      heightOfNextAddition: doc.getLineHeight() + pBottomMargin,
      pageMargin,
    })

    doc.text(
      'When work is completed, return all ballots to the ballot container and seal the container.',
      pageMargin,
      y
    )
    y += doc.getLineHeight() + pBottomMargin

    y = addPageBreakIfNecessary({
      doc,
      y,
      yMax,
      heightOfNextAddition: doc.getLineHeight() + sectionBottomMargin,
      pageMargin,
    })

    const resealedPrompt = 'Was the container resealed by the audit board?'
    const resealedPromptDimensions = doc.getTextDimensions(resealedPrompt)
    doc.text(resealedPrompt, pageMargin, y)
    const resealedCheckboxX =
      pageMargin + resealedPromptDimensions.w + checkboxLeftMargin
    const resealedCheckboxY = y - checkboxSize + checkboxTopMargin
    doc.rect(resealedCheckboxX, resealedCheckboxY, checkboxSize, checkboxSize)
    doc.text('Yes', resealedCheckboxX + checkboxSize + checkboxRightMargin, y)
    y += doc.getLineHeight() + sectionBottomMargin

    y = addPageBreakIfNecessary({
      doc,
      y,
      yMax,
      heightOfNextAddition:
        doc.getLineHeight() +
        signatureLineLabelTopMargin +
        doc.getLineHeight() +
        sectionBottomMargin,
      pageMargin,
    })

    const signatureLine = `x${blankLine(30)}`
    const signatureLineDimensions = doc.getTextDimensions(signatureLine)
    doc.text(signatureLine, pageMargin, y)
    doc.text(
      signatureLine,
      pageMargin + signatureLineDimensions.w + signatureLineRightMargin,
      y
    )
    y += doc.getLineHeight() + signatureLineLabelTopMargin

    doc.setFont('Helvetica', 'normal').setFontSize(signatureLineLabelFontSize)

    const signatureLineLabel = '(Audit Board Member)'
    const signatureLineLabelDimensions = doc.getTextDimensions(
      signatureLineLabel
    )
    const signatureLine1LabelX =
      // Center the signature line label below the signature line
      pageMargin +
      signatureLineDimensions.w / 2 -
      signatureLineLabelDimensions.w / 2
    doc.text(signatureLineLabel, signatureLine1LabelX, y)
    const signatureLine2LabelX =
      signatureLine1LabelX +
      signatureLineRightMargin +
      signatureLineDimensions.w
    doc.text(signatureLineLabel, signatureLine2LabelX, y)
    y += doc.getLineHeight() + sectionBottomMargin

    doc.setFont('Helvetica', 'normal').setFontSize(defaultFontSize)

    y = addPageBreakIfNecessary({
      doc,
      y,
      yMax,
      heightOfNextAddition: doc.getLineHeight() + sectionBottomMargin,
      pageMargin,
    })

    doc.line(pageMargin, y, pageWidth - pageMargin, y)
    y += doc.getLineHeight() + sectionBottomMargin

    //
    // Check-in/out station steps
    //

    // Add a page break if the entire section doesn't fit on the current page so that it isn't
    // split across pages
    const checkInOutStationStepsSectionHeight =
      (doc.getLineHeight() + pBottomMargin) * 4
    y = addPageBreakIfNecessary({
      doc,
      y,
      yMax,
      heightOfNextAddition: checkInOutStationStepsSectionHeight,
      pageMargin,
    })

    doc.setFont('Helvetica', 'bold').setFontSize(defaultFontSize)

    doc.text('Check-In/Out Station Steps:', pageMargin, y)
    y += doc.getLineHeight() + pBottomMargin

    doc.setFont('Helvetica', 'normal').setFontSize(defaultFontSize)

    doc.rect(
      pageMargin,
      y - checkboxSize + checkboxTopMargin,
      checkboxSize,
      checkboxSize
    )
    doc.text(
      'Recorded batch check-in',
      pageMargin + checkboxSize + checkboxRightMargin,
      y
    )
    y += doc.getLineHeight() + pBottomMargin

    doc.rect(
      pageMargin,
      y - checkboxSize + checkboxTopMargin,
      checkboxSize,
      checkboxSize
    )
    doc.text(
      'Entered tallies into Arlo',
      pageMargin + checkboxSize + checkboxRightMargin,
      y
    )
    y += doc.getLineHeight() + pBottomMargin

    doc.text(
      `${blankLine(5)} Initials of check-in/out station member`,
      pageMargin,
      y
    )

    // Create page for next batch if present
    if (i < batches.length - 1) {
      doc.addPage()
      y = pageMargin
    }
  }

  await doc.save(
    `Batch Tally Sheets - ${jurisdictionName} - ${auditName}.pdf`,
    { returnPromise: true }
  )
  return doc.output() // Returned for snapshot tests
}

export const downloadTallyEntryLoginLinkPrintout = async (
  loginLinkUrl: string,
  jurisdictionName: string,
  auditName: string
): Promise<string> => {
  const doc = new jsPDF({ format: 'letter', unit: 'pt' })

  let y = pageMargin
  const x = pageMargin
  const wrapWidth = pageContentWidth
  doc.setFont('Helvetica', 'normal').setFontSize(defaultFontSize)

  doc.setFillColor('#F8EDE2') // Light yellow from Blueprint
  const calloutPadding = 15
  doc.roundedRect(
    x - calloutPadding,
    y,
    pageContentWidth + calloutPadding * 2,
    doc.getLineHeight() * 3 + calloutPadding * 2,
    3,
    3,
    'F'
  )
  doc.setFont('Helvetica', 'bold').setFontSize(defaultFontSize)
  y = renderTextWrapped({
    doc,
    text: 'Keep Secure!',
    wrapWidth: pageContentWidth - calloutPadding,
    x,
    y: y + calloutPadding + doc.getLineHeight() * (2 / 3),
    bottomMargin: doc.getLineHeight() / 4,
  })
  doc.setFont('Helvetica', 'normal').setFontSize(defaultFontSize)
  y = renderTextWrapped({
    doc,
    text: 'Share this login link with tally entry account users only.',
    wrapWidth: pageContentWidth - calloutPadding,
    x,
    y,
    bottomMargin: 0,
  })
  y = renderTextWrapped({
    doc,
    text: 'Do not post publicly.',
    wrapWidth: pageContentWidth - calloutPadding,
    x,
    y,
    bottomMargin: 0,
  })
  y += calloutPadding + sectionBottomMargin

  doc.setFont('Helvetica', 'normal').setFontSize(10)
  doc.setTextColor(Colors.GRAY1)
  y = renderTextWrapped({
    doc,
    text: `${jurisdictionName} - ${auditName}`,
    wrapWidth,
    x,
    y,
    bottomMargin: pBottomMargin,
  })

  doc.setTextColor(Colors.BLACK)
  doc.setFont('Helvetica', 'bold').setFontSize(headingFontSize)
  y = renderTextWrapped({
    doc,
    text: 'Tally Entry Login Link',
    wrapWidth,
    x,
    y,
    bottomMargin: pBottomMargin,
  })

  doc.setFont('Helvetica', 'normal').setFontSize(defaultFontSize)
  y = renderTextWrapped({
    doc,
    text: 'Use this link to log into Arlo:',
    wrapWidth,
    x,
    y,
    bottomMargin: pBottomMargin,
  })

  doc.setFont('Helvetica', 'bold').setFontSize(defaultFontSize)
  const yBeforeUrl = y
  y = renderTextWrapped({
    doc,
    text: loginLinkUrl,
    wrapWidth,
    x,
    y,
    bottomMargin: 0,
  })
  doc.link(x, yBeforeUrl, pageContentWidth, y - yBeforeUrl, {
    url: loginLinkUrl,
  })
  await doc.save(
    `Tally Entry Login Link - ${jurisdictionName} - ${auditName}.pdf`,
    { returnPromise: true }
  )
  return doc.output() // returned for test snapshots
}
